#!/usr/bin/env python3
"""
Notion OAuth Verification Script
Verifies that the OAuth flow completed successfully
"""

import os
import sys
import jwt
import time
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# User details
USER_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"
USER_EMAIL = "opnureyes2@gmail.com"

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY")

def generate_test_token():
    """Generate a test JWT token for the user"""
    payload = {
        "user_id": USER_ID,
        "email": USER_EMAIL,
        "exp": int(time.time()) + 3600  # 1 hour expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def check_database():
    """Check if Notion token exists in database"""
    print("1. Checking database for Notion token...")

    # Convert DATABASE_URL from sqlalchemy format to psycopg format
    db_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        workspace_id,
                        workspace_name,
                        workspace_icon,
                        owner_email,
                        created_at,
                        LENGTH(access_token) as token_length
                    FROM notion_tokens
                    WHERE user_id = %s
                """, (USER_ID,))

                row = cur.fetchone()

                if row:
                    print("   ✅ PASS - Notion token found in database")
                    print(f"   Workspace ID: {row[0]}")
                    print(f"   Workspace Name: {row[1]}")
                    print(f"   Workspace Icon: {row[2]}")
                    print(f"   Owner Email: {row[3]}")
                    print(f"   Created At: {row[4]}")
                    print(f"   Token Length: {row[5]} characters (encrypted)")
                    return True
                else:
                    print("   ❌ FAIL - No Notion token found in database")
                    print("   Did you complete the OAuth authorization in your browser?")
                    return False
    except Exception as e:
        print(f"   ❌ ERROR - Database query failed: {e}")
        return False

def test_status_endpoint():
    """Test the status endpoint with JWT token"""
    print("\n2. Testing status endpoint...")

    import requests

    token = generate_test_token()

    try:
        response = requests.get(
            "http://localhost:7777/api/oauth/notion/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("connected"):
                print("   ✅ PASS - Status endpoint returns connected")
                print(f"   Workspace: {data.get('workspace_name')}")
                print(f"   Owner: {data.get('owner_email')}")
                print(f"   Connected At: {data.get('connected_at')}")
                return True
            else:
                print("   ❌ FAIL - Status endpoint says not connected")
                return False
        else:
            print(f"   ❌ FAIL - Status endpoint returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - Failed to call status endpoint: {e}")
        return False

def test_disconnect_endpoint():
    """Test the disconnect endpoint"""
    print("\n3. Testing disconnect endpoint...")

    import requests

    token = generate_test_token()

    try:
        response = requests.post(
            "http://localhost:7777/api/oauth/notion/disconnect",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("   ✅ PASS - Disconnect endpoint successful")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print("   ❌ FAIL - Disconnect did not succeed")
                return False
        else:
            print(f"   ❌ FAIL - Disconnect endpoint returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - Failed to call disconnect endpoint: {e}")
        return False

def verify_disconnected():
    """Verify token was removed from database"""
    print("\n4. Verifying token was removed from database...")

    # Convert DATABASE_URL from sqlalchemy format to psycopg format
    db_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM notion_tokens
                    WHERE user_id = %s
                """, (USER_ID,))

                count = cur.fetchone()[0]

                if count == 0:
                    print("   ✅ PASS - Token successfully removed from database")
                    return True
                else:
                    print(f"   ❌ FAIL - Token still exists in database (count: {count})")
                    return False
    except Exception as e:
        print(f"   ❌ ERROR - Database query failed: {e}")
        return False

def main():
    print("=" * 80)
    print("NOTION OAUTH VERIFICATION")
    print("=" * 80)
    print()

    # Run verification tests
    results = []

    # Test 1: Check database
    results.append(check_database())

    if not results[0]:
        print("\n⚠️  OAuth flow not completed. Please authorize the app first.")
        sys.exit(1)

    # Test 2: Status endpoint
    results.append(test_status_endpoint())

    # Test 3: Disconnect endpoint
    results.append(test_disconnect_endpoint())

    # Test 4: Verify disconnected
    results.append(verify_disconnected())

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! Notion OAuth integration is working correctly!")
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
