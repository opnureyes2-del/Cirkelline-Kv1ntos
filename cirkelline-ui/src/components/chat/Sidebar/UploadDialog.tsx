// components/chat/Sidebar/UploadDialog.tsx
'use client'
import React, { useState, useRef } from 'react';
import { Upload, Loader2, X, FileText, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';

interface UploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function UploadDialog({ isOpen, onClose, onSuccess }: UploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isShared, setIsShared] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  const isAdmin = user?.is_admin === true;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_shared', isShared.toString());

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';
      const response = await fetch(`${apiUrl}/api/knowledge/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Upload failed');
      }

      const data = await response.json();
      toast.success(data.message || 'File uploaded successfully!');

      // Reset and close
      setFile(null);
      setIsShared(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Upload error:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setFile(null);
    setIsShared(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary">
          <h2 className="text-lg font-heading font-semibold text-light-text dark:text-dark-text">
            Upload Document
          </h2>
          <button
            onClick={handleCancel}
            className="text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* File Input */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.txt,.doc,.docx,.csv,.json,.md"
            />

            {file ? (
              <div className="flex items-center gap-3 p-4 bg-accent/5 border border-accent/20 rounded-lg">
                <FileText className="text-accent" size={24} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={() => {
                    setFile(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  className="text-light-text-secondary hover:text-error transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full p-8 border-2 border-dashed border-border-primary hover:border-accent rounded-lg transition-colors flex flex-col items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary hover:text-accent"
              >
                <Upload size={32} />
                <p className="text-sm font-medium">Click to select a file</p>
                <p className="text-xs">PDF, TXT, DOC, DOCX, CSV, JSON, MD</p>
              </button>
            )}
          </div>

          {/* Share Checkbox - Only for Admins */}
          {isAdmin && (
            <div className="flex items-start gap-3 p-4 bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-lg">
              <Checkbox
                id="share-doc"
                checked={isShared}
                onCheckedChange={(checked) => setIsShared(checked === true)}
                className="mt-0.5"
              />
              <div className="flex-1">
                <Label
                  htmlFor="share-doc"
                  className="text-sm font-medium text-light-text dark:text-dark-text cursor-pointer flex items-center gap-2"
                >
                  <Share2 size={18} className="text-accent" />
                  Share with all admins
                </Label>
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
                  Make this document visible to all admin users
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-border-primary">
          <Button
            onClick={handleCancel}
            variant="ghost"
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="min-w-[100px]"
          >
            {uploading ? (
              <>
                <Loader2 className="animate-spin mr-2" size={18} />
                Uploading...
              </>
            ) : (
              'Upload'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
