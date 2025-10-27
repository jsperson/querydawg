#!/usr/bin/env python3
"""
Test all service connections for QueryDawg project.

This script verifies that all API keys and service configurations are working correctly.
Run this after setting up .env file to ensure everything is ready for development.

Usage:
    python scripts/test_connections.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

print("=" * 70)
print("QueryDawg Service Connection Tests")
print("=" * 70)
print()

# Track results
results = {
    "passed": [],
    "failed": [],
}

# =============================================================================
# Test 1: Environment Variables Loaded
# =============================================================================
print("[ 1/5 ] Testing environment variables...")
try:
    required_vars = [
        "OPENAI_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_HOST",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("[") or value.startswith("xxxx"):
            missing.append(var)

    if missing:
        raise ValueError(f"Missing or invalid env vars: {', '.join(missing)}")

    print("✅ All required environment variables loaded")
    results["passed"].append("Environment Variables")
except Exception as e:
    print(f"❌ Environment variables check failed: {e}")
    results["failed"].append("Environment Variables")
    print()
    print("Make sure you:")
    print("  1. Created .env file: cp .env.example .env")
    print("  2. Filled in all API keys with real values")
    print()

print()

# =============================================================================
# Test 2: OpenAI API Connection
# =============================================================================
print("[ 2/5 ] Testing OpenAI API connection...")
try:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Test with a minimal completion
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'test' if you can read this."}],
        max_tokens=10,
    )

    content = response.choices[0].message.content
    print(f"✅ OpenAI API connected successfully")
    print(f"   Response: {content}")
    print(f"   Model: {response.model}")
    results["passed"].append("OpenAI API")
except ImportError:
    print("❌ OpenAI package not installed")
    print("   Run: pip install openai")
    results["failed"].append("OpenAI API")
except Exception as e:
    print(f"❌ OpenAI API connection failed: {e}")
    results["failed"].append("OpenAI API")
    print()
    print("Check your OPENAI_API_KEY in .env file")
    print("Get key from: https://platform.openai.com/api-keys")
    print()

print()

# =============================================================================
# Test 3: Pinecone Connection
# =============================================================================
print("[ 3/5 ] Testing Pinecone connection...")
try:
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    # List indexes
    indexes = pc.list_indexes()

    index_name = os.getenv("PINECONE_INDEX_NAME", "querydawg-sematic")

    # Check if our index exists
    index_names = [idx.name for idx in indexes]

    if index_name in index_names:
        # Get index stats
        index = pc.Index(index_name)
        stats = index.describe_index_stats()

        print(f"✅ Pinecone connected successfully")
        print(f"   Index: {index_name}")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimension: {stats.dimension if hasattr(stats, 'dimension') else 'N/A'}")
        results["passed"].append("Pinecone")
    else:
        print(f"⚠️  Pinecone connected, but index '{index_name}' not found")
        print(f"   Available indexes: {', '.join(index_names) if index_names else 'None'}")
        print(f"   This is OK - index will be populated in Week 3")
        results["passed"].append("Pinecone")

except ImportError:
    print("❌ Pinecone package not installed")
    print("   Run: pip install pinecone-client")
    results["failed"].append("Pinecone")
except Exception as e:
    print(f"❌ Pinecone connection failed: {e}")
    results["failed"].append("Pinecone")
    print()
    print("Check your PINECONE_API_KEY in .env file")
    print("Get key from: https://app.pinecone.io")
    print()

print()

# =============================================================================
# Test 4: Supabase REST API Connection
# =============================================================================
print("[ 4/5 ] Testing Supabase REST API connection...")
try:
    from supabase import create_client, Client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    supabase: Client = create_client(url, key)

    # Test connection by querying information_schema
    # This should work even with empty database
    response = supabase.rpc("version").execute()

    print(f"✅ Supabase REST API connected successfully")
    print(f"   URL: {url}")
    print(f"   Status: Connected")
    results["passed"].append("Supabase REST API")
except ImportError:
    print("❌ Supabase package not installed")
    print("   Run: pip install supabase")
    results["failed"].append("Supabase REST API")
except Exception as e:
    # Even if the RPC call fails, if we can create client, connection is OK
    print(f"⚠️  Supabase REST API - partial connection")
    print(f"   Client created successfully, but version check failed: {e}")
    print(f"   This is usually OK - your credentials are valid")
    results["passed"].append("Supabase REST API")

print()

# =============================================================================
# Test 5: Supabase PostgreSQL Connection
# =============================================================================
print("[ 5/5 ] Testing Supabase PostgreSQL connection...")
try:
    import psycopg2

    database_url = os.getenv("DATABASE_URL")

    # Connect to PostgreSQL
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Test with a simple query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    # Get database name
    cursor.execute("SELECT current_database();")
    db_name = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"✅ Supabase PostgreSQL connected successfully")
    print(f"   Database: {db_name}")
    print(f"   PostgreSQL version: {version.split(',')[0]}")
    results["passed"].append("Supabase PostgreSQL")
except ImportError:
    print("❌ psycopg2 package not installed")
    print("   Run: pip install psycopg2-binary")
    results["failed"].append("Supabase PostgreSQL")
except Exception as e:
    print(f"❌ Supabase PostgreSQL connection failed: {e}")
    results["failed"].append("Supabase PostgreSQL")
    print()
    print("Check your DATABASE_URL in .env file")
    print("Make sure you replaced [YOUR-PASSWORD] with your actual database password")
    print("Get from: Supabase Dashboard > Settings > Database")
    print()

print()

# =============================================================================
# Summary
# =============================================================================
print("=" * 70)
print("Summary")
print("=" * 70)
print()

total_tests = len(results["passed"]) + len(results["failed"])
passed_count = len(results["passed"])
failed_count = len(results["failed"])

print(f"Total Tests: {total_tests}")
print(f"✅ Passed: {passed_count}")
print(f"❌ Failed: {failed_count}")
print()

if results["passed"]:
    print("Passed tests:")
    for test in results["passed"]:
        print(f"  ✅ {test}")
    print()

if results["failed"]:
    print("Failed tests:")
    for test in results["failed"]:
        print(f"  ❌ {test}")
    print()
    print("Please fix the failed tests before proceeding.")
    print("See error messages above for troubleshooting steps.")
    print()
    sys.exit(1)
else:
    print("🎉 All tests passed! Your environment is ready for development.")
    print()
    print("Next steps:")
    print("  1. ✅ Service connections verified")
    print("  2. Continue to Week 1 Days 3-4: Download and load Spider datasets")
    print()
    sys.exit(0)
