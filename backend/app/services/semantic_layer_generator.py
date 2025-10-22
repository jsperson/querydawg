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

from ..llm.base import BaseLLM
from ..database.supabase_schema_extractor import SupabaseSchemaExtractor


class SemanticLayerGenerator:
    """Generate semantic layers for databases using LLM."""

    def __init__(
        self,
        llm: BaseLLM,
        database_url: str,
        custom_instructions: Optional[str] = None,
        sample_rows: int = 10
    ):
        """
        Initialize the semantic layer generator.

        Args:
            llm: LLM instance to use for generation
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

        response = self.llm.generate(
            prompt=prompt,
            system_message="You are a database documentation expert specializing in creating comprehensive, business-friendly database documentation."
        )

        # Parse JSON response
        try:
            semantic_layer = json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response: {response[:500]}...")
            raise

        # Add metadata
        result = {
            "database": database_name,
            "semantic_layer": semantic_layer,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "generator_version": "1.0.0",
                "llm_provider": self.llm.provider,
                "llm_model": self.llm.model,
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
        prompt = f"""You are a database documentation expert. Generate a comprehensive semantic layer for this database.

INSTRUCTIONS:
- Use your general domain knowledge to infer meaning (e.g., what "population" typically means, common business patterns)
- DO NOT research or reference this specific database or dataset
- Base your analysis ONLY on the schema structure and sample data provided below
- Generate a complete semantic layer in JSON format following the schema provided

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
  "domain": "string - inferred business domain (e.g., Geography, E-commerce, Healthcare)",
  "description": "string - high-level database purpose based on tables and data",

  "tables": [
    {{
      "name": "string - technical table name",
      "business_name": "string - human-friendly name",
      "description": "string - what this table represents",
      "primary_use_cases": ["string - common query patterns"],

      "columns": [
        {{
          "name": "string - technical column name",
          "business_name": "string - human-friendly name",
          "description": "string - what this column means",
          "data_type": "string - SQL data type",
          "sample_values": ["values from sample data"],
          "synonyms": ["string - alternative names"],
          "common_filters": ["string - typical WHERE conditions"],
          "aggregation_patterns": ["string - common aggregations if numeric"]
        }}
      ],

      "relationships": [
        {{
          "type": "foreign_key",
          "to_table": "string",
          "to_column": "string",
          "description": "string - what this relationship means",
          "cardinality": "string - one-to-many, many-to-one, etc."
        }}
      ],

      "common_queries": [
        {{
          "question": "string - natural language question",
          "description": "string - query pattern explanation",
          "involves_tables": ["string - other tables in join"]
        }}
      ]
    }}
  ],

  "cross_table_insights": [
    {{
      "description": "string - important multi-table patterns",
      "tables": ["string"],
      "use_case": "string"
    }}
  ],

  "domain_terminology": {{
    "term": "definition - domain-specific terms"
  }},

  "query_guidelines": [
    "string - best practices for querying this database"
  ]
}}

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
