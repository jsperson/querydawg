#!/usr/bin/env python3
"""Test if auto-embed code works"""
import os
from dotenv import load_dotenv

load_dotenv()

# Check environment variables
required_vars = [
    "OPENAI_API_KEY",
    "PINECONE_API_KEY", 
    "PINECONE_ENVIRONMENT",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY"
]

print("Checking environment variables:")
all_present = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✓ {var}: {'*' * 10}")
    else:
        print(f"  ✗ {var}: MISSING")
        all_present = False

if not all_present:
    print("\n❌ Missing environment variables - auto-embed would be skipped")
else:
    print("\n✅ All environment variables present - auto-embed should run")

# Test imports
print("\nTesting imports:")
try:
    from app.services.embedding_service import EmbeddingService
    print("  ✓ EmbeddingService imported")
except Exception as e:
    print(f"  ✗ EmbeddingService import failed: {e}")

try:
    from app.database.metadata_store import MetadataStore
    print("  ✓ MetadataStore imported")
except Exception as e:
    print(f"  ✗ MetadataStore import failed: {e}")
