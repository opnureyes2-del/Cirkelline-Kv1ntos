"""
Initialize knowledge base and upload test documents.
This creates the necessary database tables and uploads both Ivo and Rasmus documents.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def initialize_and_upload():
    print("\n" + "="*60)
    print("🚀 INITIALIZING KNOWLEDGE BASE")
    print("="*60 + "\n")

    from my_os import knowledge, create_private_document_metadata, db
    from sqlalchemy import text, create_engine
    from sqlalchemy.orm import Session

    # Step 1: Create database tables
    print("📦 Step 1: Creating knowledge base tables...")
    try:
        await knowledge.create_async()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"⚠️  Table creation warning: {e}")
        print("   (This may be normal if tables already exist)")

    # Step 2: Upload Ivo's document
    print("\n📄 Step 2: Uploading Ivo's private document...")

    ivo_user_id = "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e"

    test_file_ivo = "/tmp/ivo_notes.txt"
    with open(test_file_ivo, "w") as f:
        f.write("Ivo's private notes about project strategy and AI development.\n")
        f.write("Key focus areas:\n")
        f.write("- Gemini 2.5 Flash integration\n")
        f.write("- Multi-agent system architecture\n")
        f.write("- Knowledge base implementation with pgvector\n")
        f.write("- JWT authentication and user isolation\n")

    metadata_ivo = create_private_document_metadata(
        user_id=ivo_user_id,
        user_type="Admin"
    )

    await knowledge.add_content_async(
        name="ivo_notes.txt",
        path=test_file_ivo,
        metadata=metadata_ivo,
        description="Ivo's private notes on AI strategy"
    )

    print("✅ Ivo's document uploaded")
    print(f"   user_id: {ivo_user_id}")
    print(f"   access_level: {metadata_ivo['access_level']}")

    # Step 3: Upload Rasmus's document
    print("\n📄 Step 3: Uploading Rasmus's private document...")

    # Get Rasmus user_id from database
    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        result = session.execute(
            text("SELECT id FROM users WHERE email = 'opnureyes2@gmail.com'")
        )
        rasmus_row = result.fetchone()

    if not rasmus_row:
        print("❌ Could not find Rasmus user_id in database!")
        print("   Make sure Rasmus is registered")
        return

    rasmus_user_id = str(rasmus_row[0])
    print(f"   Found Rasmus user_id: {rasmus_user_id}")

    test_file_rasmus = "/tmp/rasmus_notes.txt"
    with open(test_file_rasmus, "w") as f:
        f.write("Rasmus's private notes about business operations and strategy.\n")
        f.write("Key focus areas:\n")
        f.write("- Go-to-market strategy and positioning\n")
        f.write("- Partnership development and alliances\n")
        f.write("- Revenue planning and financial modeling\n")
        f.write("- Customer acquisition and retention\n")

    metadata_rasmus = create_private_document_metadata(
        user_id=rasmus_user_id,
        user_type="Admin"
    )

    await knowledge.add_content_async(
        name="rasmus_notes.txt",
        path=test_file_rasmus,
        metadata=metadata_rasmus,
        description="Rasmus's private notes on business strategy"
    )

    print("✅ Rasmus's document uploaded")
    print(f"   user_id: {rasmus_user_id}")
    print(f"   access_level: {metadata_rasmus['access_level']}")

    # Step 4: Verify uploads
    print("\n🔍 Step 4: Verifying uploads...")

    # Check contents table
    with Session(engine) as session:
        # Find contents table
        tables_result = session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE '%content%'
        """))

        for row in tables_result:
            table_name = row[0]
            print(f"\n   Checking table: {table_name}")

            # Count total documents
            count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"   Total documents: {count}")

            # Check for Ivo's document
            ivo_check = session.execute(text(f"""
                SELECT name FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": ivo_user_id})
            ivo_docs = [r[0] for r in ivo_check]

            if ivo_docs:
                print(f"   ✅ Ivo's documents: {', '.join(ivo_docs)}")
            else:
                print(f"   ❌ Ivo's documents: NOT FOUND")

            # Check for Rasmus's document
            rasmus_check = session.execute(text(f"""
                SELECT name FROM {table_name}
                WHERE metadata->>'user_id' = :user_id
            """), {"user_id": rasmus_user_id})
            rasmus_docs = [r[0] for r in rasmus_check]

            if rasmus_docs:
                print(f"   ✅ Rasmus's documents: {', '.join(rasmus_docs)}")
            else:
                print(f"   ❌ Rasmus's documents: NOT FOUND")

    print("\n" + "="*60)
    print("✅ INITIALIZATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart backend: python my_os.py")
    print("2. Start frontend: cd cirkelline-ui && npm run dev")
    print("3. Test as Ivo: Login → Ask 'What are my notes?'")
    print("4. Test as Rasmus: Login → Ask 'What are my notes?'")
    print("\n")

if __name__ == "__main__":
    asyncio.run(initialize_and_upload())
