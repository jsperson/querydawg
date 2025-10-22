# Semantic Layer Schema Design

## Overview

The semantic layer is a natural language documentation layer that bridges the gap between technical database schemas and business/human understanding. It provides context that enables LLMs to generate more accurate SQL queries.

## Design Principles

1. **Human-Readable**: Written in natural language, not code
2. **Business-Focused**: Describes data in terms users understand, not technical implementation
3. **Context-Rich**: Includes purpose, relationships, and common query patterns
4. **Maintainable**: Structured format that can be generated and updated automatically
5. **LLM-Optimized**: Designed to be consumed by text-to-SQL prompts

## Schema Structure

```json
{
  "database": "string",           // Database name (e.g., "world_1")
  "version": "string",            // Semantic layer version (e.g., "1.0.0")
  "generated_at": "timestamp",    // When this was generated
  "domain": "string",             // Business domain (e.g., "Geography", "E-commerce")
  "description": "string",        // High-level database purpose

  "tables": [
    {
      "name": "string",           // Technical table name
      "business_name": "string",  // Human-friendly name (e.g., "Countries")
      "description": "string",    // What this table represents
      "primary_use_cases": [      // Common ways this table is queried
        "string"
      ],

      "columns": [
        {
          "name": "string",       // Technical column name
          "business_name": "string",  // Human-friendly name
          "description": "string",    // What this column means
          "data_type": "string",      // SQL data type
          "sample_values": [          // Example values for context
            "any"
          ],
          "synonyms": [               // Alternative names/terms
            "string"
          ],
          "common_filters": [         // Typical WHERE conditions
            "string"
          ],
          "aggregation_patterns": [   // Common aggregations (SUM, AVG, etc.)
            "string"
          ]
        }
      ],

      "relationships": [
        {
          "type": "foreign_key",      // Relationship type
          "to_table": "string",       // Related table name
          "to_column": "string",      // Related column name
          "description": "string",    // What this relationship means
          "cardinality": "string"     // "one-to-many", "many-to-one", etc.
        }
      ],

      "common_queries": [
        {
          "question": "string",       // Natural language question
          "description": "string",    // Query pattern explanation
          "involves_tables": [        // Other tables typically joined
            "string"
          ]
        }
      ]
    }
  ],

  "cross_table_insights": [
    {
      "description": "string",        // Important multi-table relationships
      "tables": ["string"],           // Involved tables
      "use_case": "string"            // When to use this pattern
    }
  ],

  "domain_terminology": {
    "term": "definition"              // Domain-specific terms and meanings
  },

  "query_guidelines": [
    "string"                          // Best practices for querying this database
  ]
}
```

## Example: World Database

