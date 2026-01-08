#!/usr/bin/env python3
"""
Notion CRUD Endpoints Test Script
Tests all 4 Notion API endpoints with connected workspace
"""

import os
import jwt
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# User details (user who connected Notion workspace)
USER_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"
USER_EMAIL = "opnureyes2@gmail.com"

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
BASE_URL = "http://localhost:7777"

def generate_test_token():
    """Generate a test JWT token for the user"""
    payload = {
        "user_id": USER_ID,
        "email": USER_EMAIL,
        "exp": int(time.time()) + 3600  # 1 hour expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def test_get_companies(token):
    """Test GET /api/notion/companies endpoint"""
    print("\n1. Testing GET /api/notion/companies...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/notion/companies",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ PASS - Companies endpoint working")
            print(f"   Workspace: {data.get('workspace')}")
            print(f"   Count: {data.get('count')}")
            if data.get('count') > 0:
                print(f"   Sample: {data.get('companies', [])[0]}")
            return True
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False

def test_get_projects(token):
    """Test GET /api/notion/projects endpoint"""
    print("\n2. Testing GET /api/notion/projects...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/notion/projects",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ PASS - Projects endpoint working")
            print(f"   Workspace: {data.get('workspace')}")
            print(f"   Count: {data.get('count')}")
            if data.get('count') > 0:
                print(f"   Sample: {data.get('projects', [])[0]}")
            return True
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False

def test_get_tasks(token):
    """Test GET /api/notion/tasks endpoint"""
    print("\n3. Testing GET /api/notion/tasks...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/notion/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ PASS - Tasks endpoint working")
            print(f"   Workspace: {data.get('workspace')}")
            print(f"   Count: {data.get('count')}")
            if data.get('count') > 0:
                print(f"   Sample: {data.get('tasks', [])[0]}")
            return True
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False

def test_create_task(token):
    """Test POST /api/notion/tasks endpoint"""
    print("\n4. Testing POST /api/notion/tasks...")

    try:
        task_data = {
            "name": f"Test Task from API - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            # Note: Status and description omitted for simple test
            # Valid status values: "Not started", "Done"
        }

        response = requests.post(
            f"{BASE_URL}/api/notion/tasks",
            headers={"Authorization": f"Bearer {token}"},
            json=task_data
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ PASS - Task created successfully")
            print(f"   Task ID: {data.get('task', {}).get('id')}")
            print(f"   Task Name: {data.get('task', {}).get('name')}")
            print(f"   Workspace: {data.get('task', {}).get('workspace')}")
            return True
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False

def main():
    print("=" * 80)
    print("NOTION CRUD ENDPOINTS TEST")
    print("=" * 80)
    print()

    # Generate JWT token
    print("Generating JWT token...")
    token = generate_test_token()
    print(f"User: {USER_EMAIL}")
    print(f"User ID: {USER_ID}")
    print()

    # Run tests
    results = []

    results.append(test_get_companies(token))
    results.append(test_get_projects(token))
    results.append(test_get_tasks(token))
    results.append(test_create_task(token))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! Notion CRUD endpoints are working correctly!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
