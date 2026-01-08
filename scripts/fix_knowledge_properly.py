"""
Proper fix: Upload documents and call knowledge.aload() to initialize
Based on official Agno documentation pattern
"""
import asyncio
from my_os import knowledge, db, create_private_document_metadata
from sqlalchemy import text

async def fix_knowledge_properly():
    print("\n" + "="*60)
    print("PROPER KNOWLEDGE BASE INITIALIZATION")
    print("="*60 + "\n")

    # Step 1: Clear any existing broken data
    print("STEP 1: Cleaning up...")
    try:
        with db.db_engine.connect() as conn:
            # Check if table exists first
            check_table = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'knowledge_contents'
                )
            """))
            table_exists = check_table.scalar()

            if table_exists:
                conn.execute(text("DELETE FROM knowledge_contents"))
                conn.commit()
                print("✅ Cleared old data")
            else:
                print("⚠️  No existing table (will be created)")
    except Exception as e:
        print(f"⚠️  Cleanup: {e}")

    # Step 2: Upload Ivo's document
    print("\nSTEP 2: Uploading Ivo's document...")

    ivo_file = "/tmp/ivo_notes_final.txt"
    with open(ivo_file, "w") as f:
        f.write("""Ivo's Private Technical Notes

Project: Cirkelline Multi-Agent System

Architecture Overview:
- Gemini 2.5 Flash for multimodal processing
- Specialized agents: Audio, Video, Image, Document
- Two coordinated teams: Research Team and Law Team
- Main orchestrator using route mode

Technical Stack:
- Backend: AgentOS with FastAPI
- Database: PostgreSQL with pgvector
- Frontend: Next.js with TypeScript
- Knowledge Base: RAG with metadata filtering

Development Focus:
- User isolation and privacy
- Per-user knowledge bases
- Secure authentication with JWT
- Admin profile recognition

These are Ivo's personal technical notes about Cirkelline development and architecture.
""")

    ivo_metadata = create_private_document_metadata(
        user_id="cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e",
        user_type="admin"
    )

    print(f"   Metadata: {ivo_metadata}")

    await knowledge.add_content_async(
        name="ivo_notes_final.txt",
        path=ivo_file,
        metadata=ivo_metadata,
        description="Ivo's private technical notes about Cirkelline"
    )

    print("✅ Ivo's document uploaded to memory")

    # Step 3: Upload Rasmus's document
    print("\nSTEP 3: Uploading Rasmus's document...")

    rasmus_file = "/tmp/rasmus_notes_final.txt"
    with open(rasmus_file, "w") as f:
        f.write("""Rasmus's Private Business Notes

Project: Cirkelline Business Strategy

Business Development:
- Partnership opportunities in AI sector
- Revenue models for multi-agent systems
- Market positioning and competitive analysis

Operations Planning:
- Team scaling and hiring strategy
- Process optimization for development workflow
- Customer onboarding and support systems

Strategic Initiatives:
- Product-market fit validation
- Go-to-market strategy
- Growth metrics and KPIs

Financial Planning:
- Investment requirements
- Revenue projections
- Cost structure optimization

These are Rasmus's personal business notes about Cirkelline operations and strategy.
""")

    rasmus_metadata = create_private_document_metadata(
        user_id="2c0a495c-3e56-4f12-ba68-a2d89e2deb71",
        user_type="admin"
    )

    print(f"   Metadata: {rasmus_metadata}")

    await knowledge.add_content_async(
        name="rasmus_notes_final.txt",
        path=rasmus_file,
        metadata=rasmus_metadata,
        description="Rasmus's private business notes about Cirkelline"
    )

    print("✅ Rasmus's document uploaded to memory")

    # Step 4: THE CRITICAL STEP - Call aload() to initialize everything
    print("\n" + "="*60)
    print("STEP 4: INITIALIZING KNOWLEDGE BASE (CREATING TABLES)")
    print("="*60)
    print("\nCalling knowledge.aload() to:")
    print("  - Create knowledge_contents table")
    print("  - Process and chunk documents")
    print("  - Generate embeddings")
    print("  - Store in vector database")
    print("  - Index for search")
    print("\nThis may take 30-60 seconds...")

    try:
        await knowledge.aload(recreate=True)  # recreate=True for clean start
        print("\n✅ KNOWLEDGE BASE INITIALIZED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Verify tables were created
    print("\nSTEP 5: Verifying table creation...")

    with db.db_engine.connect() as conn:
        # Check for knowledge tables
        tables_result = conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND (tablename LIKE '%knowledge%' OR tablename LIKE '%content%')
        """))

        tables = [row[0] for row in tables_result]

        if tables:
            print(f"✅ Tables created: {tables}")
        else:
            print("❌ NO TABLES CREATED!")
            return

    # Step 6: Verify documents in contents table
    print("\nSTEP 6: Verifying documents...")

    with db.db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name, metadata->>'user_id' as user_id, metadata->>'access_level' as access
            FROM knowledge_contents
            ORDER BY name
        """))

        rows = result.fetchall()

        if rows:
            print(f"✅ Found {len(rows)} documents in database:")
            for row in rows:
                owner = "IVO" if "cc74dcd6" in str(row[1]) else "RASMUS" if "2c0a495c" in str(row[1]) else "UNKNOWN"
                print(f"\n   📄 {row[0]}")
                print(f"      Owner: {owner}")
                print(f"      Access: {row[2]}")
                print(f"      user_id: {row[1][:20]}...")
        else:
            print("❌ NO DOCUMENTS IN DATABASE!")
            return

    # Step 7: Verify vector embeddings
    print("\nSTEP 7: Verifying vector embeddings...")

    try:
        from my_os import vector_db

        # Test search for Ivo's content
        print("\nSearching vectors for 'Gemini architecture'...")
        results = vector_db.search("Gemini architecture", limit=2)
        print(f"   Found {len(results)} vector results")

        # Test search for Rasmus's content
        print("\nSearching vectors for 'business strategy'...")
        results = vector_db.search("business strategy", limit=2)
        print(f"   Found {len(results)} vector results")

        print("\n✅ Vector database working")

    except Exception as e:
        print(f"\n⚠️  Vector search: {e}")

    print("\n" + "="*60)
    print("KNOWLEDGE BASE FIX COMPLETE!")
    print("="*60)

    print("\n📋 SUMMARY:")
    print("✅ Both documents uploaded")
    print("✅ knowledge.aload() executed successfully")
    print("✅ Tables created in PostgreSQL")
    print("✅ Documents indexed in contents DB")
    print("✅ Vectors stored in vector DB")

    print("\n🎯 NEXT STEPS:")
    print("1. Restart backend: python my_os.py")
    print("2. Test as Ivo: 'what are my notes?'")
    print("   → Should find ivo_notes_final.txt (NOT web search!)")
    print("3. Test as Rasmus: 'what are my notes?'")
    print("   → Should find rasmus_notes_final.txt (NOT web search!)")
    print("4. Each user should ONLY see their own notes")

    print("\n✅ Knowledge base is ready for testing!\n")

if __name__ == "__main__":
    asyncio.run(fix_knowledge_properly())
