#!/usr/bin/env python3
"""
Setup test documents for knowledge retriever testing using Agno Knowledge API.
Creates documents with different access levels and owners.
"""

import sys
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

import os
from dotenv import load_dotenv
load_dotenv()

from my_os import knowledge, ADMIN_USER_IDS
from datetime import datetime

# Test user IDs
IVO_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"  # Admin
RASMUS_ID = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"  # Admin
REGULAR_USER_ID = "6f174494-1055-474c-8d6f-73afb6610745"  # Regular user

# Test documents (using file paths)
test_docs = [
    {
        "name": "ivo_private.txt",
        "path": "ivo_private.txt",
        "user_id": IVO_ID,
        "access_level": "private",
        "description": "Ivo's private contract"
    },
    {
        "name": "rasmus_private.txt",
        "path": "rasmus_private.txt",
        "user_id": RASMUS_ID,
        "access_level": "private",
        "description": "Rasmus's private notes"
    },
    {
        "name": "regular_user_private.txt",
        "path": "regular_user_private.txt",
        "user_id": REGULAR_USER_ID,
        "access_level": "private",
        "description": "Regular user's vacation plans"
    },
    {
        "name": "company_policy.txt",
        "path": "company_policy.txt",
        "user_id": IVO_ID,
        "access_level": "admin-shared",
        "shared_by_name": "Ivo",
        "description": "Admin-shared company policy"
    }
]

def main():
    print("=" * 80)
    print("SETTING UP TEST DOCUMENTS FOR KNOWLEDGE RETRIEVER TESTING")
    print("=" * 80)

    try:
        # Insert test documents using Knowledge API
        print("\nInserting test documents...")
        for doc in test_docs:
            # Build metadata
            metadata = {
                "user_id": doc["user_id"],
                "user_type": "Admin" if doc["user_id"] in ADMIN_USER_IDS else "Regular",
                "access_level": doc["access_level"],
                "uploaded_by": doc["user_id"],
                "uploaded_at": datetime.now().isoformat(),
                "uploaded_via": "test_script"
            }

            if doc.get("shared_by_name"):
                metadata["shared_by_name"] = doc["shared_by_name"]

            # Add to knowledge base
            knowledge.add_content(
                name=doc["name"],
                path=doc["path"],
                metadata=metadata,
                description=doc["description"]
            )

            print(f"✅ Inserted: {doc['name']} (owner: {doc['user_id'][:8]}..., access: {doc['access_level']})")

        # Load into vector database
        print("\nLoading into vector database...")
        knowledge.load(recreate=False, upsert=True)

        print("\n" + "=" * 80)
        print("✅ TEST DOCUMENTS SETUP COMPLETE!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
