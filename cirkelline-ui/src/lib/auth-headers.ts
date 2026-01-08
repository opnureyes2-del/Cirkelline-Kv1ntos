/**
 * Get Authorization headers for API requests
 * Returns headers with Bearer token if user is logged in
 */
export function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') {
    return {};
  }

  const token = localStorage.getItem('token');

  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }

  return {};
}

/**
 * Get full headers including Content-Type and Authorization
 */
export function getAPIHeaders(contentType: string = 'application/json'): Record<string, string> {
  return {
    'Content-Type': contentType,
    ...getAuthHeaders()
  };
}
