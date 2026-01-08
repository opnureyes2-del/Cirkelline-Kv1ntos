import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { randomUUID } from 'crypto';
import { isAdminEmail, getAdminProfile } from '@/config/adminProfiles';

const JWT_SECRET = process.env.JWT_SECRET!;
const SALT_ROUNDS = 12;

export interface JWTPayload {
  user_id: string;
  email: string;
  display_name: string;
  // New fields for backend JWT Middleware
  user_name?: string;
  user_role?: string;
  user_type?: string;
  // Legacy admin fields (keeping for backwards compatibility)
  is_admin?: boolean;
  admin_name?: string;
  admin_role?: string;
  admin_context?: string;
  admin_preferences?: string;
  admin_instructions?: string;
  exp?: number;
  iat?: number;
}

export function signToken(payload: Omit<JWTPayload, 'exp' | 'iat'>): string {
  // Base payload with timestamps
  const tokenPayload: Partial<JWTPayload> & { iat: number } = {
    user_id: payload.user_id,
    email: payload.email,
    display_name: payload.display_name,
    iat: Math.floor(Date.now() / 1000)
  };

  // Check if user is admin and add profile
  if (isAdminEmail(payload.email)) {
    const adminProfile = getAdminProfile(payload.email);
    if (adminProfile) {
      // New fields for backend JWT Middleware (used by dependencies_claims)
      tokenPayload.user_name = adminProfile.name;
      tokenPayload.user_role = adminProfile.role;
      tokenPayload.user_type = "Admin";

      // Legacy fields (keeping for backwards compatibility)
      tokenPayload.is_admin = true;
      tokenPayload.admin_name = adminProfile.name;
      tokenPayload.admin_role = adminProfile.role;
      tokenPayload.admin_context = adminProfile.context;
      tokenPayload.admin_preferences = adminProfile.preferences;
      tokenPayload.admin_instructions = adminProfile.instructions;

      console.log(`✅ Admin JWT generated for: ${adminProfile.name} (${payload.email})`);
    }
  } else {
    // Regular user - set new fields
    tokenPayload.user_name = payload.display_name;
    tokenPayload.user_role = "User";
    tokenPayload.user_type = "Regular";
    tokenPayload.is_admin = false;
    console.log(`✅ Regular user JWT generated for: ${payload.email}`);
  }

  return jwt.sign(tokenPayload, JWT_SECRET, { expiresIn: '7d' });
}

export function verifyToken(token: string): JWTPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload;
  } catch {
    return null;
  }
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function comparePassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function validatePassword(password: string): { valid: boolean; error?: string } {
  if (password.length < 8) {
    return { valid: false, error: 'Password must be at least 8 characters long' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one uppercase letter' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one number' };
  }
  return { valid: true };
}

export function validateEmail(email: string): { valid: boolean; error?: string } {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }
  return { valid: true };
}

export function generateAnonUserId(): string {
  return `anon-${randomUUID()}`;
}
