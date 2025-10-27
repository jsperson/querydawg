"""
Semantic Layer Generator

Generates natural language documentation (semantic layers) for databases
using LLM analysis of schema and sample data.

Uses Supabase PostgreSQL as the source for schema and data extraction.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .llm.base import LLMProvider
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
            database_url: Supabase PostgreSQL connection string
            custom_instructions: Optional custom instructions to add to prompt
            sample_rows: Number of sample rows to extract per table
        """
        self.llm = llm
        self.database_url = database_url
        self.custom_instructions = custom_instructions or ""
        self.sample_rows = sample_rows
        self.schema_extractor = SupabaseSchemaExtractor(database_url)

    def generate(
        self,
        database_name: str,
        anonymize: bool = True,
        save_prompt: bool = True
    ) -> Dict[str, Any]:
        """
        Generate semantic layer for a database.

        Args:
            database_name: Name of the database schema in Supabase (e.g., 'world_1')
            anonymize: If True, use anonymous database name in prompt
            save_prompt: If True, include the prompt in the output

        Returns:
            Dictionary containing semantic layer and metadata
        """
        # Extract schema from Supabase
        schema_info = self.schema_extractor.extract_schema(database_name)

        # Sample data from each table in Supabase
        sample_data = self.schema_extractor.sample_all_tables(
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
        try:
            semantic_layer = json.loads(llm_response.content)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response: {llm_response.content[:500]}...")
            raise

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
            database_name: Name of the database schema in Supabase (e.g., 'world_1')
            anonymize: If True, use anonymous database name in prompt

        Returns:
            Dictionary containing the prompt and metadata
        """
        # Extract schema from Supabase
        schema_info = self.schema_extractor.extract_schema(database_name)

        # Sample data from each table in Supabase
        sample_data = self.schema_extractor.sample_all_tables(
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

ANALYSIS APPROACH:
Think step-by-step before generating output:
1. Domain identification: What business domain does this database serve?
2. Entity analysis: What are the main business objects being tracked?
3. Relationship mapping: How do these entities relate to each other?
4. Column semantics: What business concept does each column represent?
5. Query patterns: What questions would users typically ask?
6. Ambiguities: What might confuse an LLM during text-to-SQL translation?

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
      "row_count": number,
      "business_name": "string - human-friendly name",
      "purpose": "string - what this table represents in business terms",
      "primary_key": "string - primary key column(s)",

      "columns": [
        {{
          "name": "string - technical column name",
          "type": "string - SQL data type",
          "nullable": boolean,
          "business_name": "string - human-friendly name",
          "business_meaning": "string - what this represents in plain English",
          "synonyms": ["string - 3-5 alternate terms users might use"],
          "sample_values": ["values from sample data provided"],
          "typical_filters": ["string - common WHERE clause patterns"],
          "aggregations": ["string - common aggregation patterns if numeric/date"],
          "value_constraints": "string - any known constraints or ranges"
        }}
      ],

      "relationships": [
        {{
          "type": "foreign_key",
          "column": "string",
          "references_table": "string",
          "references_column": "string",
          "business_meaning": "string - what this relationship represents",
          "cardinality": "string - one-to-many, many-to-one, etc.",
          "join_pattern": "string - typical SQL join syntax",
          "common_uses": ["string - when users would query across these tables"]
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

  "domain_glossary": [
    {{
      "business_term": "string - term users would use",
      "technical_mapping": "string - which table.column represents this",
      "definition": "string - clear definition",
      "synonyms": ["string - alternate phrasings"],
      "example_usage": "string - how users would reference this in questions"
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
- Business language: Write for non-technical users
- Completeness: Cover all tables and meaningful columns
- Specificity: Be concrete (e.g., "customer's shipping address" not just "address")
- Rich synonyms: Include 3-5 alternate terms for each key concept
- Realistic examples: Provide 2-3 actual sample values from the data
- Query context: Explain how each element is commonly queried
- Clear relationships: State the business meaning of every foreign key
- Pattern variety: Identify 5-10 common query patterns for this domain

Generate ONLY the JSON object, no additional text or markdown formatting.
"""
        return prompt

    def _format_schema(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for the prompt."""
        lines = []

        for table in schema_info["tables"]:
            lines.append(f"\nTable: {table['name']}")
            lines.append(f"  Row count: {table['row_count']}")
            lines.append("  Columns:")

            for col in table["columns"]:
                pk = " [PRIMARY KEY]" if col["primary_key"] else ""
                nullable = " NULL" if col["nullable"] else " NOT NULL"
                default = f" DEFAULT {col.get('default', '')}" if col.get("default") else ""
                lines.append(f"    - {col['name']}: {col['type']}{pk}{nullable}{default}")

            if table["foreign_keys"]:
                lines.append("  Foreign Keys:")
                for fk in table["foreign_keys"]:
                    lines.append(
                        f"    - {fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}"
                    )

        return "\n".join(lines)

    def _format_samples(self, sample_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format sample data for the prompt."""
        lines = []

        for table_name, rows in sample_data.items():
            lines.append(f"\nTable: {table_name}")
            if not rows:
                lines.append("  (no data)")
                continue

            lines.append(f"  Sample rows ({len(rows)}):")
            for i, row in enumerate(rows[:5], 1):  # Show max 5 rows in prompt
                # Truncate long values
                formatted_row = {
                    k: (str(v)[:50] + "..." if len(str(v)) > 50 else v)
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
