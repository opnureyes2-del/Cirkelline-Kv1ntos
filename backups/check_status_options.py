#!/usr/bin/env python3
"""
Script to inspect available status options in Tasks database
"""

import os
import jwt
import json
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

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
    print("CHECKING AVAILABLE STATUS OPTIONS")
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

    # Get database details (to see status options)
    db_id = tasks_db["id"]
    print(f"✅ Found Tasks database: {db_id}")
    print()

    # Retrieve database to see properties configuration
    try:
        db_info = notion.databases.retrieve(database_id=db_id)
        props = db_info.get("properties", {})

        if "Status" in props:
            status_prop = props["Status"]
            print(f"Status property type: {status_prop.get('type')}")

            # For status type properties, check the available options
            if status_prop.get("type") == "status":
                status_config = status_prop.get("status", {})
                options = status_config.get("options", [])

                if options:
                    print(f"\n✅ Available status options ({len(options)}):")
                    for opt in options:
                        print(f"   - \"{opt.get('name')}\" (id: {opt.get('id')})")
                else:
                    print("\n⚠️  No status options found")
                    print(f"Full status config: {json.dumps(status_config, indent=2)}")
        else:
            print("⚠️  No 'Status' property found in database")
            print(f"Available properties: {list(props.keys())}")

    except Exception as e:
        print(f"❌ Error retrieving database: {e}")
        import traceback
        print(traceback.format_exc())

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
