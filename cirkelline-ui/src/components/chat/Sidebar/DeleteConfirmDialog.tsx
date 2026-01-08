// components/chat/Sidebar/DeleteConfirmDialog.tsx
'use client'
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  documentName: string;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting?: boolean;
}

export function DeleteConfirmDialog({
  isOpen,
  documentName,
  onConfirm,
  onCancel,
  isDeleting = false,
}: DeleteConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-[100]"
            onClick={onCancel}
          />

          {/* Modal */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", duration: 0.3 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] bg-light-surface dark:bg-dark-surface border border-border-primary rounded-xl w-[90vw] sm:w-auto min-w-[320px] sm:min-w-[400px] max-w-[500px]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-5 border-b border-border-primary">
              <h3 className="font-heading text-lg font-semibold text-light-text dark:text-dark-text flex items-center gap-2">
                🗑️ Delete Document
              </h3>
            </div>

            {/* Body */}
            <div className="p-5 space-y-3">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Are you sure you want to delete:
              </p>
              <p className="font-medium text-light-text dark:text-dark-text bg-light-bg dark:bg-dark-bg p-3 rounded-lg break-words">
                &ldquo;{documentName}&rdquo;
              </p>
              <p className="text-sm text-error font-medium">
                This action cannot be undone.
              </p>
            </div>

            {/* Actions */}
            <div className="p-4 border-t border-border-primary flex gap-3 justify-end">
              <button
                onClick={onCancel}
                disabled={isDeleting}
                className="px-5 py-2.5 border border-border-primary rounded-lg text-sm font-medium text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                disabled={isDeleting}
                className="px-5 py-2.5 bg-error text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isDeleting && (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
