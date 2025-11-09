"""
Semantic Layer Generator

Generates natural language documentation (semantic layers) for databases
using LLM analysis of schema and sample data.

Uses local SQLite files for schema extraction (preserving case) and
Supabase PostgreSQL for sample data extraction.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .llm.base import LLMProvider
from ..database.turso_schema_extractor import TursoSchemaExtractor
from ..database.supabase_schema_extractor import SupabaseSchemaExtractor


class SemanticLayerGenerator:
    """Generate semantic layers for databases using LLM."""

    def __init__(
        self,
        llm: LLMProvider,
        database_url: str,
        custom_instructions: Optional[str] = None,
        sample_rows: int = 10
    ):
        """
        Initialize the semantic layer generator.

        Args:
            llm: LLM provider instance to use for generation
            database_url: Supabase PostgreSQL connection string (for sample data)
            custom_instructions: Optional custom instructions to add to prompt
            sample_rows: Number of sample rows to extract per table
        """
        self.llm = llm
        self.database_url = database_url
        self.custom_instructions = custom_instructions or ""
        self.sample_rows = sample_rows

        # Use Turso for schema extraction (preserves original case from Spider SQLite)
        self.turso_extractor = TursoSchemaExtractor()

        # Use Supabase for sample data extraction (has actual data)
        self.supabase_extractor = SupabaseSchemaExtractor(database_url, use_spider_metadata=False)

    def generate(
        self,
        database_name: str,
        anonymize: bool = True,
        save_prompt: bool = True
    ) -> Dict[str, Any]:
        """
        Generate semantic layer for a database.

        Args:
            database_name: Name of the database (e.g., 'world_1', 'network_1')
            anonymize: If True, use anonymous database name in prompt
            save_prompt: If True, include the prompt in the output

        Returns:
            Dictionary containing semantic layer and metadata
        """
        # Extract schema from Turso (preserves original case from Spider SQLite)
        print(f"Extracting schema from Turso for {database_name}...")
        schema_info = self.turso_extractor.extract_schema(database_name)

        # Sample data from Supabase (has actual data)
        print(f"Sampling data from Supabase for {database_name}...")
        sample_data = self.supabase_extractor.sample_all_tables(
            database_name,
            limit=self.sample_rows
        )

        # Build prompt
        prompt = self._build_prompt(
            database_name=database_name if not anonymize else "database_unknown",
            schema_info=schema_info,
            sample_data=sample_data
        )

        # Generate semantic layer using LLM
        print(f"Generating semantic layer for {database_name}...")
        print(f"Prompt length: {len(prompt)} characters")

        llm_response = self.llm.generate(
            system_prompt="You are a database documentation expert specializing in creating semantic layers for text-to-SQL systems. Your documentation helps LLMs accurately translate natural language questions into SQL queries.",
            user_prompt=prompt
        )

        # Parse JSON response
        print(f"LLM Response metadata: tokens={llm_response.tokens_used}, cost=${llm_response.cost_usd:.4f}, time={llm_response.generation_time_ms}ms")
        print(f"LLM Response content length: {len(llm_response.content) if llm_response.content else 0} chars")

        # Handle None or empty response
        if not llm_response.content:
            raise ValueError("LLM returned empty response")

        # Strip markdown code blocks if present
        content = llm_response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]  # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()

        print(f"After cleanup, content length: {len(content)} chars")
        print(f"First 200 chars: {content[:200]}")

        try:
            semantic_layer = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse LLM response as JSON")
            print(f"JSONDecodeError: {e}")
            print(f"Full response (first 1000 chars):")
            print(content[:1000])
            raise ValueError(f"Failed to parse JSON: {e}") from e

        # Add metadata
        result = {
            "database": database_name,
            "semantic_layer": semantic_layer,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "generator_version": "1.0.0",
                "llm_provider": llm_response.provider,
                "llm_model": llm_response.model,
                "tokens_used": llm_response.tokens_used,
                "cost_usd": llm_response.cost_usd,
                "generation_time_ms": llm_response.generation_time_ms,
                "anonymized": anonymize,
                "sample_rows_per_table": self.sample_rows,
                "custom_instructions_used": bool(self.custom_instructions)
            }
        }

        # Optionally include prompt
        if save_prompt:
            result["prompt_used"] = prompt

        return result

    def build_prompt_only(
        self,
        database_name: str,
        anonymize: bool = True
    ) -> Dict[str, Any]:
        """
        Build the prompt without calling the LLM.

        Useful for previewing what will be sent to the LLM before generation.

        Args:
            database_name: Name of the database (e.g., 'world_1', 'network_1')
            anonymize: If True, use anonymous database name in prompt

        Returns:
            Dictionary containing the prompt and metadata
        """
        # Extract schema from Turso (preserves original case from Spider SQLite)
        schema_info = self.turso_extractor.extract_schema(database_name)

        # Sample data from Supabase (has actual data)
        sample_data = self.supabase_extractor.sample_all_tables(
            database_name,
            limit=self.sample_rows
        )

        # Build prompt
        prompt = self._build_prompt(
            database_name=database_name if not anonymize else "database_unknown",
            schema_info=schema_info,
            sample_data=sample_data
        )

        return {
            "database": database_name,
            "prompt": prompt,
            "prompt_length": len(prompt),
            "anonymized": anonymize
        }

    def _build_prompt(
        self,
        database_name: str,
        schema_info: Dict[str, Any],
        sample_data: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Build the prompt for semantic layer generation.

        Args:
            database_name: Name of the database (possibly anonymized)
            schema_info: Schema information from SchemaExtractor
            sample_data: Sample rows from each table

        Returns:
            Complete prompt string
        """
        # Schema section
        schema_text = self._format_schema(schema_info)

        # Sample data section
        samples_text = self._format_samples(sample_data)

        # Build full prompt
        prompt = f"""You are a database documentation expert specializing in creating semantic layers for text-to-SQL systems.

YOUR TASK:
Generate comprehensive, natural language semantic documentation for this database that will help an LLM accurately translate user questions into SQL queries.

CRITICAL CONSTRAINTS:
- Base your analysis ONLY on the provided schema structure and sample data below
- DO NOT research or reference external information about this specific database
- Use your general domain knowledge to infer meaning (e.g., what "population" typically means in databases)
- Reason about business patterns from the schema structure itself

FOREIGN KEY RELATIONSHIPS (CRITICAL FOR QUERY SUCCESS):
The schema below includes documented foreign key relationships. These are MANDATORY for correct query generation.

**RULES FOR RELATIONSHIPS:**
1. INCLUDE ALL foreign keys shown in the schema - do NOT skip any
2. Document the EXACT join pattern for each FK
3. Explain WHEN this join is needed (what questions require it)
4. Do NOT invent relationships not shown in the schema
5. Each FK MUST appear in your "relationships" array with complete join_pattern

**Missing a documented foreign key will cause query failures!**

BRIDGE TABLES (MANY-TO-MANY RELATIONSHIPS):
Some tables exist solely to connect two other tables in many-to-many relationships.

**Identifying Bridge Tables:**
- Typically has 2+ foreign keys and few/no other meaningful columns
- Often named like "table1_table2", "junction_*", or similar
- Required for queries that connect the two referenced tables

**Critical Requirements:**
1. IDENTIFY all bridge tables in your analysis
2. Document the COMPLETE join path through the bridge
3. Mark as "is_bridge_table": true in relationships
4. Explain WHY this table is needed (what M:M relationship it represents)
5. List common mistakes (e.g., "DO NOT skip this table when joining X to Y")

**Example**: If order_items bridges orders to products:
- orders → order_items → products
- Purpose: Enables queries connecting orders to product details (many-to-many relationship)
- Common mistake: Trying to join orders directly to products (will fail or give wrong results)

COLUMN NAME DISAMBIGUATION:
Some column names appear in multiple tables with different meanings.

**When documenting columns:**
1. Identify all column names that appear in 2+ tables
2. Explain the semantic difference between each occurrence
3. Provide usage guidance (when to use table1.column vs table2.column)
4. Warn about ambiguous references that need table qualification

**Example**: If both "orders" and "customers" have a "status" column:
- orders.status: Current fulfillment status (pending, shipped, delivered)
- customers.status: Account status (active, inactive, suspended)
- Usage: Always qualify which table's status is needed for the query

ANALYSIS APPROACH:
Think step-by-step before generating output:
1. Domain identification: What business domain does this database serve?
2. Entity analysis: What are the main business objects being tracked?
3. **Relationship mapping: Document EVERY foreign key shown in schema below**
4. **Bridge table identification: Which tables serve as many-to-many bridges?**
5. Column semantics: What business concept does each column represent?
6. **Column disambiguation: Which column names appear in multiple tables?**
7. Query patterns: What questions would users typically ask?
8. Ambiguities: What might confuse an LLM during text-to-SQL translation?

{self.custom_instructions}

DATABASE: {database_name}

SCHEMA STRUCTURE:
{schema_text}

SAMPLE DATA:
{samples_text}

OUTPUT FORMAT:
Generate a JSON object with this structure:

{{
  "database": "{database_name}",
  "version": "1.0.0",
  "generated_at": "{datetime.utcnow().isoformat()}",

  "overview": {{
    "domain": "string - inferred business domain (e.g., E-commerce, Healthcare)",
    "purpose": "string - what this database is used for in plain English",
    "key_entities": ["string - main business objects tracked"],
    "typical_questions": ["string - common questions users ask about this data"]
  }},

  "tables": [
    {{
      "name": "string - technical table name",
      "business_name": "string - human-friendly name",
      "purpose": "string - what this table represents in business terms",

      "columns": [
        {{
          "name": "string - technical column name",
          "business_name": "string - human-friendly name",
          "business_meaning": "string - what this represents in plain English",
          "synonyms": ["string - 3-5 alternate terms users might use"],
          "typical_filters": ["string - common WHERE clause patterns like 'column = ?' or 'column > ?'"],
          "aggregations": ["string - common aggregation patterns if numeric/date, e.g., 'AVG(column)', 'SUM(column)'"],
          "common_values": ["string - example values users might reference, e.g., 'USA', 'Active', '2023-01-01'"],
          "disambiguation": {{
            "appears_in_tables": ["string - other tables with this column name (if applicable)"],
            "this_table_meaning": "string - what this column means in THIS table",
            "other_table_meanings": {{
              "table_name": "string - what it means in that table"
            }},
            "usage_guidance": "string - when to use which table's version"
          }}
        }}
      ],

      "relationships": [
        {{
          "column": "string - FK column name",
          "references_table": "string - target table name",
          "relationship_type": "string - 'one-to-many', 'many-to-one', or 'many-to-many'",
          "is_bridge_table": "boolean - true if this table bridges a many-to-many relationship",
          "complete_join_path": ["string - if multi-hop join required, show full path (e.g., 'table1 → bridge → table2')"],
          "business_meaning": "string - what this relationship represents in business terms",
          "common_uses": ["string - when/why users would query across these tables"],
          "common_mistakes": ["string - typical errors when using this relationship (e.g., 'DO NOT skip bridge_table')"]
        }}
      ],

      "common_query_patterns": [
        {{
          "question": "string - natural language question users ask",
          "explanation": "string - how to query this table to answer it",
          "involves_joins": ["string - other tables typically joined"]
        }}
      ]
    }}
  ],

  "cross_table_patterns": [
    {{
      "pattern_type": "string - e.g., 'monthly revenue aggregation'",
      "example_question": "string - natural language question",
      "tables_involved": ["string"],
      "typical_structure": "string - general SQL pattern",
      "key_considerations": ["string - gotchas or important details"]
    }}
  ],

  "ambiguities": [
    {{
      "issue": "string - potential confusion for text-to-SQL",
      "example": "string - ambiguous user question",
      "clarification": "string - how to resolve it",
      "affected_elements": ["string - table.column references"]
    }}
  ],

  "query_guidelines": [
    "string - best practices for querying this database",
    "string - common pitfalls to avoid",
    "string - performance considerations"
  ]
}}

QUALITY REQUIREMENTS:
- Business language: Write for non-technical users, focus on WHAT data means, not HOW it's stored
- NO technical schema details: Do NOT include data types, row counts, primary keys, nullability, or FK references - these will be provided separately from the live database schema
- Completeness: Cover all tables and meaningful columns with business context
- Specificity: Be concrete (e.g., "customer's shipping address" not just "address")
- Rich synonyms: Include 3-5 alternate terms users might use for each concept
  * CRITICAL: Synonyms must be UNAMBIGUOUS and NOT match partial words from the column name
  * DO NOT use synonyms that contain fragments of the actual column name
  * BAD examples: "Degree ID" for degree_program_id, "Course ID" for course_id, "Student Name" for student_name_id
  * GOOD examples: "Program Identifier" for degree_program_id, "Enrollment Code" for course_id, "Learner Full Name Identifier" for student_name_id
  * Filter out any synonym that could be confused with the actual business concept vs the ID column
- Query context: Explain how users typically filter/aggregate each field
- Clear relationships: State the BUSINESS MEANING of each relationship (e.g., "links orders to customers")
- Common values: Provide realistic example values users might reference (e.g., 'Active', 'Pending', 'USA')
- Pattern variety: Identify 5-10 common query patterns for this domain

Generate ONLY the JSON object, no additional text or markdown formatting.
"""
        return prompt

    def _format_schema(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for the prompt."""
        lines = []

        for table in schema_info["tables"]:
            lines.append(f"\n===== Table: {table['name']} =====")
            lines.append(f"Row count: {table['row_count']}")

            # Find primary key column name
            pk_cols = [col['name'] for col in table['columns'] if col.get('primary_key')]
            pk_name = ', '.join(pk_cols) if pk_cols else 'unknown'
            lines.append(f"Primary key: {pk_name}")

            lines.append("\nColumns:")

            for col in table["columns"]:
                pk = " [PRIMARY KEY]" if col["primary_key"] else ""
                nullable = " NULL" if col["nullable"] else " NOT NULL"
                lines.append(f"  • {col['name']}: {col['type']}{pk}{nullable}")

            if table["foreign_keys"]:
                lines.append("\n🔗 FOREIGN KEYS (MANDATORY - INCLUDE ALL IN YOUR OUTPUT):")
                for fk in table["foreign_keys"]:
                    source = fk.get('source', 'database')
                    lines.append(
                        f"  → {fk['column']} REFERENCES {fk['referenced_table']}.{fk['referenced_column']}"
                    )
                    lines.append(
                        f"     JOIN: JOIN {fk['referenced_table']} ON {table['name']}.{fk['column']} = {fk['referenced_table']}.{fk['referenced_column']}"
                    )
                    lines.append(f"     Source: {source}")
            else:
                lines.append("\n(No foreign keys)")

        return "\n".join(lines)

    def _format_samples(self, sample_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format sample data for the prompt."""
        from decimal import Decimal

        def make_json_serializable(value):
            """Convert value to JSON-serializable type."""
            if isinstance(value, Decimal):
                return float(value)
            elif value is None:
                return None
            else:
                return value

        lines = []

        for table_name, rows in sample_data.items():
            lines.append(f"\nTable: {table_name}")
            if not rows:
                lines.append("  (no data)")
                continue

            lines.append(f"  Sample rows ({len(rows)}):")
            for i, row in enumerate(rows[:5], 1):  # Show max 5 rows in prompt
                # Convert to JSON-serializable and truncate long values
                formatted_row = {
                    k: (str(v)[:50] + "..." if len(str(v)) > 50 else make_json_serializable(v))
                    for k, v in row.items()
                }
                lines.append(f"    {i}. {json.dumps(formatted_row, ensure_ascii=False)}")

        return "\n".join(lines)


def load_custom_instructions(path: Optional[str] = None) -> str:
    """
    Load custom instructions from file.

    Args:
        path: Path to instructions file. If None, looks for default location.

    Returns:
        Custom instructions string, or empty string if not found
    """
    if path is None:
        # Default location
        path = Path(__file__).parent.parent.parent.parent / "data" / "semantic_layer_instructions.txt"
    else:
        path = Path(path)

    if path.exists():
        return path.read_text().strip()
    return ""
