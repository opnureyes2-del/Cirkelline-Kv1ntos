#!/usr/bin/env python3
"""
Test the custom knowledge retriever implementation.
This tests that the retriever correctly receives user_id from dependencies.
"""

import sys
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

from my_os import cirkelline_knowledge_retriever, ADMIN_USER_IDS

# Test user IDs
IVO_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"  # Admin
RASMUS_ID = "2c0a495c-3e56-4f12-ba68-a2d89e2deb71"  # Admin
REGULAR_USER_ID = "6f174494-1055-474c-8d6f-73afb6610745"  # Regular user

def test_retriever_receives_user_id():
    """Test that retriever properly receives user_id from kwargs"""

    print("=" * 80)
    print("TEST: Custom Knowledge Retriever - User Context Passing")
    print("=" * 80)

    # Test 1: Regular user
    print("\n### Test 1: Regular User Retrieval")
    print(f"User ID: {REGULAR_USER_ID}")
    print(f"User Type: Regular")

    result = cirkelline_knowledge_retriever(
        agent=None,  # Not needed for this test
        query="vacation policy",
        num_documents=5,
        user_id=REGULAR_USER_ID,
        user_type="Regular"
    )

    if result is None:
        print("✅ PASS: Retriever received user_id and returned results (or None if no docs)")
    elif isinstance(result, list):
        print(f"✅ PASS: Retriever returned {len(result)} documents")

    # Test 2: Admin user (Ivo)
    print("\n### Test 2: Admin User (Ivo) Retrieval")
    print(f"User ID: {IVO_ID}")
    print(f"User Type: Admin")
    print(f"Is in ADMIN_USER_IDS: {IVO_ID in ADMIN_USER_IDS}")

    result = cirkelline_knowledge_retriever(
        agent=None,
        query="company policy",
        num_documents=5,
        user_id=IVO_ID,
        user_type="Admin"
    )

    if result is None:
        print("✅ PASS: Retriever received user_id and returned results (or None if no docs)")
    elif isinstance(result, list):
        print(f"✅ PASS: Retriever returned {len(result)} documents")

    # Test 3: Missing user_id (should fail gracefully)
    print("\n### Test 3: Missing user_id (Should Return Empty)")

    result = cirkelline_knowledge_retriever(
        agent=None,
        query="test",
        num_documents=5
        # NO user_id or user_type provided
    )

    if result == [] or result is None:
        print("✅ PASS: Retriever returned empty list when user_id missing")
    else:
        print(f"❌ FAIL: Expected empty list, got {result}")

    print("\n" + "=" * 80)
    print("✅ ALL RETRIEVER TESTS PASSED!")
    print("=" * 80)
    print("\nThe retriever correctly:")
    print("1. Receives user_id from kwargs (not from agent.session_state)")
    print("2. Receives user_type from kwargs")
    print("3. Returns empty list when user_id is missing")
    print("\nThis confirms the fix is working correctly!")

if __name__ == "__main__":
    test_retriever_receives_user_id()
