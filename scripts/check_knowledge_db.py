"""Debug script to check knowledge base contents"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from my_os import db, vector_db
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import json

print("\n🔍 INVESTIGATING KNOWLEDGE BASE\n")

# Get database connection
db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with Session(engine) as session:
    # List all tables
    tables_result = session.execute(text("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND (tablename LIKE '%knowledge%'
        OR tablename LIKE '%content%')
        ORDER BY tablename
    """))

    print("📋 Knowledge-related tables:")
    tables = []
    for row in tables_result:
        tables.append(row[0])
        print(f"  - {row[0]}")

    if not tables:
        print("❌ NO KNOWLEDGE TABLES FOUND!")
        print("   Knowledge base was never initialized!")
        exit(1)

    # Try each table to find contents
    for table_name in tables:
        try:
            print(f"\n{'='*60}")
            print(f"📄 Table: {table_name}")
            print('='*60)

            # Get column names
            cols_result = session.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in cols_result]
            print(f"Columns: {', '.join(columns)}")

            # Get row count
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            print(f"Total rows: {count}")

            if count > 0:
                # Get all rows
                result = session.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()

                for i, row in enumerate(rows, 1):
                    print(f"\n  Row {i}:")
                    row_dict = dict(zip(columns, row))
                    for key, value in row_dict.items():
                        if key == 'metadata' and value:
                            try:
                                print(f"    {key}:")
                                for mk, mv in value.items():
                                    print(f"      {mk}: {mv}")
                            except:
                                print(f"    {key}: {value}")
                        elif key in ['content', 'chunk'] and value and len(str(value)) > 100:
                            print(f"    {key}: {str(value)[:100]}... (truncated)")
                        else:
                            print(f"    {key}: {value}")
            else:
                print(f"  ⚠️  Table is EMPTY")

        except Exception as e:
            print(f"  ❌ Error reading table {table_name}: {e}")

    # Specifically check for our test documents
    print("\n\n" + "="*60)
    print("🎯 SEARCHING FOR TEST DOCUMENTS")
    print("="*60)

    for table_name in tables:
        try:
            result = session.execute(text(f"""
                SELECT name, metadata
                FROM {table_name}
                WHERE name LIKE '%notes%'
            """))

            rows = result.fetchall()
            if rows:
                print(f"\nIn table '{table_name}':")
                for row in rows:
                    print(f"\n  📄 Document: {row[0]}")
                    if row[1]:
                        print(f"     Metadata:")
                        for key, value in row[1].items():
                            print(f"       {key}: {value}")
        except Exception as e:
            # Table might not have these columns
            pass

print("\n" + "="*60)
print("🔍 CHECKING VECTOR DATABASE")
print("="*60)

try:
    # Check vector table
    with Session(engine) as session:
        # Get vector table name
        vec_tables = session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE '%vector%'
        """))

        for row in vec_tables:
            table_name = row[0]
            print(f"\n📊 Vector table: {table_name}")

            # Count vectors
            count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"   Total vectors: {count}")

            # Try to get some sample data
            if count > 0:
                result = session.execute(text(f"""
                    SELECT name, metadata
                    FROM {table_name}
                    LIMIT 10
                """))

                print(f"\n   Sample entries:")
                for r in result:
                    print(f"     - {r[0]}")
                    if r[1]:
                        print(f"       user_id: {r[1].get('user_id', 'N/A')}")
                        print(f"       access_level: {r[1].get('access_level', 'N/A')}")

except Exception as e:
    print(f"❌ Error checking vectors: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🔍 CHECKING FOR SPECIFIC USER DOCUMENTS")
print("="*60)

IVO_USER_ID = "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e"
RASMUS_USER_ID = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"

with Session(engine) as session:
    for table_name in tables:
        try:
            # Check for Ivo's documents
            ivo_result = session.execute(text(f"""
                SELECT name, metadata
                FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": IVO_USER_ID})

            ivo_docs = ivo_result.fetchall()
            if ivo_docs:
                print(f"\n✅ Ivo's documents in '{table_name}':")
                for doc in ivo_docs:
                    print(f"   - {doc[0]}")

            # Check for Rasmus's documents
            rasmus_result = session.execute(text(f"""
                SELECT name, metadata
                FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": RASMUS_USER_ID})

            rasmus_docs = rasmus_result.fetchall()
            if rasmus_docs:
                print(f"\n✅ Rasmus's documents in '{table_name}':")
                for doc in rasmus_docs:
                    print(f"   - {doc[0]}")
            elif 'ivo_docs' in locals() and ivo_docs:
                print(f"\n❌ Rasmus has NO documents in '{table_name}' (but Ivo does!)")

        except Exception as e:
            # Table might not support this query
            pass

print("\n" + "="*60)
print("✅ INVESTIGATION COMPLETE")
print("="*60 + "\n")
