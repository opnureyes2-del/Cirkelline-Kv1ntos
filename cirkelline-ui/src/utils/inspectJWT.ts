/**
 * JWT Inspection Utility (Development Only)
 * Use this to verify JWT tokens contain correct data
 */

export function inspectJWT(token: string): void {
  if (typeof window === 'undefined') return; // Server-side

  try {
    // Decode JWT (without verification, for inspection only)
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.error('Invalid JWT format');
      return;
    }

    const payload = JSON.parse(atob(parts[1]));

    console.log('=== JWT TOKEN INSPECTION ===');
    console.log('User ID:', payload.user_id);
    console.log('Email:', payload.email);
    console.log('Display Name:', payload.display_name);
    console.log('Is Admin:', payload.is_admin);

    if (payload.is_admin) {
      console.log('Admin Name:', payload.admin_name);
      console.log('Admin Role:', payload.admin_role);
      console.log('Admin Context:', payload.admin_context);
      console.log('Admin Preferences:', payload.admin_preferences);
      console.log('Admin Instructions:', payload.admin_instructions);
    }

    console.log('Issued At:', new Date(payload.iat * 1000).toLocaleString());
    console.log('Expires:', new Date(payload.exp * 1000).toLocaleString());
    console.log('============================');

    return payload;
  } catch (error) {
    console.error('Error inspecting JWT:', error);
  }
}

/**
 * Quick inspect from localStorage
 */
export function inspectStoredToken(): void {
  if (typeof window === 'undefined') return;

  const token = localStorage.getItem('token');
  if (!token) {
    console.error('No token found in localStorage');
    return;
  }

  inspectJWT(token);
}

// Extend window interface for debugging utilities
declare global {
  interface Window {
    inspectJWT: typeof inspectJWT;
    inspectStoredToken: typeof inspectStoredToken;
  }
}

// Make available in browser console for debugging
if (typeof window !== 'undefined') {
  window.inspectJWT = inspectJWT;
  window.inspectStoredToken = inspectStoredToken;
  console.log('🔍 JWT Inspection utilities loaded. Use:');
  console.log('  inspectStoredToken() - Inspect token from localStorage');
  console.log('  inspectJWT(token) - Inspect specific token');
}
