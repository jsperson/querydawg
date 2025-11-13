#!/usr/bin/env python3
"""
Debug raw Turso API responses
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    org = os.getenv("TURSO_ORG", "jsperson")
    account_token = os.getenv("TURSO_TOKEN")

    if not account_token:
        print("Error: TURSO_TOKEN not set")
        return

    # Get database-specific token
    db_name = "concert-singer"

    print(f"Creating token for {db_name}...")
    token_url = f"https://api.turso.tech/v1/organizations/{org}/databases/{db_name}/auth/tokens"
    headers = {
        "Authorization": f"Bearer {account_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(token_url, headers=headers, json={}, timeout=30)
    if response.status_code not in [200, 201]:
        print(f"Failed to create token: {response.status_code}")
        print(response.text)
        return

    db_token = response.json().get("jwt")
    print(f"✓ Got database token\n")

    # Test queries
    db_url = f"https://{db_name}-{org}.turso.io"

    queries = [
        "SELECT 1",
        "SELECT name FROM sqlite_master WHERE type='table'",
        "SELECT * FROM singer LIMIT 1"
    ]

    for sql in queries:
        print(f"=== Query: {sql} ===")

        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql
                    }
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {db_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{db_url}/v2/pipeline",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Status: {response.status_code}")
        print(f"Raw response:")
        print(json.dumps(response.json(), indent=2))
        print()

if __name__ == "__main__":
    main()
