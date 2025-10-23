"""
Prompt templates for different LLM tasks
"""
from typing import Dict, Any, List


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
2. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
3. Include proper WHERE clauses for filtering
4. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
5. Add ORDER BY and LIMIT clauses when relevant
6. Use table aliases for clarity in multi-table queries
7. Ensure column references are unambiguous
8. Return ONLY the SQL query without explanations or markdown formatting"""

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

        return f"""DATABASE SCHEMA:
{formatted_schema}

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
        return """You are an expert PostgreSQL debugger. Your task is to identify and fix SQL syntax errors and logical issues. Return ONLY the corrected SQL query without explanations."""

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

        return f"""DATABASE SCHEMA:
{formatted_schema}

FAILED SQL QUERY:
{sql}

ERROR MESSAGE:
{error_message}

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

The semantic layer provides important business context:
- Table descriptions explain what each table represents
- Column descriptions clarify the meaning of each field
- Relationships document how tables connect
- Business rules describe important constraints and logic

Guidelines:
1. Generate ONLY valid PostgreSQL syntax
2. Use the semantic layer to understand business context and terminology
3. Choose appropriate tables and columns based on semantic meanings
4. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
5. Include proper WHERE clauses for filtering
6. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
7. Add ORDER BY and LIMIT clauses when relevant
8. Use table aliases for clarity in multi-table queries
9. Ensure column references are unambiguous
10. Return ONLY the SQL query without explanations or markdown formatting"""

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
            semantic_section += f"Description: {semantic_layer.get('description', 'N/A')}\n\n"

            # Add table documentation
            tables = semantic_layer.get('tables', [])
            if tables:
                semantic_section += "Tables:\n"
                for table in tables:
                    semantic_section += f"\n  {table.get('name', 'N/A')}:\n"
                    semantic_section += f"    Description: {table.get('description', 'N/A')}\n"

                    # Add column documentation
                    columns = table.get('columns', [])
                    if columns:
                        semantic_section += "    Columns:\n"
                        for col in columns:
                            semantic_section += f"      - {col.get('name', 'N/A')}: {col.get('description', 'N/A')}\n"

                    # Add relationships if present
                    relationships = table.get('relationships', [])
                    if relationships:
                        semantic_section += "    Relationships:\n"
                        for rel in relationships:
                            semantic_section += f"      - {rel.get('description', 'N/A')}\n"

        return f"""DATABASE SCHEMA:
{formatted_schema}{semantic_section}

QUESTION: {question}

Generate a PostgreSQL query to answer this question. Use the semantic layer documentation to understand the business context and choose the right tables and columns. Return only the SQL query."""
