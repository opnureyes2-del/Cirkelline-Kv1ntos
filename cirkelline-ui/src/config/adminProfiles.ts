/**
 * Admin Profiles Configuration
 *
 * Define admin users and their profiles here.
 * These profiles are included in JWT tokens at login.
 */

export interface AdminProfile {
  name: string;
  role: string;
  context: string;
  preferences: string;
  instructions: string;
}

export const ADMIN_PROFILES: Record<string, AdminProfile> = {
  "opnureyes2@gmail.com": {
    name: "Ivo",
    role: "CEO & Creator",
    context: "Co-founder of Cirkelline, focuses on AI strategy and product development",
    preferences: "Prefers technical details with code examples. Likes direct, efficient communication.",
    instructions: "Always provide technical implementation details. Include code snippets when relevant. Be direct and skip unnecessary explanations."
  },
  "opnureyes2@gmail.com": {
    name: "Rasmus",
    role: "CEO & Creator",
    context: "Co-founder of Cirkelline, focuses on business strategy and operations",
    preferences: "",
    instructions: ""
  }
  // Add more admins here as needed
};

/**
 * Check if email belongs to an admin
 */
export function isAdminEmail(email: string): boolean {
  return email in ADMIN_PROFILES;
}

/**
 * Get admin profile by email
 */
export function getAdminProfile(email: string): AdminProfile | null {
  return ADMIN_PROFILES[email] || null;
}
