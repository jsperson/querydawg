"""
Embedding Service for Semantic Layer Vectorization

Handles embedding generation and upload to Pinecone for semantic search.
Implements intelligent chunking of semantic layer documents.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec


class EmbeddingService:
    """Service for generating and managing embeddings of semantic layers."""

    def __init__(
        self,
        openai_api_key: str,
        pinecone_api_key: str,
        pinecone_environment: str,
        pinecone_index_name: str,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536
    ):
        """
        Initialize the embedding service.

        Args:
            openai_api_key: OpenAI API key
            pinecone_api_key: Pinecone API key
            pinecone_environment: Pinecone environment
            pinecone_index_name: Name of the Pinecone index
            embedding_model: OpenAI embedding model to use
            embedding_dimensions: Dimension of embeddings (1536 for text-embedding-3-small)
        """
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions

        # Initialize Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = pinecone_index_name
        self.index = self.pc.Index(pinecone_index_name)

    def chunk_semantic_layer(
        self,
        semantic_layer: Dict[str, Any],
        database_name: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk semantic layer into meaningful pieces for embedding.

        Strategy:
        1. Database Overview - Single chunk with domain, purpose, key entities
        2. Table Documentation - One chunk per table with all its details
        3. Cross-Table Patterns - One chunk per pattern
        4. Domain Glossary - One chunk with all glossary terms
        5. Query Guidelines - One chunk with all guidelines
        6. Ambiguities - One chunk with all ambiguities

        Args:
            semantic_layer: The semantic layer JSON
            database_name: Name of the database

        Returns:
            List of chunks, each with 'text', 'metadata', and 'id'
        """
        chunks = []

        # 1. Database Overview Chunk
        if "overview" in semantic_layer:
            overview = semantic_layer["overview"]
            text = f"""Database: {database_name}
Domain: {overview.get('domain', 'Unknown')}
Purpose: {overview.get('purpose', 'N/A')}

Key Entities: {', '.join(overview.get('key_entities', []))}

Typical Questions:
{chr(10).join(f"- {q}" for q in overview.get('typical_questions', []))}
"""
            chunks.append({
                "id": self._generate_id(database_name, "overview"),
                "text": text,
                "metadata": {
                    "database": database_name,
                    "chunk_type": "overview",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # 2. Table Documentation Chunks (one per table)
        for table in semantic_layer.get("tables", []):
            table_name = table.get("name", "unknown")

            # Table overview
            text_parts = [
                f"Table: {table_name}",
                f"Business Name: {table.get('business_name', table_name)}",
                f"Purpose: {table.get('purpose', 'N/A')}",
                f"Row Count: {table.get('row_count', 0):,}",
                f"Primary Key: {table.get('primary_key', 'N/A')}",
                "",
                "Columns:"
            ]

            # Column details
            for col in table.get("columns", []):
                col_text = [
                    f"  - {col['name']} ({col.get('type', 'unknown')})",
                    f"    Business Name: {col.get('business_name', col['name'])}",
                    f"    Meaning: {col.get('business_meaning', 'N/A')}",
                ]

                if col.get('synonyms'):
                    col_text.append(f"    Synonyms: {', '.join(col['synonyms'])}")

                if col.get('typical_filters'):
                    col_text.append(f"    Common Filters: {', '.join(col['typical_filters'])}")

                if col.get('aggregations'):
                    col_text.append(f"    Aggregations: {', '.join(col['aggregations'])}")

                text_parts.extend(col_text)

            # Relationships
            if table.get("relationships"):
                text_parts.append("\nRelationships:")
                for rel in table["relationships"]:
                    rel_text = f"  - {rel.get('column')} → {rel.get('references_table')}.{rel.get('references_column')}"
                    rel_text += f"\n    Meaning: {rel.get('business_meaning', 'N/A')}"
                    rel_text += f"\n    Cardinality: {rel.get('cardinality', 'unknown')}"
                    text_parts.append(rel_text)

            # Common query patterns
            if table.get("common_query_patterns"):
                text_parts.append("\nCommon Query Patterns:")
                for pattern in table["common_query_patterns"]:
                    text_parts.append(f"  Q: {pattern.get('question', 'N/A')}")
                    text_parts.append(f"  A: {pattern.get('explanation', 'N/A')}")
                    if pattern.get('involves_joins'):
                        text_parts.append(f"     Joins: {', '.join(pattern['involves_joins'])}")

            chunks.append({
                "id": self._generate_id(database_name, f"table_{table_name}"),
                "text": "\n".join(text_parts),
                "metadata": {
                    "database": database_name,
                    "chunk_type": "table",
                    "table_name": table_name,
                    "row_count": table.get('row_count', 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # 3. Cross-Table Patterns
        if semantic_layer.get("cross_table_patterns"):
            text_parts = [f"Cross-Table Query Patterns for {database_name}:", ""]

            for pattern in semantic_layer["cross_table_patterns"]:
                text_parts.extend([
                    f"Pattern: {pattern.get('pattern_type', 'N/A')}",
                    f"Example Question: {pattern.get('example_question', 'N/A')}",
                    f"Tables: {', '.join(pattern.get('tables_involved', []))}",
                    f"Structure: {pattern.get('typical_structure', 'N/A')}",
                    f"Considerations: {', '.join(pattern.get('key_considerations', []))}",
                    ""
                ])

            chunks.append({
                "id": self._generate_id(database_name, "cross_table_patterns"),
                "text": "\n".join(text_parts),
                "metadata": {
                    "database": database_name,
                    "chunk_type": "cross_table_patterns",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # 4. Domain Glossary
        if semantic_layer.get("domain_glossary"):
            text_parts = [f"Domain Glossary for {database_name}:", ""]

            for term in semantic_layer["domain_glossary"]:
                text_parts.extend([
                    f"Term: {term.get('business_term', 'N/A')}",
                    f"  Technical Mapping: {term.get('technical_mapping', 'N/A')}",
                    f"  Definition: {term.get('definition', 'N/A')}",
                    f"  Synonyms: {', '.join(term.get('synonyms', []))}",
                    f"  Example Usage: {term.get('example_usage', 'N/A')}",
                    ""
                ])

            chunks.append({
                "id": self._generate_id(database_name, "glossary"),
                "text": "\n".join(text_parts),
                "metadata": {
                    "database": database_name,
                    "chunk_type": "glossary",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # 5. Ambiguities
        if semantic_layer.get("ambiguities"):
            text_parts = [f"Potential Ambiguities for {database_name}:", ""]

            for ambiguity in semantic_layer["ambiguities"]:
                text_parts.extend([
                    f"Issue: {ambiguity.get('issue', 'N/A')}",
                    f"  Example: {ambiguity.get('example', 'N/A')}",
                    f"  Clarification: {ambiguity.get('clarification', 'N/A')}",
                    f"  Affected Elements: {', '.join(ambiguity.get('affected_elements', []))}",
                    ""
                ])

            chunks.append({
                "id": self._generate_id(database_name, "ambiguities"),
                "text": "\n".join(text_parts),
                "metadata": {
                    "database": database_name,
                    "chunk_type": "ambiguities",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        # 6. Query Guidelines
        if semantic_layer.get("query_guidelines"):
            text_parts = [f"Query Guidelines for {database_name}:", ""]

            for guideline in semantic_layer["query_guidelines"]:
                if isinstance(guideline, str):
                    text_parts.append(f"- {guideline}")
                elif isinstance(guideline, dict):
                    text_parts.append(f"- {guideline.get('guideline', guideline)}")

            chunks.append({
                "id": self._generate_id(database_name, "guidelines"),
                "text": "\n".join(text_parts),
                "metadata": {
                    "database": database_name,
                    "chunk_type": "guidelines",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })

        return chunks

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def embed_semantic_layer(
        self,
        semantic_layer: Dict[str, Any],
        database_name: str
    ) -> Dict[str, Any]:
        """
        Embed a complete semantic layer and upload to Pinecone.

        Args:
            semantic_layer: The semantic layer JSON
            database_name: Name of the database

        Returns:
            Dictionary with upload statistics
        """
        # Chunk the semantic layer
        chunks = self.chunk_semantic_layer(semantic_layer, database_name)

        print(f"Created {len(chunks)} chunks for {database_name}")

        # Generate embeddings for each chunk
        vectors = []
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            print(f"Embedding chunk {i+1}/{len(chunks)}: {chunk['metadata']['chunk_type']}")

            # Generate embedding
            embedding = self.embed_text(chunk['text'])

            # Prepare vector for Pinecone
            vectors.append({
                "id": chunk['id'],
                "values": embedding,
                "metadata": {
                    **chunk['metadata'],
                    "text": chunk['text'][:1000]  # Store first 1000 chars in metadata
                }
            })

            # Estimate tokens (rough: 1 token ≈ 4 chars)
            total_tokens += len(chunk['text']) // 4

        # Upload to Pinecone in batch
        print(f"Uploading {len(vectors)} vectors to Pinecone...")
        self.index.upsert(vectors=vectors)

        return {
            "database": database_name,
            "chunks_created": len(chunks),
            "vectors_uploaded": len(vectors),
            "estimated_tokens": total_tokens,
            "estimated_cost_usd": total_tokens * 0.00000002,  # $0.02 per 1M tokens
            "chunk_types": [c['metadata']['chunk_type'] for c in chunks]
        }

    def delete_database_embeddings(self, database_name: str) -> Dict[str, Any]:
        """
        Delete all embeddings for a specific database.

        Args:
            database_name: Name of the database

        Returns:
            Dictionary with deletion statistics
        """
        # Delete by filter (Pinecone supports metadata filtering)
        self.index.delete(filter={"database": {"$eq": database_name}})

        return {
            "database": database_name,
            "status": "deleted"
        }

    def search_semantic_context(
        self,
        query: str,
        database_name: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant semantic context for a query.

        Args:
            query: Natural language query
            database_name: Database to search within
            top_k: Number of results to return

        Returns:
            List of relevant chunks with scores
        """
        # Embed the query
        query_embedding = self.embed_text(query)

        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            filter={"database": {"$eq": database_name}},
            top_k=top_k,
            include_metadata=True
        )

        # Format results
        context_chunks = []
        for match in results['matches']:
            context_chunks.append({
                "chunk_type": match['metadata'].get('chunk_type', 'unknown'),
                "table_name": match['metadata'].get('table_name'),
                "text": match['metadata'].get('text', 'N/A'),
                "score": match['score']
            })

        return context_chunks

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.get('total_vector_count', 0),
            "dimension": stats.get('dimension', self.embedding_dimensions),
            "index_fullness": stats.get('index_fullness', 0.0),
            "namespaces": stats.get('namespaces', {})
        }

    def _generate_id(self, database_name: str, chunk_identifier: str) -> str:
        """Generate a unique ID for a chunk."""
        content = f"{database_name}:{chunk_identifier}"
        return hashlib.md5(content.encode()).hexdigest()
