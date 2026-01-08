#!/usr/bin/env python3
"""
Quick script to inspect actual property names in Tasks database
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
    print("INSPECTING TASKS DATABASE PROPERTIES")
    print("=" * 80)
    print()

    # Get access token
    access_token = get_notion_token()
    if not access_token:
        print("   ❌ No Notion token found!")
        return

    # Initialize Notion client
    notion = Client(auth=access_token)

    # Search for data sources
    response = notion.search()
    databases = [item for item in response.get("results", []) if item.get("object") == "data_source"]

    # Find Tasks database
    tasks_db = None
    for db in databases:
        title = db.get("title", [])
        if title and "task" in title[0].get("text", {}).get("content", "").lower():
            tasks_db = db
            break

    if not tasks_db:
        print("   ❌ No Tasks database found!")
        return

    print(f"✅ Found Tasks database: {tasks_db.get('id')}")
    print()

    # Query for tasks
    db_results = notion.data_sources.query(data_source_id=tasks_db["id"])

    if db_results.get("results"):
        # Get first task
        first_task = db_results["results"][0]
        props = first_task.get("properties", {})

        print("Available properties in Tasks database:")
        print()
        for prop_name in props.keys():
            prop_type = props[prop_name].get("type")
            print(f"   - '{prop_name}' (type: {prop_type})")

        print()
        print("=" * 80)
        print("Use these EXACT property names in your code!")
        print("=" * 80)
    else:
        print("   ⚠️  No tasks found in database")

if __name__ == "__main__":
    main()
