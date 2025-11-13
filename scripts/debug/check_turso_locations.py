#!/usr/bin/env python3
"""
Check available Turso locations
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TURSO_TOKEN")
org = os.getenv("TURSO_ORG", "jsperson")

print("Checking available Turso locations...")

url = "https://api.turso.tech/v1/locations"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    locations = data.get("locations", {})
    print(f"\nAvailable locations:")
    for code, name in locations.items():
        print(f"  {code}: {name}")
else:
    print(f"Error: {response.text}")
