#!/usr/bin/env python3
"""
Notion OAuth Flow Test Script
Tests the complete OAuth flow for Notion integration
"""

import os
import jwt
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# User details
USER_ID = "ee461076-8cbb-4626-947b-956f293cf7bf"
USER_EMAIL = "opnureyes2@gmail.com"

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

def main():
    print("=" * 80)
    print("NOTION OAUTH FLOW TEST")
    print("=" * 80)
    print()

    # Generate JWT token
    print("1. Generating JWT token for test user...")
    token = generate_test_token()
    print(f"   User: {USER_EMAIL}")
    print(f"   User ID: {USER_ID}")
    print(f"   Token: {token[:50]}...")
    print()

    # Generate OAuth start URL
    print("2. OAuth Start URL:")
    oauth_start_url = f"http://localhost:7777/api/oauth/notion/start?token={token}"
    print(f"   {oauth_start_url}")
    print()

    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. Copy the OAuth Start URL above")
    print("2. Open it in your browser")
    print("3. Authorize Cirkelline to access your Notion workspace")
    print("4. You'll be redirected back to the callback endpoint")
    print("5. Check the database to verify token storage")
    print()
    print("After authorization, run:")
    print("  python3 test_notion_oauth.py verify")
    print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print("Verification coming soon...")
    else:
        main()
