"""
Pure investigation: Find out WHY Rasmus can't find his notes
"""
import asyncio
from my_os import db, knowledge, get_private_knowledge_filters
from sqlalchemy import text
import json

print("\n" + "="*60)
print("INVESTIGATION: Why Rasmus Can't Find His Notes")
print("="*60 + "\n")

# User IDs
ivo_user_id = "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e"
rasmus_user_id = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"

print("👥 USER IDS:")
print(f"   Ivo:    {ivo_user_id}")
print(f"   Rasmus: {rasmus_user_id}")

# Check 1: What's in the database?
print("\n" + "-"*60)
print("CHECK 1: What documents exist in database?")
print("-"*60)

with db.db_engine.connect() as conn:
    # Find knowledge tables
    tables = conn.execute(text("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND (tablename LIKE '%knowledge%' OR tablename LIKE '%content%')
    """))

    table_list = [row[0] for row in tables]
    print(f"\nKnowledge tables: {table_list}")

    for table_name in table_list:
        print(f"\n📋 Table: {table_name}")
        try:
            result = conn.execute(text(f"""
                SELECT name, metadata
                FROM {table_name}
            """))

            rows = result.fetchall()
            if rows:
                print(f"   Found {len(rows)} documents:")
                for row in rows:
                    name = row[0]
                    metadata = row[1]
                    user_id = metadata.get('user_id') if metadata else None

                    owner = "❓ UNKNOWN"
                    if user_id == ivo_user_id:
                        owner = "✅ IVO"
                    elif user_id == rasmus_user_id:
                        owner = "✅ RASMUS"

                    print(f"\n   📄 {name}")
                    print(f"      Owner: {owner}")
                    print(f"      user_id: {user_id}")
                    print(f"      Full metadata: {json.dumps(metadata, indent=10)}")
            else:
                print("   ⚠️  TABLE IS EMPTY")
        except Exception as e:
            print(f"   ❌ Error: {e}")

# Check 2: What filters are being applied?
print("\n" + "-"*60)
print("CHECK 2: What filters are being applied?")
print("-"*60)

ivo_filters = get_private_knowledge_filters(ivo_user_id)
rasmus_filters = get_private_knowledge_filters(rasmus_user_id)

print(f"\nIvo's filters:    {ivo_filters}")
print(f"Rasmus's filters: {rasmus_filters}")

# Check 3: Manual database query with filters
print("\n" + "-"*60)
print("CHECK 3: Manual query simulation")
print("-"*60)

with db.db_engine.connect() as conn:
    for table_name in table_list:
        try:
            print(f"\n📋 Table: {table_name}")

            # Query for Ivo
            ivo_result = conn.execute(text(f"""
                SELECT name FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": ivo_user_id})
            ivo_docs = [row[0] for row in ivo_result]

            # Query for Rasmus
            rasmus_result = conn.execute(text(f"""
                SELECT name FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": rasmus_user_id})
            rasmus_docs = [row[0] for row in rasmus_result]

            print(f"   Ivo's documents:    {ivo_docs if ivo_docs else '❌ NONE'}")
            print(f"   Rasmus's documents: {rasmus_docs if rasmus_docs else '❌ NONE'}")

        except Exception as e:
            print(f"   Error: {e}")

# Check 4: Vector database
print("\n" + "-"*60)
print("CHECK 4: What's in vector database?")
print("-"*60)

try:
    from my_os import vector_db

    print("\nSearching vectors for 'Ivo notes'...")
    try:
        results = vector_db.search("Ivo notes", limit=3)
        print(f"   Found {len(results)} results")
    except Exception as e:
        print(f"   ❌ Search error: {e}")

    print("\nSearching vectors for 'Rasmus notes'...")
    try:
        results = vector_db.search("Rasmus notes", limit=3)
        print(f"   Found {len(results)} results")
    except Exception as e:
        print(f"   ❌ Search error: {e}")

except Exception as e:
    print(f"❌ Vector DB access error: {e}")

# Summary
print("\n" + "="*60)
print("INVESTIGATION SUMMARY")
print("="*60)

print("\nANSWER THESE:")
print("1. Does Rasmus's document exist in database? _____")
print("2. Does it have correct user_id in metadata? _____")
print("3. Does manual SQL query find it for Rasmus? _____")
print("4. Are vectors embedded for Rasmus's document? _____")
print("5. What is the ACTUAL problem? _____")

print("\n")