```json
{
  "database": "world_1",
  "version": "1.0.0",
  "generated_at": "2025-10-22T10:00:00Z",
  "domain": "Geography and Demographics",
  "description": "Contains information about countries, cities, and languages worldwide. Useful for geographic, demographic, and political queries.",

  "tables": [
    {
      "name": "country",
      "business_name": "Countries",
      "description": "Information about world countries including population, area, government, and economy",
      "primary_use_cases": [
        "Finding countries by region or continent",
        "Comparing countries by population or GDP",
        "Analyzing government types and independence dates"
      ],

      "columns": [
        {
          "name": "Code",
          "business_name": "Country Code",
          "description": "Three-letter ISO country code (primary identifier)",
          "data_type": "CHAR(3)",
          "sample_values": ["USA", "CHN", "IND", "BRA"],
          "synonyms": ["ISO code", "country abbreviation"],
          "common_filters": ["Equal to specific country"],
          "aggregation_patterns": ["COUNT for number of countries"]
        },
        {
          "name": "Name",
          "business_name": "Country Name",
          "description": "Full official name of the country",
          "data_type": "VARCHAR(52)",
          "sample_values": ["United States", "China", "India", "Brazil"],
          "synonyms": ["country", "nation"],
          "common_filters": ["LIKE for partial name matching", "IN for multiple countries"],
          "aggregation_patterns": []
        },
        {
          "name": "Population",
          "business_name": "Population",
          "description": "Total number of people living in the country",
          "data_type": "INTEGER",
          "sample_values": [1400000000, 330000000, 210000000],
          "synonyms": ["inhabitants", "people", "residents"],
          "common_filters": ["Greater than for populous countries", "BETWEEN for population ranges"],
          "aggregation_patterns": ["SUM for total population", "AVG for average", "MAX/MIN for extremes"]
        },
        {
          "name": "Continent",
          "business_name": "Continent",
          "description": "The continent where this country is located",
          "data_type": "VARCHAR(20)",
          "sample_values": ["Asia", "Europe", "Africa", "North America", "South America"],
          "synonyms": ["region"],
          "common_filters": ["Equal to specific continent", "IN for multiple continents"],
          "aggregation_patterns": ["GROUP BY for continent-level statistics"]
        },
        {
          "name": "SurfaceArea",
          "business_name": "Land Area",
          "description": "Total land area in square kilometers",
          "data_type": "FLOAT",
          "sample_values": [9833520.0, 9147593.0, 3287263.0],
          "synonyms": ["area", "size", "territory"],
          "common_filters": ["Greater than for large countries", "ORDER BY for ranking"],
          "aggregation_patterns": ["SUM for total area", "AVG for average area"]
        }
      ],

      "relationships": [
        {
          "type": "foreign_key",
          "to_table": "city",
          "to_column": "CountryCode",
          "description": "A country has many cities. Use this to find all cities in a country.",
          "cardinality": "one-to-many"
        },
        {
          "type": "foreign_key",
          "to_table": "countrylanguage",
          "to_column": "CountryCode",
          "description": "A country has multiple languages. Use this to find what languages are spoken in a country.",
          "cardinality": "one-to-many"
        }
      ],

      "common_queries": [
        {
          "question": "What are the top 10 countries by population?",
          "description": "Sort countries by population descending and limit to 10",
          "involves_tables": []
        },
        {
          "question": "How many countries are in each continent?",
          "description": "Group by continent and count",
          "involves_tables": []
        },
        {
          "question": "What countries in Asia have population over 100 million?",
          "description": "Filter by continent and population threshold",
          "involves_tables": []
        }
      ]
    },
    {
      "name": "city",
      "business_name": "Cities",
      "description": "Information about cities worldwide including population and which country they belong to",
      "primary_use_cases": [
        "Finding cities in a specific country",
        "Finding largest cities globally or by region",
        "Comparing city populations"
      ],

      "columns": [
        {
          "name": "Name",
          "business_name": "City Name",
          "description": "Name of the city",
          "data_type": "VARCHAR(35)",
          "sample_values": ["New York", "Tokyo", "London", "Shanghai"],
          "synonyms": ["city", "urban area"],
          "common_filters": ["LIKE for partial matching", "IN for multiple cities"],
          "aggregation_patterns": ["COUNT for number of cities"]
        },
        {
          "name": "CountryCode",
          "business_name": "Country",
          "description": "The country this city belongs to (links to country.Code)",
          "data_type": "CHAR(3)",
          "sample_values": ["USA", "JPN", "GBR", "CHN"],
          "synonyms": ["nation"],
          "common_filters": ["Equal to specific country", "IN for multiple countries"],
          "aggregation_patterns": ["GROUP BY to aggregate by country"]
        },
        {
          "name": "Population",
          "business_name": "Population",
          "description": "Number of people living in the city",
          "data_type": "INTEGER",
          "sample_values": [8000000, 13000000, 9000000],
          "synonyms": ["inhabitants", "residents"],
          "common_filters": ["Greater than for large cities", "ORDER BY for ranking"],
          "aggregation_patterns": ["SUM for total urban population", "AVG for average city size"]
        }
      ],

      "relationships": [
        {
          "type": "foreign_key",
          "to_table": "country",
          "to_column": "Code",
          "description": "Each city belongs to exactly one country. Join to get country details.",
          "cardinality": "many-to-one"
        }
      ],

      "common_queries": [
        {
          "question": "What are the largest cities in China?",
          "description": "Filter by country code and sort by population",
          "involves_tables": []
        },
        {
          "question": "Which countries have the most cities in the database?",
          "description": "Group by country code and count",
          "involves_tables": ["country"]
        },
        {
          "question": "What is the total urban population of Europe?",
          "description": "Join with country, filter by continent, sum city populations",
          "involves_tables": ["country"]
        }
      ]
    }
  ],

  "cross_table_insights": [
    {
      "description": "To analyze cities by continent, you must join city -> country -> filter by Continent",
      "tables": ["city", "country"],
      "use_case": "Queries about cities in a specific continent or region"
    },
    {
      "description": "Country capital cities can be found by joining country.Capital (city ID) with city.ID",
      "tables": ["country", "city"],
      "use_case": "Finding capital cities"
    }
  ],

  "domain_terminology": {
    "Continent": "One of seven major land masses: Asia, Africa, North America, South America, Europe, Australia, Antarctica",
    "Country Code": "ISO 3166-1 alpha-3 three-letter country code",
    "Surface Area": "Measured in square kilometers, includes land area only"
  },

  "query_guidelines": [
    "When comparing countries, always consider whether to use total values or per-capita values",
    "City populations may be outdated - this is historical data",
    "Not all cities in a country are in the database - typically only larger cities are included",
    "Use LIMIT when asking for 'top N' results",
    "When filtering by continent, remember it's stored in the country table, not city table"
  ]
}
```

