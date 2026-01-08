// components/chat/Sidebar/DocumentCard.tsx
'use client'
import React from 'react';
import { Trash2, Share2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface DocumentCardProps {
  document: {
    id: string;
    name: string;
    size: number;
    status: 'processing' | 'completed' | 'failed';
    uploaded_at: string;
    metadata: Record<string, unknown>;
  };
  onDelete: (id: string) => void;
}

// Format date and time together
function formatDateTime(dateString: string): string {
  if (!dateString) return 'Unknown';

  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  const timeStr = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });

  // If today, show "Today HH:mm"
  if (diffDays === 0) {
    return `Today ${timeStr}`;
  }

  // If within 7 days, show day name
  if (diffDays < 7) {
    const dayStr = date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
    return `${dayStr} ${timeStr}`;
  }

  // Otherwise show full date
  const dateStr = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
  return `${dateStr} ${timeStr}`;
}

export function DocumentCard({ document, onDelete }: DocumentCardProps) {
  // Status dot colors
  const statusDot = {
    processing: 'bg-yellow-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };

  const dotColor = statusDot[document.status] || statusDot.completed;

  // Check if this is an admin-shared document
  const isShared = document.metadata?.access_level === 'admin-shared';
  const sharedByName = document.metadata?.shared_by_name as string | undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-light-bg dark:bg-dark-bg border border-border-primary hover:border-border-primary transition-colors group"
      whileHover={{ scale: 1.02, y: -1 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.15 }}
    >
      {/* Document Info */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate mb-1 text-[#6b6b6b] dark:text-[#a0a0a0]" title={document.name}>
          {document.name}
        </div>

        <div className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
          {/* Status Dot */}
          <div className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          {/* Date and Time */}
          <span>{formatDateTime(document.uploaded_at)}</span>
        </div>

        {/* Shared Indicator */}
        {isShared && sharedByName && (
          <div className="flex items-center gap-1.5 mt-1 text-xs text-accent">
            <Share2 size={18} />
            <span>Shared by {sharedByName}</span>
          </div>
        )}
      </div>

      {/* Delete Button */}
      <motion.button
        onClick={() => onDelete(document.id)}
        disabled={document.status === 'processing'}
        className="flex-shrink-0 p-1.5 rounded-lg text-light-text-secondary dark:text-dark-text-secondary hover:text-error hover:bg-error/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed opacity-0 group-hover:opacity-100"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        title="Delete document"
      >
        <Trash2 size={18} />
      </motion.button>
    </motion.div>
  );
}
