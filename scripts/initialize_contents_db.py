"""
Initialize Contents DB tables properly using Agno's methods
"""
import asyncio
from my_os import knowledge, db
from sqlalchemy import text

async def initialize_contents_db():
    print("\n🔧 INITIALIZING CONTENTS DB\n")

    # Method 1: Try knowledge.create()
    print("Method 1: Trying knowledge.create()...")
    try:
        await knowledge.create()
        print("✅ knowledge.create() succeeded")
    except AttributeError:
        print("❌ knowledge.create() doesn't exist")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Method 2: Try db.create()
    print("\nMethod 2: Trying db.create()...")
    try:
        db.create()
        print("✅ db.create() succeeded")
    except AttributeError:
        print("❌ db.create() doesn't exist")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Method 3: Try loading knowledge (sometimes creates tables)
    print("\nMethod 3: Trying knowledge.aload()...")
    try:
        await knowledge.aload()
        print("✅ knowledge.aload() succeeded")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Method 4: Check if tables were created
    print("\nMethod 4: Checking if tables exist now...")
    with db.db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND (tablename LIKE '%knowledge%' OR tablename LIKE '%content%')
        """))
        tables = [row[0] for row in result]

        if tables:
            print(f"✅ Tables created: {tables}")
        else:
            print("❌ Still no tables")

    # Method 5: Try contents_db directly
    print("\nMethod 5: Trying contents_db methods...")
    try:
        from agno.db.postgres import PostgresDb

        # Check available methods
        methods = [m for m in dir(knowledge.contents_db) if not m.startswith('_')]
        print(f"Available methods: {methods}")

        # Try create_tables if it exists
        if hasattr(knowledge.contents_db, 'create_tables'):
            knowledge.contents_db.create_tables()
            print("✅ create_tables() succeeded")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(initialize_contents_db())
