// hooks/useDocuments.ts
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';

interface Document {
  id: string;
  name: string;
  description?: string;
  type?: string;
  size: number;
  status: 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  updated_at?: string;
  metadata: Record<string, unknown>;
}

interface UseDocumentsReturn {
  documents: Document[];
  privateDocuments: Document[];
  sharedDocuments: Document[];
  loading: boolean;
  error: string | null;
  refreshDocuments: () => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
}

export function useDocuments(): UseDocumentsReturn {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [privateDocuments, setPrivateDocuments] = useState<Document[]>([]);
  const [sharedDocuments, setSharedDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeletingDocument, setIsDeletingDocument] = useState(false);
  const { user } = useAuth();

  const getAuthHeader = (): Record<string, string> => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const fetchDocuments = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';
      const response = await fetch(`${apiUrl}/api/documents`, {
        headers: {
          ...getAuthHeader(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data = await response.json();
      const allDocs = data.documents || [];
      setDocuments(allDocs);

      // Separate into private and shared documents
      const userId = user?.user_id;
      const private_docs = allDocs.filter((doc: Document) =>
        doc.metadata?.user_id === userId && doc.metadata?.access_level !== 'admin-shared'
      );
      const shared_docs = allDocs.filter((doc: Document) =>
        doc.metadata?.access_level === 'admin-shared'
      );

      setPrivateDocuments(private_docs);
      setSharedDocuments(shared_docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      console.error('Error fetching documents:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [user?.user_id]);

  const deleteDocument = useCallback(async (documentId: string) => {
    setIsDeletingDocument(true); // Pause auto-refresh during delete
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';
      const response = await fetch(`${apiUrl}/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          ...getAuthHeader(),
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete document');
      }

      // FIXED: Refresh from server instead of optimistic update
      // This prevents UI/state desync issues with the 3-second auto-refresh
      await fetchDocuments(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
      console.error('Error deleting document:', err);
      throw err; // Re-throw so component can handle it
    } finally {
      setIsDeletingDocument(false); // Resume auto-refresh
    }
  }, [fetchDocuments]);

  // Initial fetch
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Auto-refresh every 3 seconds to catch status updates (without showing loading state)
  // PAUSE refresh during delete operations to prevent race conditions
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isDeletingDocument) {
        fetchDocuments(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchDocuments, isDeletingDocument]);

  return {
    documents,
    privateDocuments,
    sharedDocuments,
    loading,
    error,
    refreshDocuments: fetchDocuments,
    deleteDocument,
  };
}
