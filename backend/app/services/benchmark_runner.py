"""
Core benchmark runner for Spider 1.0 evaluation
"""
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import os
from pathlib import Path

import psycopg2
from psycopg2 import pool
from psycopg2 import sql
import sqlglot
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.benchmark import (
    BenchmarkConfig,
    BenchmarkRunCreate,
    BenchmarkResult,
    SpiderQuestion
)
from ..database.benchmark_store import BenchmarkStore
from ..services.text_to_sql import BaselineSQLGenerator, EnhancedSQLGenerator


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded"""
    pass


class BenchmarkRunner:
    """
    Executes Spider benchmark runs with:
    - Connection pooling for safe SQL execution
    - Retry logic with exponential backoff
    - Cost tracking with budget limits
    - Incremental result storage
    """

    def __init__(
        self,
        benchmark_store: BenchmarkStore,
        spider_data_path: Optional[str] = None,
        budget_limit_usd: float = 5.0,
        connection_string: Optional[str] = None
    ):
        """
        Initialize benchmark runner

        Args:
            benchmark_store: Store for persisting results
            spider_data_path: Path to Spider dev.json (defaults to data/spider/dev.json relative to project root)
            budget_limit_usd: Maximum cost per run
            connection_string: PostgreSQL connection string for query execution
        """
        self.store = benchmark_store

        # Resolve spider_data_path relative to project root if not provided
        if spider_data_path is None:
            # backend/app/services/benchmark_runner.py -> project root is 3 levels up
            project_root = Path(__file__).parent.parent.parent.parent
            spider_data_path = str(project_root / "data" / "spider" / "dev.json")

        self.spider_data_path = spider_data_path
        self.budget_limit = budget_limit_usd
        self.total_cost = 0.0

        # Build connection string from env if not provided
        if connection_string is None:
            connection_string = os.getenv("DATABASE_URL")
            if not connection_string:
                raise ValueError("DATABASE_URL environment variable not set")

        # Store connection string for generators
        self.connection_string = connection_string

        # Create connection pool (2-10 connections)
        self.db_pool = pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=connection_string
        )

        # Cache for SQL generators (one per database)
        self._baseline_generators = {}
        self._enhanced_generators = {}

    def __del__(self):
        """Clean up connection pool"""
        if hasattr(self, 'db_pool') and self.db_pool:
            self.db_pool.closeall()

    def load_spider_questions(
        self,
        databases: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[SpiderQuestion]:
        """
        Load questions from Spider dev.json

        Args:
            databases: Filter to specific databases (None = all)
            limit: Limit number of questions (None = all)

        Returns:
            List of SpiderQuestion objects

        Raises:
            FileNotFoundError: If Spider dataset is not available
        """
        if not Path(self.spider_data_path).exists():
            raise FileNotFoundError(
                f"Spider dataset not found at: {self.spider_data_path}\n"
                f"Please download the dataset by running: python scripts/download_spider.py\n"
                f"Or manually download from: https://drive.google.com/file/d/1m68AHHPC4pqyjT-Zmt-u8TRqdw5vp-U5/view\n"
                f"And extract dev.json to: {Path(self.spider_data_path).parent}"
            )

        with open(self.spider_data_path, 'r') as f:
            data = json.load(f)

        questions = []
        for i, item in enumerate(data):
            # Spider format: {db_id, question, query, query_toks, query_toks_no_value, question_toks, sql}
            db_id = item.get('db_id')
            question_text = item.get('question')
            gold_sql = item.get('query')

            # Skip if filtering by database
            if databases and db_id not in databases:
                continue

            questions.append(SpiderQuestion(
                question_id=f"dev_{i:04d}",
                database=db_id,
                question=question_text,
                query=gold_sql,
                difficulty=None  # Spider 1.0 doesn't have difficulty labels
            ))

            # Stop if limit reached
            if limit and len(questions) >= limit:
                break

        return questions

    def sqlite_to_postgres_sql(self, sql: str) -> str:
        """
        Convert SQLite-style SQL to PostgreSQL-compatible SQL

        Main conversions:
        1. Double quotes for strings → single quotes
        2. GROUP BY column expansion for joined tables

        Args:
            sql: SQLite-style SQL string

        Returns:
            PostgreSQL-compatible SQL string
        """
        import re

        # Step 1: Convert double-quoted string literals to single quotes
        # Pattern: operator/keyword followed by optional whitespace and double-quoted string
        patterns = [
            (r'(=\s*)"([^"]+)"', r"\1'\2'"),           # = "value"
            (r'(!=\s*)"([^"]+)"', r"\1'\2'"),          # != "value"
            (r'(<>\s*)"([^"]+)"', r"\1'\2'"),          # <> "value"
            (r'(>\s*)"([^"]+)"', r"\1'\2'"),           # > "value"
            (r'(<\s*)"([^"]+)"', r"\1'\2'"),           # < "value"
            (r'(>=\s*)"([^"]+)"', r"\1'\2'"),          # >= "value"
            (r'(<=\s*)"([^"]+)"', r"\1'\2'"),          # <= "value"
            (r'(\bIN\s*\()"([^"]+)"', r"\1'\2'"),      # IN ("value"
            (r'(,\s*)"([^"]+)"', r"\1'\2'"),           # , "value" (in IN clause)
            (r'(\bLIKE\s+)"([^"]+)"', r"\1'\2'"),      # LIKE "value"
            (r'(\bNOT\s+LIKE\s+)"([^"]+)"', r"\1'\2'"),# NOT LIKE "value"
        ]

        result = sql
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Step 2: Fix GROUP BY with joined tables
        # PostgreSQL requires all selected non-aggregate columns to be in GROUP BY
        # This is a heuristic fix for common Spider patterns

        # Pattern: SELECT columns with aliases FROM table1 JOIN table2 ... GROUP BY single_column
        # Look for GROUP BY that doesn't include all table aliases used in SELECT
        # Match until we hit HAVING, ORDER, LIMIT, or end of string
        group_by_match = re.search(r'\bGROUP\s+BY\s+(.*?)(?:\s+HAVING|\s+ORDER|\s+LIMIT|$)', result, re.IGNORECASE)
        if group_by_match:
            group_by_clause = group_by_match.group(1).strip()

            # Check if GROUP BY has table aliases (e.g., T1.column)
            has_alias = re.search(r'([A-Za-z]\d+)\.', group_by_clause)

            if has_alias:
                # Extract SELECT clause (before FROM)
                select_match = re.search(r'SELECT\s+(.*?)\s+FROM', result, re.IGNORECASE | re.DOTALL)
                if select_match:
                    select_clause = select_match.group(1)

                    # Find non-aggregate columns with different table aliases
                    # Look for patterns like T2.name where T2 is different from T1 in GROUP BY
                    select_columns = []
                    for col_match in re.finditer(r'([A-Za-z]\d+)\.([A-Za-z_][A-Za-z0-9_]*)', select_clause):
                        table_alias = col_match.group(1)
                        column_name = col_match.group(2)
                        full_column = f"{table_alias}.{column_name}"

                        # Skip if it's an aggregate function argument
                        # Check backwards for COUNT, SUM, AVG, etc.
                        start_pos = col_match.start()
                        preceding_text = select_clause[max(0, start_pos-20):start_pos]
                        if not re.search(r'(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT)\s*\(', preceding_text, re.IGNORECASE):
                            select_columns.append(full_column)

                    # Add missing columns to GROUP BY
                    for col in select_columns:
                        if col not in group_by_clause:
                            group_by_clause += f", {col}"

                    # Replace GROUP BY clause
                    result = re.sub(
                        r'\bGROUP\s+BY\s+(.*?)(?=\s+HAVING|\s+ORDER|\s+LIMIT|$)',
                        f"GROUP BY {group_by_clause}",
                        result,
                        flags=re.IGNORECASE
                    )

        return result

    def normalize_sql(self, sql: str) -> str:
        """
        Normalize SQL for comparison using sqlglot

        Args:
            sql: Raw SQL string

        Returns:
            Normalized SQL string
        """
        try:
            parsed = sqlglot.parse_one(sql, dialect="postgres")
            return parsed.sql(dialect="postgres", normalize=True).strip()
        except Exception:
            # Fallback to simple normalization
            return sql.lower().strip().replace('\n', ' ').replace('\t', ' ')

    def check_exact_match(self, generated_sql: str, gold_sql: str) -> bool:
        """
        Check if generated SQL matches gold SQL (normalized comparison)

        Args:
            generated_sql: Generated SQL
            gold_sql: Ground truth SQL (SQLite syntax)

        Returns:
            True if normalized SQL strings match
        """
        # Convert gold SQL from SQLite to PostgreSQL syntax
        gold_sql_converted = self.sqlite_to_postgres_sql(gold_sql)

        norm_generated = self.normalize_sql(generated_sql)
        norm_gold = self.normalize_sql(gold_sql_converted)
        return norm_generated == norm_gold

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type(psycopg2.OperationalError)
    )
    def execute_sql_safely(
        self,
        query: str,
        database: str
    ) -> Tuple[List[Tuple], Optional[str]]:
        """
        Execute SQL in read-only transaction with timeout

        Args:
            query: SQL query to execute
            database: Database/schema name

        Returns:
            (results, error_message)
            results: List of tuples, sorted for comparison
            error_message: None if success, error string if failure
        """
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Set read-only and timeout
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("SET statement_timeout = '5s'")

                # Safely set search_path using sql.Identifier to prevent SQL injection
                search_path_query = sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(database)
                )
                cur.execute(search_path_query)

                # Execute query
                cur.execute(query)
                results = cur.fetchall()

                # Sort results for deterministic comparison
                sorted_results = sorted(results, key=lambda x: str(x))
                return sorted_results, None

        except Exception as e:
            return [], str(e)

        finally:
            # Always rollback (read-only) and return connection
            conn.rollback()
            self.db_pool.putconn(conn)

    def check_execution_match(
        self,
        generated_sql: str,
        gold_sql: str,
        database: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if generated SQL produces same results as gold SQL

        Args:
            generated_sql: Generated SQL
            gold_sql: Ground truth SQL (SQLite syntax)
            database: Database/schema name

        Returns:
            (match, error_message)
            match: True if results match
            error_message: Error from generated SQL execution (None if success)
        """
        # Convert gold SQL from SQLite to PostgreSQL syntax
        gold_sql_converted = self.sqlite_to_postgres_sql(gold_sql)

        # Execute gold SQL
        gold_results, gold_error = self.execute_sql_safely(gold_sql_converted, database)
        if gold_error:
            # Gold SQL should always work; if it doesn't, something is wrong
            return False, f"Gold SQL failed: {gold_error}"

        # Execute generated SQL
        gen_results, gen_error = self.execute_sql_safely(generated_sql, database)
        if gen_error:
            return False, gen_error

        # Compare results
        return gold_results == gen_results, None

    def _get_baseline_generator(self, database: str) -> BaselineSQLGenerator:
        """Get or create baseline generator for database"""
        if database not in self._baseline_generators:
            self._baseline_generators[database] = BaselineSQLGenerator(
                database_url=self.connection_string,
                database_name=database
            )
        return self._baseline_generators[database]

    def _get_enhanced_generator(self, database: str) -> EnhancedSQLGenerator:
        """Get or create enhanced generator for database"""
        if database not in self._enhanced_generators:
            self._enhanced_generators[database] = EnhancedSQLGenerator(
                database_url=self.connection_string,
                database_name=database
            )
        return self._enhanced_generators[database]

    def record_cost(self, cost: float, run_id: str, approach: str):
        """
        Record cost and check budget limit

        Args:
            cost: Cost in USD
            run_id: Benchmark run ID
            approach: "baseline" or "enhanced"

        Raises:
            BudgetExceededError: If budget limit exceeded
        """
        self.total_cost += cost

        if self.total_cost > self.budget_limit:
            raise BudgetExceededError(
                f"Budget limit ${self.budget_limit:.2f} exceeded (total: ${self.total_cost:.2f})"
            )

        # Update run cost in database
        self.store.update_run_cost(run_id, cost, approach)

    def process_question_baseline(
        self,
        question: SpiderQuestion,
        run_id: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Process single question with baseline approach

        Returns dict with baseline_* fields for BenchmarkResult
        """
        start_time = time.time()

        try:
            # Get generator for this database
            generator = self._get_baseline_generator(question.database)

            # Generate SQL
            response = generator.generate_sql(question.question)

            # Extract metadata
            metadata = response["metadata"]
            generated_sql = response["sql"]

            # Record cost
            cost = float(metadata["cost_usd"])
            self.record_cost(cost, run_id, "baseline")

            # Check exact match
            exact_match = self.check_exact_match(generated_sql, question.query)

            # Check execution match
            exec_match, exec_error = self.check_execution_match(
                generated_sql,
                question.query,
                question.database
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            return {
                "baseline_sql": generated_sql,
                "baseline_exact_match": exact_match,
                "baseline_exec_match": exec_match,
                "baseline_error": exec_error,
                "baseline_execution_time_ms": execution_time_ms,
                "baseline_cost_usd": Decimal(str(cost)),
                "baseline_tokens_used": metadata["tokens_used"],
                "baseline_retry_count": retry_count
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "baseline_sql": None,
                "baseline_exact_match": False,
                "baseline_exec_match": False,
                "baseline_error": str(e),
                "baseline_execution_time_ms": execution_time_ms,
                "baseline_cost_usd": Decimal("0"),
                "baseline_tokens_used": 0,
                "baseline_retry_count": retry_count
            }

    def process_question_enhanced(
        self,
        question: SpiderQuestion,
        run_id: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Process single question with enhanced approach (semantic layer)

        Returns dict with enhanced_* fields for BenchmarkResult
        """
        start_time = time.time()

        try:
            # Get generator for this database
            generator = self._get_enhanced_generator(question.database)

            # Generate SQL with semantic layer
            response = generator.generate_sql(question.question)

            # Extract metadata
            metadata = response["metadata"]
            generated_sql = response["sql"]

            # Record cost
            cost = float(metadata["cost_usd"])
            self.record_cost(cost, run_id, "enhanced")

            # Check exact match
            exact_match = self.check_exact_match(generated_sql, question.query)

            # Check execution match
            exec_match, exec_error = self.check_execution_match(
                generated_sql,
                question.query,
                question.database
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Get number of semantic chunks used
            semantic_chunks = metadata.get('semantic_chunks_used', 0)

            return {
                "enhanced_sql": generated_sql,
                "enhanced_exact_match": exact_match,
                "enhanced_exec_match": exec_match,
                "enhanced_error": exec_error,
                "enhanced_execution_time_ms": execution_time_ms,
                "enhanced_cost_usd": Decimal(str(cost)),
                "enhanced_tokens_used": metadata["tokens_used"],
                "enhanced_semantic_chunks_used": semantic_chunks,
                "enhanced_retry_count": retry_count
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "enhanced_sql": None,
                "enhanced_exact_match": False,
                "enhanced_exec_match": False,
                "enhanced_error": str(e),
                "enhanced_execution_time_ms": execution_time_ms,
                "enhanced_cost_usd": Decimal("0"),
                "enhanced_tokens_used": 0,
                "enhanced_semantic_chunks_used": 0,
                "enhanced_retry_count": retry_count
            }

    def run_benchmark(self, config: BenchmarkConfig) -> str:
        """
        Execute full benchmark run

        Args:
            config: Benchmark configuration

        Returns:
            run_id: UUID of created benchmark run

        Raises:
            BudgetExceededError: If budget exceeded
        """
        # Load questions
        questions = self.load_spider_questions(
            databases=config.databases,
            limit=config.question_limit
        )

        # Create run record
        run_create = BenchmarkRunCreate(
            name=config.name,
            run_type=config.run_type,
            question_count=len(questions),
            databases=config.databases,
            created_by="system",
            notes=f"Budget limit: ${self.budget_limit:.2f}"
        )
        run_id = self.store.create_run(run_create)

        # Mark as running
        self.store.update_run_status(run_id, "running")

        # Reset cost counter
        self.total_cost = 0.0

        completed = 0
        failed = 0

        try:
            for i, question in enumerate(questions):
                # Check if run was cancelled (only every 10 questions to reduce DB load)
                if i % 10 == 0:
                    status = self.store.get_run_status(run_id)
                    if status and status.status == "cancelled":
                        print(f"Benchmark {run_id} was cancelled by user")
                        self.store.update_run_progress(run_id, completed, failed, current_question=None)
                        return run_id

                # Update progress
                self.store.update_run_progress(
                    run_id,
                    completed=completed,
                    failed=failed,
                    current_question=question.question
                )

                # Build result object
                result_data = {
                    "run_id": run_id,
                    "question_id": question.question_id,
                    "database": question.database,
                    "question": question.question,
                    "gold_sql": question.query,
                    "difficulty": question.difficulty,
                    "processed_at": datetime.utcnow().isoformat()
                }

                # Process based on run type
                try:
                    if config.run_type in ["baseline", "both"]:
                        baseline_data = self.process_question_baseline(question, run_id)
                        result_data.update(baseline_data)

                    if config.run_type in ["enhanced", "both"]:
                        enhanced_data = self.process_question_enhanced(question, run_id)
                        result_data.update(enhanced_data)

                    # Save result
                    result = BenchmarkResult(**result_data)
                    self.store.save_result(result)

                    completed += 1

                except Exception as e:
                    # Question failed
                    failed += 1
                    print(f"Failed question {question.question_id}: {str(e)}")

            # Calculate final metrics
            self.store.calculate_and_save_metrics(run_id)

            # Mark as completed
            self.store.update_run_status(run_id, "completed", status_reason="completed")
            self.store.update_run_progress(run_id, completed, failed, current_question=None)

            return run_id

        except BudgetExceededError as e:
            # Budget exceeded
            self.store.update_run_status(run_id, "failed", status_reason="budget_exceeded", error=str(e))
            self.store.update_run_progress(run_id, completed, failed, current_question=None)
            raise

        except Exception as e:
            # Other fatal error
            self.store.update_run_status(run_id, "failed", status_reason="fatal_error", error=str(e))
            self.store.update_run_progress(run_id, completed, failed, current_question=None)
            raise
