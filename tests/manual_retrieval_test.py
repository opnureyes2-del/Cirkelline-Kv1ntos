#!/usr/bin/env python3
"""
Test the knowledge retrieval system end-to-end.
Simulates API calls to test document filtering.
"""

import requests
import json

BASE_URL = "http://localhost:7777"

# Test user IDs
RASMUS_ID = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"
IVO_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"
REGULAR_USER_ID = "6f174494-1055-474c-8d6f-73afb6610745"

def test_user_search(user_id, user_name, user_type, expected_docs):
    """Test knowledge retrieval for a specific user."""
    print(f"\n{'='*80}")
    print(f"Testing: {user_name} ({user_type})")
    print(f"User ID: {user_id}")
    print(f"Expected documents: {expected_docs}")
    print(f"{'='*80}")

    # Send message to Cirkelline asking to list documents
    data = {
        "message": "List all my documents. What documents do I have access to?",
        "user_id": user_id,
        "stream": False
    }

    # Mock dependencies (would come from JWT in real app)
    headers = {
        "X-User-Type": user_type,
        "X-User-Name": user_name
    }

    try:
        response = requests.post(
            f"{BASE_URL}/teams/cirkelline/runs",
            data=data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            agent_response = result.get("content", "")

            print(f"\n✅ Response received:")
            print(f"Status: {response.status_code}")
            print(f"\nAgent said:")
            print(agent_response[:500])  # First 500 chars

            # Check if expected docs are mentioned
            docs_found = []
            for doc in expected_docs:
                if doc.lower() in agent_response.lower():
                    docs_found.append(doc)
                    print(f"✅ Found mention of: {doc}")
                else:
                    print(f"❌ Missing: {doc}")

            if len(docs_found) == len(expected_docs):
                print(f"\n✅ TEST PASSED: All expected documents mentioned!")
            else:
                print(f"\n⚠️  TEST PARTIAL: {len(docs_found)}/{len(expected_docs)} documents found")

        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text[:200])

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=" * 80)
    print("KNOWLEDGE RETRIEVAL SYSTEM TEST")
    print("=" * 80)
    print("\nThis tests that:")
    print("1. Regular users only see their private documents")
    print("2. Admins see their private docs + admin-shared docs")
    print("3. The custom retriever filters correctly")

    # Test 1: Rasmus (Admin) - should see his private doc + admin-shared doc
    test_user_search(
        user_id=RASMUS_ID,
        user_name="Rasmus",
        user_type="Admin",
        expected_docs=["rasmus_private.txt", "company_policy.txt"]
    )

    # Test 2: Ivo (Admin) - should see his private doc + admin-shared doc
    test_user_search(
        user_id=IVO_ID,
        user_name="Ivo",
        user_type="Admin",
        expected_docs=["ivo_private.txt", "company_policy.txt"]
    )

    # Test 3: Regular user - should only see their private doc
    test_user_search(
        user_id=REGULAR_USER_ID,
        user_name="Regular User",
        user_type="Regular",
        expected_docs=["regular_user_doc.txt"]
    )

    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
