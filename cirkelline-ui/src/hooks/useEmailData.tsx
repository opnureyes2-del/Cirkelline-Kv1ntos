/**
 * Custom hook for Gmail data and operations
 * Provides email list, detail, send, reply, archive, and delete functionality
 */

import { useState, useCallback } from 'react';
import {
  Email,
  EmailDetail,
  EmailListResponse,
  SendEmailRequest,
  ReplyEmailRequest,
  EmailApiError
} from '@/types/email';

interface UseEmailDataReturn {
  // State
  emails: Email[];
  currentEmail: EmailDetail | null;
  loading: boolean;
  error: string | null;
  nextPageToken: string | null;

  // Actions
  fetchEmails: (count?: number, pageToken?: string) => Promise<void>;
  fetchEmailDetail: (emailId: string) => Promise<void>;
  sendEmail: (data: SendEmailRequest) => Promise<boolean>;
  replyToEmail: (emailId: string, data: ReplyEmailRequest) => Promise<boolean>;
  archiveEmail: (emailId: string) => Promise<boolean>;
  deleteEmail: (emailId: string) => Promise<boolean>;
  clearError: () => void;
  clearCurrentEmail: () => void;
}

export function useEmailData(): UseEmailDataReturn {
  const [emails, setEmails] = useState<Email[]>([]);
  const [currentEmail, setCurrentEmail] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextPageToken, setNextPageToken] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';

  /**
   * Get JWT token from localStorage
   */
  const getToken = useCallback((): string | null => {
    return localStorage.getItem('token');
  }, []);

  /**
   * Generic fetch wrapper with auth
   */
  const authenticatedFetch = useCallback(async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> => {
    const token = getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData: EmailApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response;
  }, [apiUrl, getToken]);

  /**
   * Fetch list of emails
   */
  const fetchEmails = useCallback(async (count: number = 20, pageToken?: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ count: count.toString() });
      if (pageToken) {
        params.append('page_token', pageToken);
      }

      const response = await authenticatedFetch(`/api/google/emails?${params}`);
      const data: EmailListResponse = await response.json();

      setEmails(data.emails);
      setNextPageToken(data.next_page_token || null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch emails';
      setError(errorMessage);
      console.error('Error fetching emails:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Mark an email as read in Gmail
   */
  const markAsRead = useCallback(async (emailId: string): Promise<boolean> => {
    try {
      await authenticatedFetch(`/api/google/emails/${emailId}/mark-read`, {
        method: 'POST',
      });
      return true;
    } catch (err) {
      console.error('Error marking email as read:', err);
      return false;
    }
  }, [authenticatedFetch]);

  /**
   * Fetch full email details
   */
  const fetchEmailDetail = useCallback(async (emailId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/emails/${emailId}`);
      const data: EmailDetail = await response.json();
      setCurrentEmail(data);

      // Mark as read in Gmail (fire and forget, don't wait)
      markAsRead(emailId);

      // Update the email in the list to mark it as read
      setEmails(prev => prev.map(email =>
        email.id === emailId
          ? { ...email, is_unread: false }
          : email
      ));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch email detail';
      setError(errorMessage);
      console.error('Error fetching email detail:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, markAsRead]);

  /**
   * Send a new email
   */
  const sendEmail = useCallback(async (data: SendEmailRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch('/api/google/emails/send', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send email';
      setError(errorMessage);
      console.error('Error sending email:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Reply to an email
   */
  const replyToEmail = useCallback(async (
    emailId: string,
    data: ReplyEmailRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/emails/${emailId}/reply`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reply to email';
      setError(errorMessage);
      console.error('Error replying to email:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Archive an email (remove from inbox)
   */
  const archiveEmail = useCallback(async (emailId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/emails/${emailId}/archive`, {
        method: 'POST',
      });

      // Remove from local state
      setEmails(prev => prev.filter(email => email.id !== emailId));

      // Clear current email if it was archived
      if (currentEmail?.id === emailId) {
        setCurrentEmail(null);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to archive email';
      setError(errorMessage);
      console.error('Error archiving email:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentEmail]);

  /**
   * Delete an email permanently
   */
  const deleteEmail = useCallback(async (emailId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/emails/${emailId}`, {
        method: 'DELETE',
      });

      // Remove from local state
      setEmails(prev => prev.filter(email => email.id !== emailId));

      // Clear current email if it was deleted
      if (currentEmail?.id === emailId) {
        setCurrentEmail(null);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete email';
      setError(errorMessage);
      console.error('Error deleting email:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentEmail]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Clear current email detail
   */
  const clearCurrentEmail = useCallback(() => {
    setCurrentEmail(null);
  }, []);

  return {
    // State
    emails,
    currentEmail,
    loading,
    error,
    nextPageToken,

    // Actions
    fetchEmails,
    fetchEmailDetail,
    sendEmail,
    replyToEmail,
    archiveEmail,
    deleteEmail,
    clearError,
    clearCurrentEmail,
  };
}
