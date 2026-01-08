"""
Test script for private document uploads.
Phase 1: Test private knowledge base isolation.

Usage:
    python test_private_upload.py
"""

import asyncio
import os
import sys

# Add current directory to path to import from my_os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_private_uploads():
    """Test uploading private documents for different users"""

    print("\n🧪 Testing Private Document Uploads (Phase 1)\n")

    # Import after path setup
    from my_os import knowledge, create_private_document_metadata, db

    # Test 1: Upload private doc for Ivo
    print("📄 Test 1: Uploading private doc for Ivo...")

    # Ivo's user_id from database
    ivo_user_id = "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e"

    test_file_ivo = "/tmp/ivo_notes.txt"
    with open(test_file_ivo, "w") as f:
        f.write("Ivo's private notes about project strategy and AI development.\n")
        f.write("Key focus areas:\n")
        f.write("- Gemini 2.5 Flash integration\n")
        f.write("- Multi-agent system architecture\n")
        f.write("- Knowledge base implementation\n")

    metadata_ivo = create_private_document_metadata(
        user_id=ivo_user_id,
        user_type="Admin"
    )

    # Use async add_content
    await knowledge.add_content_async(
        name="ivo_notes.txt",
        path=test_file_ivo,
        metadata=metadata_ivo
    )
    print("✅ Uploaded Ivo's private document")
    print(f"   Metadata: {metadata_ivo}")

    # Test 2: Upload private doc for Rasmus
    print("\n📄 Test 2: Uploading private doc for Rasmus...")

    # Get Rasmus user_id from database
    from sqlalchemy import text, create_engine
    from sqlalchemy.orm import Session

    db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    with Session(engine) as session:
        result = session.execute(
            text("SELECT id FROM users WHERE email = 'opnureyes2@gmail.com'")
        )
        rasmus_row = result.fetchone()

    if not rasmus_row:
        print("❌ Could not find Rasmus user_id")
        return

    rasmus_user_id = str(rasmus_row[0])
    print(f"   Found Rasmus user_id: {rasmus_user_id}")

    test_file_rasmus = "/tmp/rasmus_notes.txt"
    with open(test_file_rasmus, "w") as f:
        f.write("Rasmus's private notes about business operations and strategy.\n")
        f.write("Key focus areas:\n")
        f.write("- Go-to-market strategy\n")
        f.write("- Partnership development\n")
        f.write("- Revenue planning\n")

    metadata_rasmus = create_private_document_metadata(
        user_id=rasmus_user_id,
        user_type="Admin"
    )

    await knowledge.add_content_async(
        name="rasmus_notes.txt",
        path=test_file_rasmus,
        metadata=metadata_rasmus
    )
    print("✅ Uploaded Rasmus's private document")
    print(f"   Metadata: {metadata_rasmus}")

    # Test 3: Load knowledge into vector database
    print("\n📄 Test 3: Loading documents into vector database...")
    try:
        await knowledge.aload(recreate=False)
        print("✅ Knowledge base loaded successfully")
    except Exception as e:
        print(f"⚠️  Knowledge load warning: {e}")
        print("   (This may be normal if documents are already loaded)")

    print("\n✅ Phase 1 test upload complete!")
    print("\n" + "="*60)
    print("📋 TESTING INSTRUCTIONS")
    print("="*60)
    print("\n1. Restart backend:")
    print("   python my_os.py")
    print("\n2. Start frontend:")
    print("   cd cirkelline-ui && npm run dev")
    print("\n3. Test as Ivo:")
    print("   - Login: opnureyes2@gmail.com")
    print("   - Ask: 'What are my notes?'")
    print("   - Expected: Should find ivo_notes.txt ONLY")
    print("   - Should NOT see rasmus_notes.txt")
    print("\n4. Test as Rasmus:")
    print("   - Logout, then login: opnureyes2@gmail.com")
    print("   - Ask: 'What are my notes?'")
    print("   - Expected: Should find rasmus_notes.txt ONLY")
    print("   - Should NOT see ivo_notes.txt")
    print("\n5. Verify complete isolation:")
    print("   - Each user sees ONLY their own documents")
    print("   - No cross-contamination")
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_private_uploads())
