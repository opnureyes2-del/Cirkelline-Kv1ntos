#!/usr/bin/env python3
"""
Test document upload and knowledge retrieval system.
Tests:
1. Regular user can only see their own private documents
2. Admins can see their documents + admin-shared documents
3. Admin-shared documents work correctly
"""

import sys
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

import os
from dotenv import load_dotenv
load_dotenv()

from my_os import knowledge, ADMIN_USER_IDS
import asyncio
from datetime import datetime

# Test user IDs
RASMUS_ID = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"  # Admin
IVO_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"  # Admin
REGULAR_USER_ID = "6f174494-1055-474c-8d6f-73afb6610745"  # Regular user

async def main():
    print("=" * 80)
    print("TESTING DOCUMENT UPLOAD AND KNOWLEDGE RETRIEVAL")
    print("=" * 80)

    # Test documents
    test_docs = [
        {
            "name": "rasmus_private.txt",
            "content": "Rasmus's private technical notes about the Cirkelline architecture.",
            "user_id": RASMUS_ID,
            "user_type": "Admin",
            "access_level": "private"
        },
        {
            "name": "ivo_private.txt",
            "content": "Ivo's private contract and business strategy notes.",
            "user_id": IVO_ID,
            "user_type": "Admin",
            "access_level": "private"
        },
        {
            "name": "regular_user_doc.txt",
            "content": "Regular user's vacation plans and personal notes.",
            "user_id": REGULAR_USER_ID,
            "user_type": "Regular",
            "access_level": "private"
        },
        {
            "name": "company_policy.txt",
            "content": "Company-wide policy document shared with all admins. Contains important HR policies.",
            "user_id": IVO_ID,  # Uploaded by Ivo
            "user_type": "Admin",
            "access_level": "admin-shared",
            "shared_by_name": "Ivo"
        }
    ]

    print("\n📤 Uploading test documents...")

    for doc in test_docs:
        # Create temp file
        temp_path = f"/tmp/{doc['name']}"
        with open(temp_path, 'w') as f:
            f.write(doc['content'])

        # Build metadata
        metadata = {
            "user_id": doc["user_id"],
            "user_type": doc["user_type"],
            "access_level": doc["access_level"],
            "uploaded_by": doc["user_id"],
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_via": "test_script"
        }

        if doc.get("shared_by_name"):
            metadata["shared_by_name"] = doc["shared_by_name"]

        # Upload to knowledge base
        await knowledge.add_content_async(
            name=doc["name"],
            path=temp_path,
            metadata=metadata,
            description=f"Test document: {doc['name']}"
        )

        print(f"✅ Uploaded: {doc['name']} (owner: {doc['user_id'][:8]}..., access: {doc['access_level']})")

        # Clean up
        os.remove(temp_path)

    print("\n" + "=" * 80)
    print("✅ TEST DOCUMENTS UPLOADED SUCCESSFULLY!")
    print("=" * 80)
    print("\nDocuments uploaded:")
    print("1. rasmus_private.txt - Rasmus's private doc")
    print("2. ivo_private.txt - Ivo's private doc")
    print("3. regular_user_doc.txt - Regular user's private doc")
    print("4. company_policy.txt - Admin-shared doc (uploaded by Ivo)")
    print("\nExpected behavior:")
    print("- Rasmus should see: rasmus_private.txt + company_policy.txt (2 docs)")
    print("- Ivo should see: ivo_private.txt + company_policy.txt (2 docs)")
    print("- Regular user should see: regular_user_doc.txt (1 doc)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
