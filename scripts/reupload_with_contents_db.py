"""
Re-upload documents now that contents DB exists
"""
import asyncio
import os
from my_os import knowledge, create_private_document_metadata

async def reupload_documents():
    print("\n📤 RE-UPLOADING DOCUMENTS WITH CONTENTS DB\n")

    # Ivo's document
    print("Uploading Ivo's notes...")
    ivo_file = "/tmp/ivo_notes_proper.txt"
    with open(ivo_file, "w") as f:
        f.write("Ivo's private notes about AI strategy and Cirkelline development.")

    await knowledge.add_content_async(
        name="ivo_notes.txt",
        path=ivo_file,
        metadata=create_private_document_metadata(
            user_id="cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e",
            user_type="admin"
        )
    )
    print("✅ Ivo's document uploaded")

    # Rasmus's document
    print("\nUploading Rasmus's notes...")
    rasmus_file = "/tmp/rasmus_notes_proper.txt"
    with open(rasmus_file, "w") as f:
        f.write("Rasmus's private notes about business operations and strategy.")

    await knowledge.add_content_async(
        name="rasmus_notes.txt",
        path=rasmus_file,
        metadata=create_private_document_metadata(
            user_id="2c0a495c-3e56-4f12-ba68-a2d89e2deb71",
            user_type="admin"
        )
    )
    print("✅ Rasmus's document uploaded")

    # Verify in contents DB
    print("\n🔍 Verifying in contents DB...")
    from my_os import db
    from sqlalchemy import text

    with db.db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name, metadata->>'user_id' as user_id
            FROM knowledge_contents
        """))

        for row in result:
            print(f"  📄 {row[0]} - user_id: {row[1]}")

    print("\n✅ RE-UPLOAD COMPLETE")

if __name__ == "__main__":
    asyncio.run(reupload_documents())
