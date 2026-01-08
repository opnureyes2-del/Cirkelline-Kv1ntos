import { useState, useEffect } from 'react';

interface User {
  user_id: string;
  email: string;
  user_name: string;
  user_role?: string;
  user_type?: string;
  is_admin?: boolean;
}

interface UseAuthReturn {
  user: User | null;
  loading: boolean;
}

function decodeJWT(token: string): User | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const decodedUser = decodeJWT(token);
      setUser(decodedUser);
    }
    setLoading(false);
  }, []);

  return { user, loading };
}
