"""Test JWT Middleware with admin profiles."""
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Test JWT generation
def create_test_admin_jwt():
    """Create a test JWT token with admin profile."""
    payload = {
        "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
        "email": "opnureyes2@gmail.com",
        "display_name": "eenvy",
        "is_admin": True,
        "admin_name": "Ivo",
        "admin_role": "CEO & Creator",
        "admin_context": "Founded Cirkelline, focuses on AI strategy and product development",
        "admin_preferences": "Prefers technical details with code examples. Likes direct, efficient communication.",
        "admin_instructions": "Always provide technical implementation details. Include code snippets when relevant.",
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
    return token

def create_test_user_jwt():
    """Create a test JWT token for regular user."""
    payload = {
        "user_id": "test-user-123",
        "email": "user@example.com",
        "display_name": "Test User",
        "is_admin": False,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
    return token

if __name__ == "__main__":
    print("=== ADMIN JWT TOKEN ===")
    admin_token = create_test_admin_jwt()
    print(f"Token: {admin_token}\n")

    # Decode to verify
    decoded = jwt.decode(admin_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
    print("Decoded payload:")
    for key, value in decoded.items():
        if key not in ['exp', 'iat']:
            print(f"  {key}: {value}")

    print("\n=== USER JWT TOKEN ===")
    user_token = create_test_user_jwt()
    print(f"Token: {user_token}\n")

    decoded = jwt.decode(user_token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
    print("Decoded payload:")
    for key, value in decoded.items():
        if key not in ['exp', 'iat']:
            print(f"  {key}: {value}")

    print("\n=== NEXT STEPS ===")
    print("1. Use admin_token in Authorization header")
    print("2. Send POST request to /teams/cirkelline/runs")
    print("3. Cirkelline should recognize you as Ivo")
    print("\nExample curl:")
    print(f'curl -X POST http://localhost:7777/teams/cirkelline/runs \\')
    print(f'  -H "Authorization: Bearer {admin_token}" \\')
    print(f'  -H "Content-Type: application/x-www-form-urlencoded" \\')
    print(f'  -d "message=Who am I?"')
