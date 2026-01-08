#!/usr/bin/env python3
"""
Test authentication endpoints for Cirkelline backend.
This script tests signup and login with both admin accounts.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:7777"
API_BASE = f"{BASE_URL}/api"

# Test data
IVO_EMAIL = "opnureyes2@gmail.com"
RASMUS_EMAIL = "opnureyes2@gmail.com"
TEST_PASSWORD = "TestPassword123!"

print("=" * 60)
print("CIRKELLINE AUTHENTICATION TESTS")
print("=" * 60)

# Test 1: Ivo Signup
print("\n[TEST 1] Ivo Signup")
print("-" * 60)
signup_data = {
    "email": IVO_EMAIL,
    "password": TEST_PASSWORD,
    "display_name": "Ivo (Test)"
}
try:
    response = requests.post(f"{API_BASE}/auth/signup", json=signup_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Signup successful!")
        print(f"   - Token: {data['token'][:50]}...")
        print(f"   - User: {data['user']['display_name']}")
        print(f"   - Admin: {data['user']['is_admin']}")
        ivo_token = data['token']
    else:
        print(f"❌ Signup failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Ivo Login
print("\n[TEST 2] Ivo Login")
print("-" * 60)
login_data = {
    "email": IVO_EMAIL,
    "password": TEST_PASSWORD
}
try:
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"   - Token: {data['token'][:50]}...")
        print(f"   - User: {data['user']['display_name']}")
        print(f"   - Admin: {data['user']['is_admin']}")

        # Decode JWT to verify admin fields
        import jwt
        decoded = jwt.decode(data['token'], options={"verify_signature": False})
        print(f"\n   JWT Payload:")
        print(f"   - user_name: {decoded.get('user_name')}")
        print(f"   - user_role: {decoded.get('user_role')}")
        print(f"   - user_type: {decoded.get('user_type')}")
        print(f"   - admin_name: {decoded.get('admin_name')}")
        print(f"   - admin_role: {decoded.get('admin_role')}")
        print(f"   - admin_context: {decoded.get('admin_context')}")
    else:
        print(f"❌ Login failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Rasmus Signup
print("\n[TEST 3] Rasmus Signup")
print("-" * 60)
signup_data = {
    "email": RASMUS_EMAIL,
    "password": TEST_PASSWORD,
    "display_name": "Rasmus (Test)"
}
try:
    response = requests.post(f"{API_BASE}/auth/signup", json=signup_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Signup successful!")
        print(f"   - Token: {data['token'][:50]}...")
        print(f"   - User: {data['user']['display_name']}")
        print(f"   - Admin: {data['user']['is_admin']}")
        rasmus_token = data['token']
    else:
        print(f"❌ Signup failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Rasmus Login
print("\n[TEST 4] Rasmus Login")
print("-" * 60)
login_data = {
    "email": RASMUS_EMAIL,
    "password": TEST_PASSWORD
}
try:
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"   - Token: {data['token'][:50]}...")
        print(f"   - User: {data['user']['display_name']}")
        print(f"   - Admin: {data['user']['is_admin']}")

        # Decode JWT to verify admin fields
        import jwt
        decoded = jwt.decode(data['token'], options={"verify_signature": False})
        print(f"\n   JWT Payload:")
        print(f"   - user_name: {decoded.get('user_name')}")
        print(f"   - user_role: {decoded.get('user_role')}")
        print(f"   - user_type: {decoded.get('user_type')}")
        print(f"   - admin_name: {decoded.get('admin_name')}")
        print(f"   - admin_role: {decoded.get('admin_role')}")
        print(f"   - admin_context: {decoded.get('admin_context')}")
    else:
        print(f"❌ Login failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Wrong password
print("\n[TEST 5] Wrong Password (Should Fail)")
print("-" * 60)
login_data = {
    "email": IVO_EMAIL,
    "password": "WrongPassword!"
}
try:
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print(f"✅ Correctly rejected wrong password")
        print(f"   - Error: {response.json()['detail']}")
    else:
        print(f"❌ Should have rejected wrong password!")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 6: Regular user signup
print("\n[TEST 6] Regular User Signup")
print("-" * 60)
signup_data = {
    "email": "testuser@example.com",
    "password": TEST_PASSWORD,
    "display_name": "Test User"
}
try:
    response = requests.post(f"{API_BASE}/auth/signup", json=signup_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Signup successful!")
        print(f"   - User: {data['user']['display_name']}")
        print(f"   - Admin: {data['user']['is_admin']}")

        # Decode JWT to verify regular user fields
        import jwt
        decoded = jwt.decode(data['token'], options={"verify_signature": False})
        print(f"\n   JWT Payload:")
        print(f"   - user_name: {decoded.get('user_name')}")
        print(f"   - user_role: {decoded.get('user_role')}")
        print(f"   - user_type: {decoded.get('user_type')}")
        print(f"   - is_admin: {decoded.get('is_admin')}")
    else:
        print(f"❌ Signup failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
