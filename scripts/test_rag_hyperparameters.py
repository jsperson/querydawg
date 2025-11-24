#!/usr/bin/env python3
"""
RAG Hyperparameter Testing Script

Tests different combinations of:
1. top_k values (5, 7, 10, 15, 20)
2. Chunk type weights (baseline, aggressive boost, table-focused, balanced)

On target databases: pets_1, car_1, dog_kennels
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from app.services.text_to_sql.enhanced import EnhancedSQLGenerator
from app.services.embedding_service import EmbeddingService
from app.database.metadata_store import get_metadata_store
from app.database.query_executor import QueryExecutorFactory
from app.config import get_settings


# Test databases (simple, medium, complex)
TEST_DATABASES = {
    'pets_1': {
        'turso_url': None,  # Will be populated from Turso
        'questions': 42,
        'tables': 3,
        'complexity': 'simple'
    },
    'car_1': {
        'turso_url': None,
        'questions': 92,
        'tables': 6,
        'complexity': 'medium'
    },
    'dog_kennels': {
        'turso_url': None,
        'questions': 81,
        'tables': 8,
        'complexity': 'complex'
    }
}

# Top-k values to test
TOP_K_VALUES = [5, 7, 10, 15, 20]

# Limit questions for faster testing (None = all questions)
QUESTION_LIMIT = 10  # Test with first 10 questions per database for speed

# Chunk weight configurations to test
WEIGHT_CONFIGS = {
    'baseline': {
        'table': 1.2,
        'cross_table_patterns': 1.1,
        'overview': 0.7,
        'ambiguities': 0.6
    },
    'aggressive_boost': {
        'table': 1.5,
        'cross_table_patterns': 1.3,
        'overview': 0.5,
        'ambiguities': 0.4
    },
    'table_focused': {
        'table': 1.8,
        'cross_table_patterns': 0.9,
        'overview': 0.5,
        'ambiguities': 0.3
    },
    'balanced': {
        'table': 1.0,
        'cross_table_patterns': 1.0,
        'overview': 0.9,
        'ambiguities': 0.8
    },
    'cross_table_boost': {
        'table': 1.2,
        'cross_table_patterns': 1.5,
        'overview': 0.7,
        'ambiguities': 0.5
    }
}


class RAGHyperparameterTester:
    """Test different RAG hyperparameter configurations."""

    def __init__(self):
        self.settings = get_settings()
        self.metadata_store = get_metadata_store(
            self.settings.supabase_url,
            self.settings.supabase_service_role_key
        )

        # Create query executor for Turso
        self.query_executor = QueryExecutorFactory.create(
            source="turso",
            connection_string=None  # Turso factory handles URLs internally
        )

        self.results = []

    def load_turso_urls(self):
        """Build Turso database URLs using same logic as TursoClient."""
        print("Building Turso database URLs...")

        # Get Turso configuration from environment
        org = os.getenv("TURSO_ORG", "querydawg")
        base_url = os.getenv("TURSO_BASE_URL", f"{org}.turso.io")

        for db_name in TEST_DATABASES.keys():
            # Normalize database name: Turso uses lowercase and dashes
            normalized_name = db_name.replace("_", "-").lower()

            # Build URL using same logic as TursoClient
            turso_url = f"https://{normalized_name}-{base_url}"

            TEST_DATABASES[db_name]['turso_url'] = turso_url
            print(f"  ✓ {db_name}: {turso_url}")

    def get_benchmark_questions(self, db_name: str) -> List[Dict[str, Any]]:
        """Get benchmark questions and expected SQL for a database from Spider dev.json."""
        print(f"Loading benchmark questions for {db_name}...")

        # Load from Spider dev.json
        spider_path = project_root / "data" / "spider" / "dev.json"

        if not spider_path.exists():
            raise FileNotFoundError(f"Spider dev.json not found at {spider_path}")

        with open(spider_path, 'r') as f:
            spider_data = json.load(f)

        # Filter by database
        questions = []
        for i, item in enumerate(spider_data):
            if item.get('db_id') == db_name:
                questions.append({
                    'question_id': f"dev_{i:04d}",
                    'question': item['question'],
                    'expected_sql': item['query'],
                    'db_id': db_name
                })

                # Apply question limit if set
                if QUESTION_LIMIT and len(questions) >= QUESTION_LIMIT:
                    break

        print(f"  Loaded {len(questions)} questions" + (f" (limited to {QUESTION_LIMIT})" if QUESTION_LIMIT else ""))
        return questions

    def test_configuration(
        self,
        db_name: str,
        top_k: int,
        weight_config_name: str,
        weight_config: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Test a specific RAG configuration.

        Returns:
            Results dictionary with accuracy and timing info
        """
        print(f"\n{'='*80}")
        print(f"Testing: {db_name} | top_k={top_k} | weights={weight_config_name}")
        print(f"{'='*80}")

        # Temporarily modify chunk weights in EmbeddingService
        original_weights = EmbeddingService.CHUNK_TYPE_WEIGHTS.copy()
        EmbeddingService.CHUNK_TYPE_WEIGHTS = weight_config

        try:
            # Get database URL
            db_url = TEST_DATABASES[db_name]['turso_url']

            # Create generator with specified top_k
            generator = EnhancedSQLGenerator(
                database_url=db_url,
                database_name=db_name,
                connection_name="Supabase",
                use_vector_search=True,
                top_k_chunks=top_k,
                db_type='sqlite'
            )

            # Get benchmark questions
            questions = self.get_benchmark_questions(db_name)

            # Test each question
            correct = 0
            total = len(questions)
            errors = []

            start_time = time.time()

            for i, q in enumerate(questions, 1):
                question = q['question']
                expected_sql = q['expected_sql']

                try:
                    # Generate SQL
                    result = generator.generate_sql(question)
                    generated_sql = result['sql']

                    # Check execution match (more robust than text comparison)
                    is_correct, error_msg = self._check_execution_match(
                        generated_sql,
                        expected_sql,
                        db_name
                    )

                    if is_correct:
                        correct += 1
                        status = "✓"
                    else:
                        status = "✗"
                        errors.append({
                            'question_id': q['question_id'],
                            'question': question,
                            'expected': expected_sql,
                            'generated': generated_sql,
                            'error': error_msg
                        })

                    # Print progress every 10 questions
                    if i % 10 == 0:
                        accuracy = (correct / i) * 100
                        print(f"  Progress: {i}/{total} | Accuracy: {accuracy:.2f}% | {status}")

                except Exception as e:
                    print(f"  Error on question {i}: {e}")
                    errors.append({
                        'question_id': q['question_id'],
                        'question': question,
                        'error': str(e)
                    })

            elapsed_time = time.time() - start_time
            accuracy = (correct / total) * 100 if total > 0 else 0

            print(f"\n  RESULTS: {correct}/{total} correct ({accuracy:.2f}%)")
            print(f"  Time: {elapsed_time:.1f}s ({elapsed_time/total:.2f}s per question)")

            return {
                'database': db_name,
                'top_k': top_k,
                'weight_config': weight_config_name,
                'weights': weight_config,
                'total_questions': total,
                'correct': correct,
                'accuracy': accuracy,
                'elapsed_time': elapsed_time,
                'avg_time_per_question': elapsed_time / total if total > 0 else 0,
                'errors': errors,
                'timestamp': datetime.utcnow().isoformat()
            }

        finally:
            # Restore original weights
            EmbeddingService.CHUNK_TYPE_WEIGHTS = original_weights

    def _check_execution_match(
        self,
        generated_sql: str,
        expected_sql: str,
        database: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if generated SQL produces same results as expected SQL.

        Args:
            generated_sql: Generated SQL query
            expected_sql: Expected SQL query (SQLite format)
            database: Database name

        Returns:
            (match, error_message)
        """
        try:
            # Execute expected SQL
            expected_results, _, expected_error = self.query_executor.execute_query(expected_sql, database)
            if expected_error:
                return False, f"Expected SQL failed: {expected_error}"

            # Execute generated SQL
            generated_results, _, generated_error = self.query_executor.execute_query(generated_sql, database)
            if generated_error:
                return False, f"Generated SQL failed: {generated_error}"

            # Compare results (convert to sets for order-independent comparison)
            try:
                expected_set = {frozenset(row) for row in expected_results}
                generated_set = {frozenset(row) for row in generated_results}
                match = expected_set == generated_set
                return match, None if match else "Results don't match"
            except TypeError:
                # Fallback for unhashable types
                match = expected_results == generated_results
                return match, None if match else "Results don't match"

        except Exception as e:
            return False, f"Execution error: {str(e)}"

    def run_phase1_top_k_tests(self):
        """Phase 1: Test different top_k values with baseline weights."""
        print("\n" + "="*80)
        print("PHASE 1: TOP-K OPTIMIZATION (baseline weights)")
        print("="*80)

        baseline_weights = WEIGHT_CONFIGS['baseline']

        for db_name in TEST_DATABASES.keys():
            for top_k in TOP_K_VALUES:
                result = self.test_configuration(
                    db_name=db_name,
                    top_k=top_k,
                    weight_config_name='baseline',
                    weight_config=baseline_weights
                )
                self.results.append(result)

                # Save intermediate results
                self.save_results()

    def run_phase2_weight_tests(self, best_top_k: int):
        """Phase 2: Test different weight configurations with best top_k."""
        print("\n" + "="*80)
        print(f"PHASE 2: WEIGHT OPTIMIZATION (top_k={best_top_k})")
        print("="*80)

        for db_name in TEST_DATABASES.keys():
            for weight_name, weight_config in WEIGHT_CONFIGS.items():
                if weight_name == 'baseline':
                    continue  # Already tested in Phase 1

                result = self.test_configuration(
                    db_name=db_name,
                    top_k=best_top_k,
                    weight_config_name=weight_name,
                    weight_config=weight_config
                )
                self.results.append(result)

                # Save intermediate results
                self.save_results()

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and find optimal configuration."""
        print("\n" + "="*80)
        print("ANALYSIS: Finding Optimal Configuration")
        print("="*80)

        # Group by database
        by_database = {}
        for result in self.results:
            db = result['database']
            if db not in by_database:
                by_database[db] = []
            by_database[db].append(result)

        # Find best top_k (Phase 1 results only)
        print("\n--- Top-K Analysis (baseline weights) ---")
        top_k_scores = {}
        for top_k in TOP_K_VALUES:
            total_correct = 0
            total_questions = 0
            for result in self.results:
                if result['weight_config'] == 'baseline' and result['top_k'] == top_k:
                    total_correct += result['correct']
                    total_questions += result['total_questions']

            accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            top_k_scores[top_k] = {
                'correct': total_correct,
                'total': total_questions,
                'accuracy': accuracy
            }
            print(f"  top_k={top_k}: {total_correct}/{total_questions} ({accuracy:.2f}%)")

        best_top_k = max(top_k_scores.items(), key=lambda x: x[1]['accuracy'])[0]
        print(f"\n  → Best top_k: {best_top_k} ({top_k_scores[best_top_k]['accuracy']:.2f}%)")

        # Find best weight configuration
        print("\n--- Weight Configuration Analysis ---")
        weight_scores = {}
        for weight_name in WEIGHT_CONFIGS.keys():
            total_correct = 0
            total_questions = 0
            for result in self.results:
                if result['weight_config'] == weight_name and result['top_k'] == best_top_k:
                    total_correct += result['correct']
                    total_questions += result['total_questions']

            if total_questions > 0:
                accuracy = (total_correct / total_questions * 100)
                weight_scores[weight_name] = {
                    'correct': total_correct,
                    'total': total_questions,
                    'accuracy': accuracy
                }
                print(f"  {weight_name}: {total_correct}/{total_questions} ({accuracy:.2f}%)")

        if weight_scores:
            best_weight_config = max(weight_scores.items(), key=lambda x: x[1]['accuracy'])[0]
            print(f"\n  → Best weights: {best_weight_config} ({weight_scores[best_weight_config]['accuracy']:.2f}%)")
        else:
            best_weight_config = 'baseline'

        # Per-database breakdown
        print("\n--- Per-Database Results ---")
        for db_name in TEST_DATABASES.keys():
            print(f"\n{db_name} ({TEST_DATABASES[db_name]['complexity']}):")
            db_results = by_database.get(db_name, [])

            # Find best config for this database
            best_result = max(db_results, key=lambda x: x['accuracy'])
            print(f"  Best: top_k={best_result['top_k']}, weights={best_result['weight_config']}")
            print(f"  Accuracy: {best_result['correct']}/{best_result['total_questions']} ({best_result['accuracy']:.2f}%)")

        return {
            'best_top_k': best_top_k,
            'best_weight_config': best_weight_config,
            'top_k_scores': top_k_scores,
            'weight_scores': weight_scores,
            'by_database': by_database
        }

    def save_results(self):
        """Save results to JSON file."""
        output_dir = project_root / 'logs'
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f'rag_hyperparameter_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        with open(output_file, 'w') as f:
            json.dump({
                'test_databases': TEST_DATABASES,
                'top_k_values': TOP_K_VALUES,
                'weight_configs': WEIGHT_CONFIGS,
                'results': self.results,
                'timestamp': datetime.utcnow().isoformat()
            }, f, indent=2)

        print(f"\n  💾 Results saved to: {output_file}")


def main():
    """Main test execution."""
    print("="*80)
    print("RAG HYPERPARAMETER OPTIMIZATION TEST")
    print("="*80)
    print(f"Test databases: {', '.join(TEST_DATABASES.keys())}")
    print(f"Question limit: {QUESTION_LIMIT} per database" if QUESTION_LIMIT else "Using all questions")
    print(f"Top-k values: {TOP_K_VALUES}")
    print(f"Weight configs: {', '.join(WEIGHT_CONFIGS.keys())}")
    print("="*80)

    tester = RAGHyperparameterTester()

    # Load database URLs
    tester.load_turso_urls()

    # Phase 1: Test top_k values
    tester.run_phase1_top_k_tests()

    # Analyze Phase 1 results to find best top_k
    analysis = tester.analyze_results()
    best_top_k = analysis['best_top_k']

    # Phase 2: Test weight configurations with best top_k
    tester.run_phase2_weight_tests(best_top_k)

    # Final analysis
    final_analysis = tester.analyze_results()

    # Save final results
    tester.save_results()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"Optimal Configuration:")
    print(f"  top_k: {final_analysis['best_top_k']}")
    print(f"  weights: {final_analysis['best_weight_config']}")
    print("="*80)


if __name__ == "__main__":
    main()
