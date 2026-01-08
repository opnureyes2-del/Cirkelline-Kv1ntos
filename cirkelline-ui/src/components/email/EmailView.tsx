/**
 * EmailView - Main Email Container
 * Two-panel layout: Left (email list) + Right (detail/compose)
 * Follows Cirkelline design system and Calendar architecture pattern
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Email, EmailDetail } from '@/types/email';
import { ChevronDown, Trash2, Archive, Folder, Square, CheckSquare, ArrowLeft, Reply } from 'lucide-react';

interface EmailViewProps {
  // Data
  emails: Email[];
  currentEmail: EmailDetail | null;
  loading: boolean;
  selectedFolder: string;
  nextPageToken: string | null;

  // Layout
  layoutMode?: 'stacked' | 'side-by-side';

  // Actions
  fetchEmails: (count?: number, pageToken?: string) => Promise<void>;
  fetchEmailDetail: (emailId: string) => Promise<void>;
  sendEmail: (data: { to: string; subject: string; body: string }) => Promise<boolean>;
  replyToEmail: (emailId: string, data: { body: string; reply_all?: boolean }) => Promise<boolean>;
  archiveEmail: (emailId: string) => Promise<boolean>;
  deleteEmail: (emailId: string) => Promise<boolean>;
}

type ViewType = 'list' | 'detail' | 'compose' | 'reply';

// Helper function to format date as relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';

  // For older dates, show month and day
  const month = date.toLocaleDateString('en-US', { month: 'short' });
  const day = date.getDate();
  return `${month} ${day}`;
}

export default function EmailView({
  emails,
  currentEmail,
  loading,
  selectedFolder,
  nextPageToken,
  layoutMode = 'stacked',
  fetchEmails,
  fetchEmailDetail,
  sendEmail,
  replyToEmail,
  archiveEmail,
  deleteEmail,
}: EmailViewProps) {
  // State
  const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
  const [view, setView] = useState<ViewType>('list');
  const [leftPanelWidth, setLeftPanelWidth] = useState(30); // 30% default - left panel smaller
  const [topPanelHeight, setTopPanelHeight] = useState(40); // 40% default for stacked internal layout
  const [isResizing, setIsResizing] = useState(false);

  // When in side-by-side container mode, use vertical (stacked) internal layout
  const isVerticalLayout = layoutMode === 'side-by-side';

  // Filter emails by selected folder
  const filteredEmails = useMemo(() => {
    return emails.filter(email => {
      if (!email.labels) return selectedFolder === 'INBOX';
      return email.labels.includes(selectedFolder);
    });
  }, [emails, selectedFolder]);

  // Handle email click
  const handleEmailClick = useCallback(async (email: Email) => {
    await fetchEmailDetail(email.id);
    setView('detail');
  }, [fetchEmailDetail]);

  // Handle email selection (checkbox)
  const handleEmailSelect = useCallback((emailId: string, checked: boolean) => {
    setSelectedEmails(prev =>
      checked ? [...prev, emailId] : prev.filter(id => id !== emailId)
    );
  }, []);

  // Handle select all
  const handleSelectAll = useCallback((checked: boolean) => {
    setSelectedEmails(checked ? filteredEmails.map(e => e.id) : []);
  }, [filteredEmails]);

  // Handle batch delete
  const handleBatchDelete = useCallback(async () => {
    for (const emailId of selectedEmails) {
      await deleteEmail(emailId);
    }
    setSelectedEmails([]);
    await fetchEmails(20);
  }, [selectedEmails, deleteEmail, fetchEmails]);

  // Handle batch archive
  const handleBatchArchive = useCallback(async () => {
    for (const emailId of selectedEmails) {
      await archiveEmail(emailId);
    }
    setSelectedEmails([]);
    await fetchEmails(20);
  }, [selectedEmails, archiveEmail, fetchEmails]);

  // Handle compose
  const handleCompose = useCallback(() => {
    setView('compose');
  }, []);

  // Handle reply
  const handleReply = useCallback(() => {
    if (currentEmail) {
      setView('reply');
    }
  }, [currentEmail]);

  // Handle back to list
  const handleBack = useCallback(() => {
    setView('list');
  }, []);

  // Handle send
  const handleSend = useCallback(async (data: { to: string; subject: string; body: string }) => {
    const success = await sendEmail(data);
    if (success) {
      setView('list');
      await fetchEmails(20);
    }
    return success;
  }, [sendEmail, fetchEmails]);

  // Handle reply submit
  const handleReplySubmit = useCallback(async (body: string) => {
    if (currentEmail) {
      const success = await replyToEmail(currentEmail.id, { body });
      if (success) {
        setView('detail');
        await fetchEmails(20);
      }
      return success;
    }
    return false;
  }, [currentEmail, replyToEmail, fetchEmails]);

  // Handle load more
  const handleLoadMore = useCallback(async () => {
    if (nextPageToken) {
      await fetchEmails(20, nextPageToken);
    }
  }, [nextPageToken, fetchEmails]);

  // Resize handlers (horizontal for stacked, vertical for side-by-side)
  const handleMouseDown = useCallback(() => {
    setIsResizing(true);
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const container = document.querySelector('.email-container');
    if (!container) return;

    const containerRect = container.getBoundingClientRect();

    if (isVerticalLayout) {
      // Vertical resize
      const newHeight = ((e.clientY - containerRect.top) / containerRect.height) * 100;
      const clampedHeight = Math.min(Math.max(newHeight, 25), 75);
      setTopPanelHeight(clampedHeight);
    } else {
      // Horizontal resize
      const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      const clampedWidth = Math.min(Math.max(newWidth, 30), 70);
      setLeftPanelWidth(clampedWidth);
    }
  }, [isVerticalLayout]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Add/remove mouse event listeners
  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = isVerticalLayout ? 'row-resize' : 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, isVerticalLayout, handleMouseMove, handleMouseUp]);

  // Listen for compose event from header
  React.useEffect(() => {
    const handleComposeEvent = () => {
      handleCompose();
    };
    window.addEventListener('email-compose', handleComposeEvent);
    return () => {
      window.removeEventListener('email-compose', handleComposeEvent);
    };
  }, [handleCompose]);

  return (
    <div className={`email-container flex h-full overflow-hidden ${isVerticalLayout ? 'flex-col' : 'flex-col md:flex-row'}`} style={{ backgroundColor: 'var(--app-container-bg)' }}>
      {/* Top/Left Panel: Email List */}
      <div
        className="flex flex-col overflow-hidden"
        style={isVerticalLayout
          ? { height: `${topPanelHeight}%` }
          : { width: `${leftPanelWidth}%` }
        }
      >
        {/* Batch Actions Toolbar */}
        {selectedEmails.length > 0 && (
          <div className="p-2 pl-3 bg-app-container border-b border-border-primary flex items-center gap-2">
            <span className="text-xs text-light-text dark:text-dark-text">
              {selectedEmails.length} selected
            </span>
            <button
              onClick={handleBatchArchive}
              className="p-1.5 rounded hover:bg-accent/10 text-light-text-secondary dark:text-dark-text-secondary transition-colors"
              title="Archive"
            >
              <Archive size={14} />
            </button>
            <button
              onClick={handleBatchDelete}
              className="p-1.5 rounded hover:bg-red-500/10 text-red-600 dark:text-red-400 transition-colors"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        )}

        {/* Email List */}
        <div className="flex-1 overflow-y-auto app-scroll">
          {/* Select All - Only show when at least one email is selected */}
          {selectedEmails.length > 0 && (
            <div className="sticky top-0 bg-app-container border-b border-border-primary p-2 pl-3 flex items-center gap-2 z-10">
              <button
                onClick={() => handleSelectAll(!(filteredEmails.length > 0 && selectedEmails.length === filteredEmails.length))}
                className="flex-shrink-0 hover:scale-110 transition-transform focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-light-surface dark:focus:ring-offset-dark-surface rounded"
                aria-label={filteredEmails.length > 0 && selectedEmails.length === filteredEmails.length ? 'Deselect all' : 'Select all'}
              >
                {filteredEmails.length > 0 && selectedEmails.length === filteredEmails.length ? (
                  <CheckSquare
                    size={16}
                    className="text-accent animate-in zoom-in duration-200"
                  />
                ) : (
                  <Square
                    size={16}
                    className="text-gray-400 dark:text-gray-500 hover:text-accent transition-colors"
                  />
                )}
              </button>
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                Select all
              </span>
            </div>
          )}

          {filteredEmails.length === 0 ? (
            <div className="p-4 text-center text-light-text-secondary dark:text-dark-text-secondary text-sm">
              No emails in this folder
            </div>
          ) : (
            <div className="divide-y divide-border-primary">
              {filteredEmails.map((email, index) => (
                <motion.div
                  key={email.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className={`p-2 pl-3 hover:bg-app-container transition-colors cursor-pointer ${
                    email.is_unread ? 'bg-app-container' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {/* Checkbox */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEmailSelect(email.id, !selectedEmails.includes(email.id));
                      }}
                      className="mt-0.5 flex-shrink-0 hover:scale-110 transition-transform focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-light-surface dark:focus:ring-offset-dark-surface rounded"
                      aria-label={selectedEmails.includes(email.id) ? 'Deselect email' : 'Select email'}
                    >
                      {selectedEmails.includes(email.id) ? (
                        <CheckSquare
                          size={16}
                          className="text-accent animate-in zoom-in duration-200"
                        />
                      ) : (
                        <Square
                          size={16}
                          className="text-gray-400 dark:text-gray-500 hover:text-accent transition-colors"
                        />
                      )}
                    </button>

                    {/* Email Info */}
                    <div onClick={() => handleEmailClick(email)} className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className={`text-xs truncate ${email.is_unread ? 'font-semibold text-light-text dark:text-dark-text' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                          {email.from}
                        </p>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className={`text-[10px] ${email.is_unread ? 'text-light-text-secondary dark:text-dark-text-secondary' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                            {formatRelativeTime(email.date)}
                          </span>
                          {email.is_unread && (
                            <span className="w-2 h-2 rounded-full bg-accent flex-shrink-0" />
                          )}
                        </div>
                      </div>
                      <p className={`text-xs truncate ${email.is_unread ? 'font-medium text-light-text dark:text-dark-text' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                        {email.subject || '(no subject)'}
                      </p>
                      <p className={`text-[10px] truncate mt-0.5 ${email.is_unread ? 'text-light-text/50 dark:text-dark-text/50' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                        {email.snippet}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Load More Button */}
          {nextPageToken && (
            <div className="p-2 border-t border-border-primary">
              <button
                onClick={handleLoadMore}
                disabled={loading}
                className="w-full px-4 py-2 rounded-lg bg-app-container hover:bg-accent/10 text-light-text dark:text-dark-text text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? 'Loading...' : (
                  <>
                    <ChevronDown size={14} />
                    Load More
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Resize Handle */}
      <div
        className={`hidden md:block flex-shrink-0 transition-all ${
          isVerticalLayout
            ? 'h-1 hover:h-1.5 w-full bg-border-primary hover:bg-accent cursor-row-resize'
            : 'w-1 hover:w-1.5 bg-border-primary hover:bg-accent cursor-col-resize'
        }`}
        onMouseDown={handleMouseDown}
        style={{ userSelect: 'none' }}
      />

      {/* Right Panel: Email Detail / Compose */}
      <div className={`flex-1 h-full ${view === 'list' ? 'overflow-hidden' : 'overflow-y-auto app-scroll'}`}>
        {view === 'list' && (
          <div className="flex flex-col items-center justify-center h-full">
            <Folder className="w-12 h-12 text-light-text/20 dark:text-dark-text/20 mb-3" />
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
              Select an email to read
            </p>
          </div>
        )}

        {view === 'detail' && currentEmail && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="p-4"
          >
            {/* Action Buttons - Top */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={handleBack}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-app-container hover:bg-accent/10 text-light-text dark:text-dark-text rounded transition-colors"
              >
                <ArrowLeft size={14} />
                Back
              </button>
              <button
                onClick={handleReply}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-accent hover:bg-accent/90 text-white rounded transition-colors"
              >
                <Reply size={14} />
                Reply
              </button>
              <button
                onClick={async () => {
                  await deleteEmail(currentEmail.id);
                  setView('list');
                  await fetchEmails(20);
                }}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20 rounded transition-colors ml-auto"
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>

            {/* Email Header */}
            <div className="mb-4 pb-3 border-b border-border-primary">
              <h2 className="text-lg font-semibold text-light-text dark:text-dark-text mb-2">
                {currentEmail.subject || '(no subject)'}
              </h2>
              <div className="space-y-1 text-xs">
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  <span className="font-medium text-light-text dark:text-dark-text">From:</span> {currentEmail.from}
                </p>
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  <span className="font-medium text-light-text dark:text-dark-text">To:</span> {currentEmail.to}
                </p>
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  <span className="font-medium text-light-text dark:text-dark-text">Date:</span> {new Date(currentEmail.date).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Email Body - Isolated in iframe */}
            <div className="mb-4 rounded-lg">
              <iframe
                srcDoc={`
                  <!DOCTYPE html>
                  <html>
                    <head>
                      <meta charset="UTF-8">
                      <meta name="viewport" content="width=device-width, initial-scale=1.0">
                      <style>
                        body {
                          margin: 0;
                          padding: 16px;
                          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                          font-size: 14px;
                          line-height: 1.6;
                          color: #1a1a1a;
                          background-color: transparent;
                          word-wrap: break-word;
                          overflow-wrap: break-word;
                        }
                        a {
                          color: #2563eb;
                          text-decoration: underline;
                        }
                        img {
                          max-width: 100%;
                          height: auto;
                        }
                        table {
                          max-width: 100%;
                          border-collapse: collapse;
                        }
                      </style>
                    </head>
                    <body>
                      ${currentEmail.body_html || currentEmail.body_text.replace(/\n/g, '<br>')}
                    </body>
                  </html>
                `}
                className="w-full border-0 bg-transparent"
                style={{ minHeight: '200px' }}
                onLoad={(e) => {
                  const iframe = e.target as HTMLIFrameElement;
                  if (iframe.contentWindow) {
                    // Auto-resize iframe to content height
                    const resizeIframe = () => {
                      const body = iframe.contentWindow?.document.body;
                      if (body) {
                        iframe.style.height = body.scrollHeight + 32 + 'px';
                      }
                    };
                    resizeIframe();
                    // Watch for content changes
                    const resizeObserver = new ResizeObserver(resizeIframe);
                    if (iframe.contentWindow.document.body) {
                      resizeObserver.observe(iframe.contentWindow.document.body);
                    }
                  }
                }}
                sandbox="allow-same-origin"
                title="Email content"
              />
            </div>
          </motion.div>
        )}

        {view === 'compose' && (
          <ComposeForm
            onSend={handleSend}
            onCancel={handleBack}
            loading={loading}
          />
        )}

        {view === 'reply' && currentEmail && (
          <ReplyForm
            originalEmail={currentEmail}
            onSend={handleReplySubmit}
            onCancel={handleBack}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}

// Compose Form Component
function ComposeForm({
  onSend,
  onCancel,
  loading,
}: {
  onSend: (data: { to: string; subject: string; body: string }) => Promise<boolean>;
  onCancel: () => void;
  loading: boolean;
}) {
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSend({ to, subject, body });
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      onSubmit={handleSubmit}
      className="p-4 space-y-3"
    >
      <h2 className="text-sm font-semibold text-light-text dark:text-dark-text mb-3">
        New Email
      </h2>

      <div>
        <label className="block text-xs font-medium text-light-text dark:text-dark-text mb-1">
          To
        </label>
        <input
          type="email"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          required
          className="w-full px-3 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:border-accent focus:outline-none text-sm"
          placeholder="recipient@example.com"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-light-text dark:text-dark-text mb-1">
          Subject
        </label>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
          className="w-full px-3 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:border-accent focus:outline-none text-sm"
          placeholder="Email subject"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-light-text dark:text-dark-text mb-1">
          Message
        </label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={10}
          className="w-full px-3 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:border-accent focus:outline-none text-sm resize-none"
          placeholder="Write your message..."
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </motion.form>
  );
}

// Reply Form Component
function ReplyForm({
  originalEmail,
  onSend,
  onCancel,
  loading,
}: {
  originalEmail: EmailDetail;
  onSend: (body: string) => Promise<boolean>;
  onCancel: () => void;
  loading: boolean;
}) {
  const [body, setBody] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSend(body);
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      onSubmit={handleSubmit}
      className="p-4 space-y-3"
    >
      <h2 className="text-sm font-semibold text-light-text dark:text-dark-text mb-3">
        Reply to: {originalEmail.subject}
      </h2>

      <div className="p-3 rounded-lg bg-app-container border border-border-primary text-xs">
        <p className="text-light-text-secondary dark:text-dark-text-secondary mb-2">
          <span className="font-medium">From:</span> {originalEmail.from}
        </p>
        <div className="max-h-32 overflow-y-auto text-light-text/60 dark:text-dark-text/60">
          {originalEmail.body_text.substring(0, 200)}...
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-light-text dark:text-dark-text mb-1">
          Your Reply
        </label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          rows={8}
          className="w-full px-3 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:border-accent focus:outline-none text-sm resize-none"
          placeholder="Write your reply..."
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Sending...' : 'Send Reply'}
        </button>
      </div>
    </motion.form>
  );
}
