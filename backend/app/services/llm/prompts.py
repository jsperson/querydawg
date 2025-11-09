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
    def _get_db_specific_instructions(db_type: str = 'postgresql') -> Dict[str, str]:
        """
        Get database-specific instructions for SQL generation

        Args:
            db_type: Database type ('postgresql' or 'sqlite')

        Returns:
            Dictionary with db_name, syntax_instruction, and table_qualification
        """
        if db_type.lower() == 'sqlite':
            return {
                'db_name': 'SQLite',
                'syntax_instruction': 'Generate ONLY valid SQLite syntax',
                'table_qualification': 'Reference tables directly by name (e.g., table_name)',
                'qualification_example': 'table_name',
                'qualification_note': 'SQLite does not require schema qualification for table names.'
            }
        else:  # postgresql (default)
            return {
                'db_name': 'PostgreSQL',
                'syntax_instruction': 'Generate ONLY valid PostgreSQL syntax',
                'table_qualification': 'ALWAYS qualify table names with the schema name (e.g., schema_name.table_name)',
                'qualification_example': '{database_name}.table_name',
                'qualification_note': 'All table references in your SQL query MUST be qualified with the schema name.'
            }

    @staticmethod
    def baseline_sql_system(db_type: str = 'postgresql') -> str:
        """
        System prompt for baseline SQL generation

        Args:
            db_type: Database type ('postgresql' or 'sqlite')
        """
        db_info = PromptTemplates._get_db_specific_instructions(db_type)

        return f"""You are an expert {db_info['db_name']} database assistant. Your task is to generate accurate, efficient SQL queries based on the provided database schema and natural language questions.

Guidelines:
1. {db_info['syntax_instruction']}
2. {db_info['table_qualification']}
3. Use appropriate JOIN types (INNER, LEFT, etc.) based on the question
4. Include proper WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY and LIMIT clauses when relevant
7. Use table aliases for clarity in multi-table queries
8. **Ensure column references are unambiguous:**
   - When a column name exists in multiple tables in a JOIN, ALWAYS qualify it
   - Use table.column or alias.column syntax
   - Example: If both `orders` and `customers` have a `status` column, use `orders.status`
   - Check the schema carefully for duplicate column names across tables
10. **AGGREGATION vs SORTING (CRITICAL):**
   - **DO NOT use MIN/MAX/SUM/AVG when questions ask "which/what/who X has the min/max/most/least Y"**
     - These questions want the IDENTIFIER (X), not the aggregated value
     - Use ORDER BY + LIMIT instead
     - Example: "Which product has minimum price?" → ORDER BY price ASC LIMIT 1 (NOT MIN(price))
   - **DO use aggregations when questions explicitly ask for quantities:**
     - "How many..." → COUNT(*)
     - "What is the total..." → SUM(column)
     - "What is the average..." → AVG(column)
     - "What is the maximum..." (asking for the value, not the identifier) → MAX(column)
   - **Key distinction:**
     - "Which product has minimum price?" → wants product name (ORDER BY + LIMIT)
     - "What is the minimum price?" → wants the value (SELECT MIN)
11. Return ONLY the SQL query without explanations or markdown formatting
12. **CASE SENSITIVITY (SQLite CRITICAL):**
    - SQLite is CASE-SENSITIVE for all table and column identifiers
    - You MUST use the EXACT case shown in the schema
    - Example: If schema shows "Customer_ID", use "Customer_ID" NOT "customer_id" or "CustomerID"
    - Always verify your SQL uses exact case from the schema before responding
    - **This does not apply to PostgreSQL** (case-insensitive), but doesn't hurt to be precise

Examples:

AGGREGATION PATTERNS:
1. Question: "What region has the most stores?"
   - WRONG: SELECT region, COUNT(*) FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - CORRECT: SELECT region FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Question asks for "what region" (identifier), not "how many stores" (quantity)

2. Question: "Which product has the minimum price?"
   - WRONG: SELECT product_name, MIN(price) FROM products GROUP BY product_name ORDER BY MIN(price) LIMIT 1
   - CORRECT: SELECT product_name FROM products ORDER BY price ASC LIMIT 1
   - Why: Question asks for "which product" (identifier), not "what is the minimum" (value)

3. Question: "What is the maximum salary?"
   - WRONG: SELECT employee_name FROM employees ORDER BY salary DESC LIMIT 1
   - CORRECT: SELECT MAX(salary) FROM employees
   - Why: Question asks for the value itself, not which employee has it

4. Question: "How many orders were placed each month?"
   - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
   - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
   - Why: "How many" explicitly asks for the count

CASE SENSITIVITY (SQLite):
5. Given schema: Customers(Customer_ID, First_Name, Last_Name)
   - WRONG: SELECT first_name FROM customers WHERE customer_id = 1
   - CORRECT: SELECT First_Name FROM Customers WHERE Customer_ID = 1
   - Why: SQLite is case-sensitive; must match exact schema case

COLUMN DISAMBIGUATION:
6. Given: orders(status, ...) and customers(status, ...)
   Question: "Which customer status has most orders?"
   - WRONG: SELECT status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY status ORDER BY COUNT(*) DESC
   - CORRECT: SELECT customers.status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY customers.status ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Column 'status' exists in both tables; must qualify to avoid ambiguity"""

    @staticmethod
    def baseline_sql_user(question: str, schema: Dict[str, Any], db_type: str = 'postgresql') -> str:
        """
        User prompt for baseline SQL generation

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor
            db_type: Database type ('postgresql' or 'sqlite')

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)
        db_info = PromptTemplates._get_db_specific_instructions(db_type)
        database_name = schema.get('database', 'unknown')

        # Build table qualification instruction
        if db_type.lower() == 'sqlite':
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nReference tables directly (e.g., table_name)."
        else:
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nFor example, use \"{database_name}.table_name\" NOT just \"table_name\"."

        return f"""DATABASE SCHEMA:
{formatted_schema}

