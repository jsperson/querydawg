"""
Prompt templates for different LLM tasks
"""
from typing import Dict, Any, List, Optional


def format_schema_for_prompt(schema: Dict[str, Any]) -> str:
    """
    Format schema dictionary into a clear, concise text representation

    Args:
        schema: Schema dictionary from SchemaExtractor

    Returns:
        Formatted string representation of the schema
    """
    lines = []
    lines.append(f"Database: {schema['database']}\n")

    for table in schema['tables']:
        lines.append(f"Table: {table['name']}")
        lines.append(f"  Row Count: {table['row_count']:,}")

        # Columns
        lines.append("  Columns:")
        for col in table['columns']:
            pk_marker = " (PRIMARY KEY)" if col['primary_key'] else ""
            null_marker = " NULL" if col['nullable'] else " NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            lines.append(f"    - {col['name']}: {col['type']}{pk_marker}{null_marker}{default}")

        # Foreign keys
        if table['foreign_keys']:
            lines.append("  Foreign Keys:")
            for fk in table['foreign_keys']:
                lines.append(
                    f"    - {fk['column']} -> "
                    f"{fk['referenced_table']}.{fk['referenced_column']}"
                )

        lines.append("")  # Empty line between tables

    return "\n".join(lines)


class PromptTemplates:
    """Collection of prompt templates for different tasks"""

    @staticmethod
    def baseline_sql_system() -> str:
        """System prompt for baseline SQL generation"""
        return """You are an expert PostgreSQL database assistant. Your task is to generate accurate, efficient SQL queries based on the provided database schema and natural language questions.

Guidelines:
1. Generate ONLY valid PostgreSQL syntax
2. ALWAYS qualify table names with the schema name (e.g., schema_name.table_name)
3. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
4. Include proper WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY and LIMIT clauses when relevant
7. Use table aliases for clarity in multi-table queries
8. Ensure column references are unambiguous
9. **When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"), INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause.** Only exclude aggregations when the question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year, not the count).
10. Return ONLY the SQL query without explanations or markdown formatting

Examples:
- Question: "What city has the most customers?"
  - WRONG: SELECT city, COUNT(*) FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
  - CORRECT: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
- Question: "How many orders were placed each month?"
  - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
  - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month"""

    @staticmethod
    def baseline_sql_user(question: str, schema: Dict[str, Any]) -> str:
        """
        User prompt for baseline SQL generation

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)

        database_name = schema.get('database', 'unknown')
        return f"""DATABASE SCHEMA:
{formatted_schema}

IMPORTANT: All table references in your SQL query MUST be qualified with the schema name.
For example, use "{database_name}.table_name" NOT just "table_name".

QUESTION: {question}

Generate a PostgreSQL query to answer this question. Return only the SQL query."""

    @staticmethod
    def sql_explanation_system() -> str:
        """System prompt for SQL explanation"""
        return """You are a helpful assistant that explains SQL queries in clear, simple language. Break down complex queries into easy-to-understand steps.

Formatting guidelines:
- Use single quotes (') for code references like table names, column names, and SQL functions
- Do not put punctuation (commas, periods) inside quotes
- Keep explanations clear and concise"""

    @staticmethod
    def sql_explanation_user(sql: str, question: str) -> str:
        """
        User prompt for SQL explanation

        Args:
            sql: The SQL query to explain
            question: The original question

        Returns:
            Formatted user prompt
        """
        return f"""Original Question: {question}

SQL Query:
{sql}

Please explain what this SQL query does in 2-3 clear, concise sentences. Focus on the main operations and the data being retrieved."""

    @staticmethod
    def error_correction_system() -> str:
        """System prompt for SQL error correction"""
        return """You are an expert PostgreSQL debugger. Your task is to identify and fix SQL syntax errors and logical issues.

IMPORTANT: All table names must be qualified with their schema name (e.g., schema_name.table_name).

Return ONLY the corrected SQL query without explanations."""

    @staticmethod
    def error_correction_user(
        sql: str,
        error_message: str,
        schema: Dict[str, Any]
    ) -> str:
        """
        User prompt for SQL error correction

        Args:
            sql: The erroneous SQL query
            error_message: Error message from database
            schema: Database schema

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)

        database_name = schema.get('database', 'unknown')
        return f"""DATABASE SCHEMA:
{formatted_schema}

FAILED SQL QUERY:
{sql}

ERROR MESSAGE:
{error_message}

IMPORTANT: All table references in your SQL query MUST be qualified with the schema name.
For example, use "{database_name}.table_name" NOT just "table_name".

Fix the SQL query to resolve this error. Return only the corrected SQL query."""

    @staticmethod
    def schema_summary_system() -> str:
        """System prompt for schema summarization"""
        return """You are a database documentation assistant. Summarize database schemas in clear, concise language that helps users understand the data structure."""

    @staticmethod
    def schema_summary_user(schema: Dict[str, Any]) -> str:
        """
        User prompt for schema summarization

        Args:
            schema: Database schema

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)

        return f"""{formatted_schema}

Provide a brief summary of this database schema, including:
1. What domain/topic it covers
2. Main entities (tables) and their relationships
3. Key insights about the data structure"""

    @staticmethod
    def enhanced_sql_system() -> str:
        """System prompt for enhanced SQL generation with semantic layer"""
        return """You are an expert PostgreSQL database assistant. Your task is to generate accurate, efficient SQL queries based on the provided database schema, semantic documentation, and natural language questions.

