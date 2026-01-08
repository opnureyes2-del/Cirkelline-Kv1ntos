#!/usr/bin/env python3
"""
Debug script to see what Notion API actually returns
"""

import os
import jwt
import time
import json
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

# User details
USER_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

def get_notion_token():
    """Get Notion access token from database"""
    import psycopg
    from utils.encryption import decrypt_token

    db_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT access_token
                FROM notion_tokens
                WHERE user_id = %s
            """, (USER_ID,))

            row = cur.fetchone()
            if row:
                return decrypt_token(row[0])
    return None

def main():
    print("=" * 80)
    print("NOTION API DEBUG - What does search() actually return?")
    print("=" * 80)
    print()

    # Get access token
    print("1. Getting Notion access token from database...")
    access_token = get_notion_token()
    if not access_token:
        print("   ❌ No Notion token found!")
        return
    print(f"   ✅ Token found (length: {len(access_token)})")
    print()

    # Initialize Notion client
    print("2. Initializing Notion client...")
    notion = Client(auth=access_token)
    print("   ✅ Client initialized")
    print()

    # Search for all objects
    print("3. Calling notion.search() with no filter...")
    response = notion.search()
    print(f"   ✅ Search completed")
    print()

    # Show raw response structure
    print("4. Raw response structure:")
    print(f"   Keys: {list(response.keys())}")
    print(f"   Total results: {len(response.get('results', []))}")
    print()

    # Analyze each result
    print("5. Analyzing each result:")
    print()

    results = response.get("results", [])

    # Count by object type
    object_types = {}
    for item in results:
        obj_type = item.get("object")
        object_types[obj_type] = object_types.get(obj_type, 0) + 1

    print(f"   Object type breakdown:")
    for obj_type, count in object_types.items():
        print(f"   - {obj_type}: {count}")
    print()

    # Show first few databases in detail
    databases = [item for item in results if item.get("object") == "database"]

    print(f"6. Found {len(databases)} database(s)")
    print()

    if databases:
        print("7. First database structure (showing first 3):")
        for i, db in enumerate(databases[:3]):
            print(f"\n   === Database {i+1} ===")
            print(f"   ID: {db.get('id')}")
            print(f"   Object: {db.get('object')}")
            print(f"   Keys available: {list(db.keys())}")

            # Check title structure
            if 'title' in db:
                print(f"   Title type: {type(db['title'])}")
                print(f"   Title value: {db['title']}")

            # Check if there's a different field for the name
            for key in ['title', 'name', 'properties']:
                if key in db:
                    print(f"   {key}: {db[key]}")
    else:
        print("   ⚠️  NO DATABASES FOUND!")
        print()
        print("   First 3 results of ANY type:")
        for i, item in enumerate(results[:3]):
            print(f"\n   === Result {i+1} ===")
            print(f"   Object type: {item.get('object')}")
            print(f"   Keys: {list(item.keys())}")
            print(f"   Raw: {json.dumps(item, indent=2)[:500]}...")

if __name__ == "__main__":
    main()