{qualification_section}

QUESTION: {question}

Generate a {db_info['db_name']} query to answer this question. Return only the SQL query."""

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
    def enhanced_sql_system(db_type: str = 'postgresql') -> str:
        """
        System prompt for enhanced SQL generation with semantic layer

        Args:
            db_type: Database type ('postgresql' or 'sqlite')
        """
        db_info = PromptTemplates._get_db_specific_instructions(db_type)

        return f"""You are an expert {db_info['db_name']} database assistant. Your task is to generate accurate, efficient SQL queries based on the provided database schema, semantic documentation, and natural language questions.

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
1. {db_info['syntax_instruction']}
2. {db_info['table_qualification']}
3. Include proper WHERE clauses for filtering
4. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
5. Add ORDER BY and LIMIT clauses when relevant
6. Use table aliases for clarity in multi-table queries
7. **Ensure column references are unambiguous:**
   - When a column name exists in multiple tables in a JOIN, ALWAYS qualify it
   - Use table.column or alias.column syntax
   - Example: If both `orders` and `customers` have a `status` column, use `orders.status`
   - Check the schema carefully for duplicate column names across tables
8. **AGGREGATION vs SORTING (CRITICAL):**
   - **DO NOT use MIN/MAX/SUM/AVG when questions ask "which/what/who X has the min/max/most/least Y"**
     - These questions want the IDENTIFIER (X), not the aggregated value
     - Use ORDER BY + LIMIT instead
     - Example: "Which product has minimum price?" → ORDER BY price ASC LIMIT 1 (NOT MIN(price))
   - **DO use aggregations when questions explicitly ask for quantities:**
     - "How many..." → COUNT(*)
     - "What is the total..." → SUM(column)
     - "What is the average..." → AVG(column)
     - "What is the maximum..." (asking for the value, not the identifier) → MAX(column)
   - **Key distinction:**
     - "Which product has minimum price?" → wants product name (ORDER BY + LIMIT)
     - "What is the minimum price?" → wants the value (SELECT MIN)
9. Return ONLY the SQL query without explanations or markdown formatting
10. **CASE SENSITIVITY (SQLite CRITICAL):**
    - SQLite is CASE-SENSITIVE for all table and column identifiers
    - You MUST use the EXACT case shown in the schema
    - Example: If schema shows "Customer_ID", use "Customer_ID" NOT "customer_id" or "CustomerID"
    - Always verify your SQL uses exact case from the schema before responding
    - **This does not apply to PostgreSQL** (case-insensitive), but doesn't hurt to be precise

Examples:

AGGREGATION PATTERNS:
1. Question: "What region has the most stores?"
   - WRONG: SELECT region, COUNT(*) FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - CORRECT: SELECT region FROM stores GROUP BY region ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Question asks for "what region" (identifier), not "how many stores" (quantity)

