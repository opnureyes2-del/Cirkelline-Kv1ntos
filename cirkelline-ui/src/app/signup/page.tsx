"use client"

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export default function SignupPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, display_name: displayName }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || 'Signup failed');
        setLoading(false);
        return;
      }

      // Signup successful
      login(data.token);
      router.push('/');
    } catch {
      setError('An error occurred. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-light-bg dark:bg-dark-bg transition-colors">
      <div className="w-full max-w-md space-y-8 rounded-lg border border-gray-300 bg-light-surface p-8 shadow-lg dark:border-gray-700 dark:bg-dark-surface">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-light-text dark:text-dark-text">Create Account</h2>
          <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Or{' '}
            <Link href="/" className="font-medium text-accent hover:underline">
              continue as guest
            </Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="displayName" className="block text-sm font-medium text-light-text dark:text-dark-text">
                Display Name
              </label>
              <input
                id="displayName"
                type="text"
                required
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 bg-light-bg px-3 py-2 text-light-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent dark:border-gray-700 dark:bg-dark-bg dark:text-dark-text transition-colors"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-light-text dark:text-dark-text">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 bg-light-bg px-3 py-2 text-light-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent dark:border-gray-700 dark:bg-dark-bg dark:text-dark-text transition-colors"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-light-text dark:text-dark-text">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 bg-light-bg px-3 py-2 text-light-text focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent dark:border-gray-700 dark:bg-dark-bg dark:text-dark-text transition-colors"
              />
              <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                Must be 8+ characters with 1 uppercase letter and 1 number
              </p>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-accent px-4 py-2 text-white hover:bg-accent/90 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>

          <div className="text-center text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-accent hover:underline">
              Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
