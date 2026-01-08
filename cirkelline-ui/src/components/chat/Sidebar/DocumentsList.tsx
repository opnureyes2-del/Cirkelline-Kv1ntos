// components/chat/Sidebar/DocumentsList.tsx
'use client'
import React, { useState, useEffect } from 'react';
import { useDocuments } from '@/hooks/useDocuments';
import { useAuth } from '@/hooks/useAuth';
import { DocumentCard } from './DocumentCard';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import { UploadDialog } from './UploadDialog';
import { AnimatePresence } from 'framer-motion';
import { Loader2, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function DocumentsList() {
  const { documents, privateDocuments, sharedDocuments, loading, error, deleteDocument, refreshDocuments } = useDocuments();
  const { user } = useAuth();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Tab toggle state (for admins only) - persisted per user
  const isAdmin = user?.is_admin || false;
  const userId = user?.user_id || 'guest';

  // Load tab preferences from localStorage
  const getStoredTabPreferences = () => {
    if (typeof window === 'undefined') return { showPrivate: true, showAdmin: true };
    const stored = localStorage.getItem(`document-tabs-${userId}`);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return { showPrivate: true, showAdmin: true };
      }
    }
    return { showPrivate: true, showAdmin: true }; // Default: both active
  };

  const [showPrivate, setShowPrivate] = useState(getStoredTabPreferences().showPrivate);
  const [showAdmin, setShowAdmin] = useState(getStoredTabPreferences().showAdmin);

  // Save tab preferences to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && userId !== 'guest') {
      localStorage.setItem(`document-tabs-${userId}`, JSON.stringify({ showPrivate, showAdmin }));
    }
  }, [showPrivate, showAdmin, userId]);

  // Toggle functions
  const togglePrivateTab = () => setShowPrivate(!showPrivate);
  const toggleAdminTab = () => setShowAdmin(!showAdmin);

  const handleDeleteClick = (id: string, name: string) => {
    setDocumentToDelete({ id, name });
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete || isDeleting) return;

    setIsDeleting(true);
    try {
      await deleteDocument(documentToDelete.id);
      // Only close modal after successful delete
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    } catch (err) {
      console.error('Failed to delete document:', err);
      // Error is already handled in useDocuments hook
      // Keep modal open so user can see the error and try again
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="animate-spin text-accent" size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-3 text-sm text-error bg-error/10 border border-error/20 rounded-lg mx-2">
        ⚠️ {error}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <>
        <div className="px-4 py-8 text-center">
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-2">
            No documents yet
          </p>
          <p className="text-xs text-light-text-tertiary dark:text-dark-text-tertiary mb-4">
            Upload a document to get started
          </p>
          <Button
            onClick={() => setUploadDialogOpen(true)}
            size="sm"
            className="mx-auto"
          >
            <Upload size={18} className="mr-2" />
            Upload Document
          </Button>
        </div>

        <UploadDialog
          isOpen={uploadDialogOpen}
          onClose={() => setUploadDialogOpen(false)}
          onSuccess={refreshDocuments}
        />
      </>
    );
  }

  return (
    <>
      {/* Upload Button + Tab Buttons (for admins) */}
      <div className="px-2 pb-2">
        {isAdmin ? (
          // Admin layout: [Upload Icon][Private][Admin] in same row
          <div className="flex gap-2">
            {/* Upload button - icon only */}
            <Button
              onClick={() => setUploadDialogOpen(true)}
              size="sm"
              variant="outline"
              className="px-3"
              title="Upload Document"
            >
              <Upload size={18} />
            </Button>

            {/* Private tab */}
            <button
              onClick={togglePrivateTab}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                showPrivate
                  ? 'bg-[#E4E4E2] dark:bg-[#2A2A2A] text-light-text dark:text-dark-text'
                  : 'border border-border-primary text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg'
              }`}
            >
              Private
            </button>

            {/* Admin tab */}
            <button
              onClick={toggleAdminTab}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                showAdmin
                  ? 'bg-[#E4E4E2] dark:bg-[#2A2A2A] text-light-text dark:text-dark-text'
                  : 'border border-border-primary text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg'
              }`}
            >
              Admin
            </button>
          </div>
        ) : (
          // Regular user layout: Full width upload button with text
          <Button
            onClick={() => setUploadDialogOpen(true)}
            size="sm"
            variant="outline"
            className="w-full"
          >
            <Upload size={18} className="mr-2" />
            Upload Document
          </Button>
        )}
      </div>

      {/* Private Documents Section */}
      {showPrivate && privateDocuments.length > 0 && (
        <div className="mb-4">
          <div className="px-2 space-y-2">
            <AnimatePresence mode="popLayout">
              {privateDocuments.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onDelete={(id) => handleDeleteClick(id, doc.name)}
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Admin-Shared Documents Section */}
      {isAdmin && showAdmin && sharedDocuments.length > 0 && (
        <div>
          <div className="px-2 space-y-2">
            <AnimatePresence mode="popLayout">
              {sharedDocuments.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onDelete={(id) => handleDeleteClick(id, doc.name)}
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      <DeleteConfirmDialog
        isOpen={deleteDialogOpen}
        documentName={documentToDelete?.name || ''}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        isDeleting={isDeleting}
      />

      <UploadDialog
        isOpen={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onSuccess={refreshDocuments}
      />
    </>
  );
}