2. Question: "Which product has the minimum price?"
   - WRONG: SELECT product_name, MIN(price) FROM products GROUP BY product_name ORDER BY MIN(price) LIMIT 1
   - CORRECT: SELECT product_name FROM products ORDER BY price ASC LIMIT 1
   - Why: Question asks for "which product" (identifier), not "what is the minimum" (value)

3. Question: "What is the maximum salary?"
   - WRONG: SELECT employee_name FROM employees ORDER BY salary DESC LIMIT 1
   - CORRECT: SELECT MAX(salary) FROM employees
   - Why: Question asks for the value itself, not which employee has it

4. Question: "How many orders were placed each month?"
   - WRONG: SELECT month FROM orders GROUP BY month ORDER BY month
   - CORRECT: SELECT month, COUNT(*) FROM orders GROUP BY month
   - Why: "How many" explicitly asks for the count

CASE SENSITIVITY (SQLite):
5. Given schema: Customers(Customer_ID, First_Name, Last_Name)
   - WRONG: SELECT first_name FROM customers WHERE customer_id = 1
   - CORRECT: SELECT First_Name FROM Customers WHERE Customer_ID = 1
   - Why: SQLite is case-sensitive; must match exact schema case

COLUMN DISAMBIGUATION:
6. Given: orders(status, ...) and customers(status, ...)
   Question: "Which customer status has most orders?"
   - WRONG: SELECT status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY status ORDER BY COUNT(*) DESC
   - CORRECT: SELECT customers.status FROM orders JOIN customers ON orders.customer_id = customers.id GROUP BY customers.status ORDER BY COUNT(*) DESC LIMIT 1
   - Why: Column 'status' exists in both tables; must qualify to avoid ambiguity"""

    @staticmethod
    def enhanced_sql_user(question: str, schema: Dict[str, Any], semantic_layer: Optional[Dict[str, Any]], db_type: str = 'postgresql') -> str:
        """
        User prompt for enhanced SQL generation

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor
            semantic_layer: Semantic layer documentation (may be None)
            db_type: Database type ('postgresql' or 'sqlite')

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)
        db_info = PromptTemplates._get_db_specific_instructions(db_type)
        database_name = schema.get('database', 'unknown')

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

        # Build table qualification instruction
        if db_type.lower() == 'sqlite':
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nReference tables directly (e.g., table_name)."
        else:
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nFor example, use \"{database_name}.table_name\" NOT just \"table_name\"."

        return f"""DATABASE SCHEMA:
{formatted_schema}{semantic_section}

{qualification_section}

QUESTION: {question}

Generate a {db_info['db_name']} query to answer this question. Use the semantic layer documentation to understand the business context and choose the right tables and columns. Return only the SQL query."""

    @staticmethod
    def enhanced_sql_user_with_context(
        question: str,
        schema: Dict[str, Any],
        semantic_context: Optional[str],
        db_type: str = 'postgresql'
    ) -> str:
        """
        User prompt for enhanced SQL generation with text-based semantic context.

        This version accepts semantic context as a pre-formatted string
        (e.g., from vector search results) instead of a full semantic layer dict.

        Args:
            question: Natural language question
            schema: Database schema from SchemaExtractor
            semantic_context: Pre-formatted semantic context string (may be None)
            db_type: Database type ('postgresql' or 'sqlite')

        Returns:
            Formatted user prompt
        """
        formatted_schema = format_schema_for_prompt(schema)
        db_info = PromptTemplates._get_db_specific_instructions(db_type)
        database_name = schema.get('database', 'unknown')

        # Build semantic context section if available
        context_section = ""
        if semantic_context:
            context_section = f"\n\nSEMANTIC CONTEXT:\n{semantic_context}\n"

        # Build table qualification instruction
        if db_type.lower() == 'sqlite':
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nReference tables directly (e.g., table_name)."
        else:
            qualification_section = f"IMPORTANT: {db_info['qualification_note']}\nFor example, use \"{database_name}.table_name\" NOT just \"table_name\"."

        return f"""DATABASE SCHEMA:
{formatted_schema}{context_section}

{qualification_section}

QUESTION: {question}

Generate a {db_info['db_name']} query to answer this question. Use the semantic context to understand the business meaning and choose the right tables and columns. Return only the SQL query."""