## Key Components Explained

### 1. Database-Level Metadata
- **domain**: Helps LLM understand the context (e.g., "E-commerce" vs "Healthcare")
- **description**: One-line summary of what this database contains
- **cross_table_insights**: Common multi-table patterns that aren't obvious from schema alone

### 2. Table-Level Information
- **business_name**: How users refer to this table (more intuitive than technical names)
- **primary_use_cases**: Common reasons to query this table
- **common_queries**: Example questions with their patterns

### 3. Column-Level Details
- **business_name**: User-friendly column name
- **description**: What this column actually means in business terms
- **sample_values**: Help LLM understand data format and content
- **synonyms**: Alternative terms users might use
- **common_filters**: Typical WHERE clause patterns
- **aggregation_patterns**: How this column is typically aggregated

### 4. Relationships
- **description**: Plain English explanation of the relationship
- **cardinality**: Helps with JOIN optimization and understanding data model

### 5. Domain Terminology
- Defines domain-specific terms that might be ambiguous
- Helps LLM use correct terminology in SQL generation

### 6. Query Guidelines
- Best practices specific to this database
- Common pitfalls to avoid
- Data quality notes

## Benefits Over Schema-Only Approach

1. **Context**: Explains *why* data is structured this way
2. **Business Language**: Bridges technical schema and user questions
3. **Query Patterns**: Shows common query idioms for this domain
4. **Relationships**: Explains semantic meaning of JOINs
5. **Data Quality**: Notes about data limitations or quirks
6. **Examples**: Sample values help with format understanding

## Storage Format

- **Primary**: JSON files in `data/semantic_layers/{database_name}.json`
- **Future**: Vector database (Pinecone) for semantic search
- **Version Control**: Git-tracked for manual refinements

## Generation Strategy

1. **Automated (Week 2)**: Use LLM to generate initial semantic layer from schema
2. **Manual Refinement (Week 3-4)**: Review and improve generated content
3. **Iterative Improvement**: Update based on query performance

## Usage in Text-to-SQL

The semantic layer will be injected into the LLM prompt:

```
You are a SQL expert. Generate SQL for the following question.

Database: world_1
Domain: Geography and Demographics
Description: [semantic layer description]

Tables:
[Full semantic layer information]

Question: What are the 5 largest cities in Asia?

Generate SQL query:
```

This provides rich context that schema alone cannot provide.