SEMANTIC LAYER CONTEXT:
The semantic layer provides important business context to help you generate more accurate queries:
- Table purposes explain what each table represents in business terms
- Column business meanings clarify what each field contains
- Relationships show how tables connect with JOIN patterns
- Business terms map user vocabulary to technical table/column names
- Synonyms help match natural language to database columns

Use this semantic information to:
- Choose the correct tables when multiple options exist
- Select appropriate columns based on business meaning
- Understand relationships and required JOINs
- Map business terminology in questions to technical names

Guidelines:
1. Generate ONLY valid PostgreSQL syntax
2. ALWAYS qualify table names with the schema name (e.g., schema_name.table_name)
3. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
4. Include proper WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY and LIMIT clauses when relevant
7. Use table aliases for clarity in multi-table queries
8. Ensure column references are unambiguous
9. **When the question explicitly asks for quantities ("how many", "what is the total", "what is the average"), INCLUDE the aggregation (COUNT, SUM, AVG) in the SELECT clause.** Only exclude aggregations when the question asks for superlatives or identifiers (e.g., "which year had the most concerts?" wants the year, not the count).
10. Return ONLY the SQL query without explanations or markdown formatting

Examples:
- Question: "What city has the most customers?"
  - WRONG: SELECT city, COUNT(*) FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
  - CORRECT: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1
- Question: "How many orders were placed each month?"
  - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
  - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month"""

    @staticmethod
    def enhanced_sql_user(question: str, schema: Dict[str, Any], semantic_layer: Optional[Dict[str, Any]]) -> str:
        """
        User prompt for enhanced SQL generation

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor
            semantic_layer: Semantic layer documentation (may be None)

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)

        # Build semantic layer section if available
        semantic_section = ""
        if semantic_layer:
            semantic_section = "\n\nSEMANTIC LAYER DOCUMENTATION:\n"
            semantic_section += f"Database: {semantic_layer.get('database', 'N/A')}\n"

            # Add overview if present
            overview = semantic_layer.get('overview', {})
            if overview:
                semantic_section += f"Domain: {overview.get('domain', 'N/A')}\n"
                semantic_section += f"Purpose: {overview.get('purpose', 'N/A')}\n"
                key_entities = overview.get('key_entities', [])
                if key_entities:
                    semantic_section += f"Key Entities: {', '.join(key_entities)}\n"
            semantic_section += "\n"

            # Add table documentation
            tables = semantic_layer.get('tables', [])
            if tables:
                semantic_section += "Tables:\n"
                for table in tables:
                    semantic_section += f"\n  {table.get('name', 'N/A')}:\n"
                    semantic_section += f"    Business Name: {table.get('business_name', 'N/A')}\n"
                    semantic_section += f"    Purpose: {table.get('purpose', 'N/A')}\n"

                    # Add column documentation
                    columns = table.get('columns', [])
                    if columns:
                        semantic_section += "    Columns:\n"
                        for col in columns:
                            col_name = col.get('name', 'N/A')
                            business_name = col.get('business_name', col_name)
                            business_meaning = col.get('business_meaning', 'N/A')
                            semantic_section += f"      {col_name} → {business_name}: {business_meaning}\n"

                            # Add synonyms if present
                            synonyms = col.get('synonyms', [])
                            if synonyms and len(synonyms) > 0:
                                semantic_section += f"        Synonyms: {', '.join(synonyms)}\n"

                            # Add filters if present
                            filters = col.get('typical_filters', [])
                            if filters and len(filters) > 0:
                                semantic_section += f"        Filters: {', '.join(filters)}\n"

                            # Add aggregations if present
                            aggs = col.get('aggregations', [])
                            if aggs and len(aggs) > 0:
                                semantic_section += f"        Aggregations: {', '.join(aggs)}\n"

                    # Add relationships
                    relationships = table.get('relationships', [])
                    if relationships:
                        semantic_section += "    Relationships:\n"
                        for rel in relationships:
                            col = rel.get('column', 'N/A')
                            ref_table = rel.get('references_table', 'N/A')
                            rel_meaning = rel.get('business_meaning', 'N/A')
                            semantic_section += f"      {col} → {ref_table}: {rel_meaning}\n"

        database_name = schema.get('database', 'unknown')
        return f"""DATABASE SCHEMA:
{formatted_schema}{semantic_section}

IMPORTANT: All table references in your SQL query MUST be qualified with the schema name.
For example, use "{database_name}.table_name" NOT just "table_name".

QUESTION: {question}

Generate a PostgreSQL query to answer this question. Use the semantic layer documentation to understand the business context and choose the right tables and columns. Return only the SQL query."""

    @staticmethod
    def enhanced_sql_user_with_context(
        question: str,
        schema: Dict[str, Any],
        semantic_context: Optional[str]
    ) -> str:
        """
        User prompt for enhanced SQL generation with text-based semantic context.

        This version accepts semantic context as a pre-formatted string
        (e.g., from vector search results) instead of a full semantic layer dict.

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor
            semantic_context: Pre-formatted semantic context string (may be None)

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)

        # Build semantic context section if available
        context_section = ""
        if semantic_context:
            context_section = f"\n\nSEMANTIC CONTEXT:\n{semantic_context}\n"

        database_name = schema.get('database', 'unknown')
        return f"""DATABASE SCHEMA:
{formatted_schema}{context_section}

IMPORTANT: All table references in your SQL query MUST be qualified with the schema name.
For example, use "{database_name}.table_name" NOT just "table_name".

QUESTION: {question}

Generate a PostgreSQL query to answer this question. Use the semantic context to understand the business meaning and choose the right tables and columns. Return only the SQL query."""
