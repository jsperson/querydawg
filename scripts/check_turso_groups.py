#!/usr/bin/env python3
"""
Check available Turso groups and create default if needed
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TURSO_TOKEN")
org = os.getenv("TURSO_ORG", "jsperson")

print("Checking Turso groups...")

# List groups
url = f"https://api.turso.tech/v1/organizations/{org}/groups"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    groups = data.get("groups", [])
    print(f"\nFound {len(groups)} groups:")
    for g in groups:
        print(f"  - {g.get('name', 'unknown')}")
