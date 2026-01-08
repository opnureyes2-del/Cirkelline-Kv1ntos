/**
 * Email data types for Google Gmail integration
 * Matches backend API responses from /api/google/emails endpoints
 */

/**
 * Email summary data from list endpoint
 */
export interface Email {
  id: string;
  thread_id?: string;
  from: string;
  to?: string;
  subject: string;
  snippet: string;
  is_unread: boolean;
  date: string;
  labels: string[];
  has_attachments?: boolean;
}

/**
 * Full email details from get endpoint
 */
export interface EmailDetail {
  id: string;
  from: string;
  to: string;
  subject: string;
  body_text: string;
  body_html: string;
  date: string;
  labels: string[];
  is_unread: boolean;
}

/**
 * Response from GET /api/google/emails
 */
export interface EmailListResponse {
  emails: Email[];
  next_page_token?: string;
}

/**
 * Request body for POST /api/google/emails/send
 */
export interface SendEmailRequest {
  to: string;
  subject: string;
  body: string;
}

/**
 * Request body for POST /api/google/emails/{id}/reply
 */
export interface ReplyEmailRequest {
  body: string;
  reply_all?: boolean;
}

/**
 * Generic API error response
 */
export interface EmailApiError {
  detail: string;
}
