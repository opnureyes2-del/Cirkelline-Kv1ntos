# Frontend JWT Testing Guide

## Testing Admin JWT Generation

### 1. Clear Existing Tokens
```javascript
// In browser console
localStorage.clear();
// Or specifically:
localStorage.removeItem('token');
```

### 2. Login as Admin
- Navigate to login page
- Login with: **opnureyes2@gmail.com**
- Password: [your password]

### 3. Inspect Generated JWT
```javascript
// In browser console - the inspection utilities are auto-loaded
inspectStoredToken();

// Or manually:
const token = localStorage.getItem('token');
console.log('Token:', token);

// Decode and inspect
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('Payload:', payload);

// Should see:
// - is_admin: true
// - admin_name: "Ivo"
// - admin_role: "CEO & Creator"
// - admin_context: "Founded Cirkelline..."
// - admin_preferences: "Prefers technical..."
// - admin_instructions: "Always provide..."
```

### 4. Test Chat with Cirkelline
- Go to chat page
- Send message: **"Who am I?"**
- Cirkelline should respond recognizing you as "Ivo, CEO & Creator"

### 5. Test Regular User
- Logout
- Create/login with a different email (not in ADMIN_PROFILES)
- Check JWT: should have `is_admin: false`
- No admin profile fields should be present
- Cirkelline should treat as "Standard User"

## Troubleshooting

### JWT doesn't contain admin profile
- Check `adminProfiles.ts` has correct email
- Verify import path in `auth.ts`
- Check console logs for "Admin JWT generated" message
- Restart dev server after changes

### JWT_SECRET_KEY mismatch
- Backend returns 401 Unauthorized
- Copy JWT_SECRET_KEY from backend `.env`
- Update frontend `.env.local` (use `JWT_SECRET`, not `JWT_SECRET_KEY`)
- Restart frontend dev server
- Clear browser localStorage and re-login

### Cirkelline doesn't recognize admin
- Backend issue, not frontend
- Verify backend JWT middleware is running
- Check backend logs for JWT processing
- Test with curl and manually generated token

## Quick Reference

### JWT Inspection in Browser Console
```javascript
// Auto-loaded utilities (available globally)
inspectStoredToken()  // Inspect token from localStorage
inspectJWT(token)     // Inspect specific token
```

### Expected Admin JWT Payload
```json
{
  "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "email": "opnureyes2@gmail.com",
  "display_name": "eenvy",
  "is_admin": true,
  "admin_name": "Ivo",
  "admin_role": "CEO & Creator",
  "admin_context": "Founded Cirkelline, focuses on AI strategy and product development",
  "admin_preferences": "Prefers technical details with code examples. Likes direct, efficient communication.",
  "admin_instructions": "Always provide technical implementation details. Include code snippets when relevant. Be direct and skip unnecessary explanations.",
  "iat": 1234567890,
  "exp": 1234567890
}
```

### Expected Regular User JWT Payload
```json
{
  "user_id": "some-user-id",
  "email": "user@example.com",
  "display_name": "User Name",
  "is_admin": false,
  "iat": 1234567890,
  "exp": 1234567890
}
```

## Adding New Admins

Edit `src/config/adminProfiles.ts`:

```typescript
export const ADMIN_PROFILES: Record<string, AdminProfile> = {
  "opnureyes2@gmail.com": { /* Ivo's profile */ },
  "maria@cirkelline.com": {
    name: "Maria",
    role: "Legal Advisor",
    context: "Handles all legal matters for Cirkelline",
    preferences: "Prefers formal legal language",
    instructions: "Focus on compliance and risk assessment"
  }
};
```

No backend changes needed! Next login for the new admin will include their profile in the JWT.

## Implementation Details

### Files Modified
1. **src/config/adminProfiles.ts** (NEW) - Admin profiles configuration
2. **src/lib/auth.ts** - Updated `signToken()` to include admin profile
3. **src/utils/inspectJWT.ts** (NEW) - JWT inspection utilities

### JWT Flow
1. User logs in with email/password
2. `signToken()` checks if email is in `ADMIN_PROFILES`
3. If admin: Include all profile fields in JWT payload
4. If not admin: Set `is_admin: false`, no profile fields
5. JWT signed with `JWT_SECRET` and returned to client
6. Client stores JWT in localStorage
7. Client sends JWT in Authorization header on each request
8. Backend JWT Middleware extracts claims and injects as dependencies
9. Cirkelline uses dependencies to adapt responses

### Security
- JWT tokens signed with secret key
- Cannot be forged or tampered
- Expire after 7 days
- Profile data is read-only
- Backend validates signature on every request
