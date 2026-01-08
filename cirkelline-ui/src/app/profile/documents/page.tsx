'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ArrowUpDown, ChevronLeft, ChevronRight, FileText, Clock, Upload, X, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'

interface Document {
  id: string
  name: string
  content?: string
  metadata?: {
    user_id?: string
    file_type?: string
    file_size?: number
    upload_date?: string
    access_level?: string
    [key: string]: string | number | undefined
  }
  created_at: string
  updated_at?: string
}

interface DocumentsResponse {
  success: boolean
  count: number
  documents: Document[]
}

export default function DocumentsPage() {
  // Use environment variable for API endpoint
  const endpoint = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // State
  const [documents, setDocuments] = useState<Document[]>([])
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(18) // 18 documents per page

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'created_at' | 'name'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [accessLevelFilter, setAccessLevelFilter] = useState<'all' | 'private' | 'admin-shared'>('all')

  // Modal
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Upload modal
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [shareWithAdmins, setShareWithAdmins] = useState(false)

  // Load documents
  const loadDocuments = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')

      if (!token) {
        setDocuments([])
        setLoading(false)
        return
      }

      const response = await fetch(`${endpoint}/api/knowledge/documents`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        // If endpoint doesn't exist or returns error, just show empty state
        setDocuments([])
        setLoading(false)
        return
      }

      const data: DocumentsResponse = await response.json()
      setDocuments(data.documents || [])
    } catch {
      // Silently handle error and show empty state
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [endpoint])

  // Load on mount
  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  // Filter and sort documents
  useEffect(() => {
    let filtered = [...documents]

    // Apply access level filter
    if (accessLevelFilter !== 'all') {
      filtered = filtered.filter(doc =>
        doc.metadata?.access_level === accessLevelFilter
      )
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(doc =>
        doc.name.toLowerCase().includes(query) ||
        (doc.content && doc.content.toLowerCase().includes(query))
      )
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'created_at') {
        // Handle Unix timestamps (seconds) - multiply by 1000 for JavaScript Date
        const timestampA = typeof a.created_at === 'number' ? a.created_at * 1000 : a.created_at
        const timestampB = typeof b.created_at === 'number' ? b.created_at * 1000 : b.created_at
        const dateA = new Date(timestampA).getTime()
        const dateB = new Date(timestampB).getTime()
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB
      } else {
        // Sort by name
        const comparison = a.name.localeCompare(b.name)
        return sortOrder === 'desc' ? -comparison : comparison
      }
    })

    setFilteredDocuments(filtered)
    setCurrentPage(1) // Reset to first page when filters change
  }, [documents, searchQuery, sortBy, sortOrder, accessLevelFilter])

  // Pagination
  const totalPages = Math.ceil(filteredDocuments.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedDocuments = filteredDocuments.slice(startIndex, endIndex)

  // Modal handlers
  const handleOpenDocument = (doc: Document) => {
    setSelectedDocument(doc)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedDocument(null)
  }

  // Format file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Truncate text
  const truncateText = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  // Upload handlers
  const handleUploadClick = () => {
    setIsUploadModalOpen(true)
  }

  const handleCloseUploadModal = () => {
    setIsUploadModalOpen(false)
    setUploadFile(null)
    setShareWithAdmins(false)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadFile(file)
    }
  }

  const handleUpload = async () => {
    if (!uploadFile) return

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('is_shared', shareWithAdmins.toString())

      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Please log in to upload documents')
        return
      }

      const response = await fetch(`${endpoint}/api/knowledge/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      toast.success(data.message || 'File uploaded successfully!')

      // Reload documents
      await loadDocuments()

      // Close modal
      handleCloseUploadModal()
    } catch (error) {
      toast.error('Failed to upload file. Please try again.')
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading mb-2">
            Documents
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {loading ? 'Loading...' : `${filteredDocuments.length} document${filteredDocuments.length !== 1 ? 's' : ''}`}
          </p>
        </motion.div>

        {/* Controls Bar */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-6 flex flex-col sm:flex-row gap-4"
        >
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary" size={18} />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [newSortBy, newSortOrder] = e.target.value.split('-') as [typeof sortBy, typeof sortOrder]
                setSortBy(newSortBy)
                setSortOrder(newSortOrder)
              }}
              className="appearance-none pl-10 pr-10 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all cursor-pointer"
            >
              <option value="created_at-desc">Recently Added</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="name-asc">Name A-Z</option>
              <option value="name-desc">Name Z-A</option>
            </select>
            <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary pointer-events-none" size={18} />
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUploadClick}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg
                     bg-accent hover:bg-accent/90
                     text-white font-medium
                     transition-all"
          >
            <Upload size={18} />
            <span>Upload</span>
          </button>
        </motion.div>

        {/* Filter Tabs */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15 }}
          className="mb-6 flex gap-2"
        >
          <button
            onClick={() => setAccessLevelFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-all
                     ${accessLevelFilter === 'all'
                       ? 'bg-accent text-white'
                       : 'bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary hover:border-accent/50'
                     }`}
          >
            All Documents
          </button>
          <button
            onClick={() => setAccessLevelFilter('private')}
            className={`px-4 py-2 rounded-lg font-medium transition-all
                     ${accessLevelFilter === 'private'
                       ? 'bg-accent text-white'
                       : 'bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary hover:border-accent/50'
                     }`}
          >
            Private
          </button>
          <button
            onClick={() => setAccessLevelFilter('admin-shared')}
            className={`px-4 py-2 rounded-lg font-medium transition-all
                     ${accessLevelFilter === 'admin-shared'
                       ? 'bg-accent text-white'
                       : 'bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary hover:border-accent/50'
                     }`}
          >
            Admin Shared
          </button>
        </motion.div>

        {/* Documents List */}
        {loading ? (
          // Loading Skeletons
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-32 rounded-lg bg-light-surface/50 dark:bg-dark-surface/50
                         border border-border-primary animate-pulse"
              />
            ))}
          </div>
        ) : paginatedDocuments.length === 0 ? (
          // Empty State
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16"
          >
            <FileText className="mx-auto mb-4 text-light-text-secondary dark:text-dark-text-secondary" size={64} />
            <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
              No documents found
            </h3>
            <p className="text-light-text-secondary dark:text-dark-text-secondary mb-6">
              {searchQuery ? 'Try adjusting your search' : 'Upload documents to your knowledge base'}
            </p>
          </motion.div>
        ) : (
          // Documents List
          <div className="space-y-3 mb-8">
            {paginatedDocuments.map((doc, index) => {
              // Handle Unix timestamp (seconds) - multiply by 1000 for JavaScript Date
              const timestamp = typeof doc.created_at === 'number' ? doc.created_at * 1000 : doc.created_at
              const createdAt = formatDistanceToNow(new Date(timestamp), { addSuffix: true })
              const fileType = doc.metadata?.file_type || 'Unknown'
              const fileSize = formatFileSize(doc.metadata?.file_size)

              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.2 }}
                  onClick={() => handleOpenDocument(doc)}
                  className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary
                           overflow-hidden hover:border-accent/50 transition-all cursor-pointer
                           hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary"
                >
                  <div className="p-4">
                    {/* Document Name */}
                    <div className="mb-3 flex items-start gap-3">
                      <FileText className="text-accent flex-shrink-0 mt-1" size={20} />
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-light-text dark:text-dark-text truncate mb-1">
                          {doc.name}
                        </h3>
                        {doc.content && (
                          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary leading-relaxed">
                            {truncateText(doc.content)}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center gap-3 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {createdAt}
                      </span>
                      <span>{fileType}</span>
                      <span>{fileSize}</span>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {!loading && paginatedDocuments.length > 0 && totalPages > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="flex items-center justify-center gap-2"
          >
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronLeft size={20} />
            </button>

            <span className="px-4 py-2 text-sm text-light-text dark:text-dark-text">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronRight size={20} />
            </button>
          </motion.div>
        )}
      </div>

      {/* Document Detail Modal */}
      <AnimatePresence>
        {isModalOpen && selectedDocument && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={handleCloseModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary
                       max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl"
            >
              {/* Modal Header */}
              <div className="sticky top-0 bg-light-surface dark:bg-dark-surface border-b border-border-primary p-6 z-10">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-light-text dark:text-dark-text mb-2">
                      {selectedDocument.name}
                    </h2>
                    <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      Added {formatDistanceToNow(new Date(typeof selectedDocument.created_at === 'number' ? selectedDocument.created_at * 1000 : selectedDocument.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  <button
                    onClick={handleCloseModal}
                    className="ml-4 p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg
                             text-light-text-secondary dark:text-dark-text-secondary
                             hover:text-light-text dark:hover:text-dark-text transition-all"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Document Content Preview */}
                {selectedDocument.content && (
                  <div>
                    <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-2">
                      Content Preview
                    </h3>
                    <p className="text-light-text dark:text-dark-text leading-relaxed whitespace-pre-wrap">
                      {selectedDocument.content}
                    </p>
                  </div>
                )}

                {/* Metadata */}
                <div className="pt-4 border-t border-border-primary">
                  <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-3">
                    Document Information
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-light-text-secondary dark:text-dark-text-secondary">File Type:</span>
                      <span className="text-light-text dark:text-dark-text">
                        {selectedDocument.metadata?.file_type || 'Unknown'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-light-text-secondary dark:text-dark-text-secondary">File Size:</span>
                      <span className="text-light-text dark:text-dark-text">
                        {formatFileSize(selectedDocument.metadata?.file_size)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-light-text-secondary dark:text-dark-text-secondary">Document ID:</span>
                      <span className="text-light-text dark:text-dark-text font-mono text-xs">
                        {selectedDocument.id}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 bg-light-surface dark:bg-dark-surface border-t border-border-primary p-6">
                <button
                  onClick={handleCloseModal}
                  className="w-full px-4 py-2.5 rounded-lg
                           bg-accent hover:bg-accent/90
                           text-white font-medium
                           transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Modal */}
      <AnimatePresence>
        {isUploadModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={handleCloseUploadModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary
                       max-w-md w-full shadow-2xl"
            >
              {/* Modal Header */}
              <div className="border-b border-border-primary p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-light-text dark:text-dark-text">
                    Upload Document
                  </h2>
                  <button
                    onClick={handleCloseUploadModal}
                    className="p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg
                             text-light-text-secondary dark:text-dark-text-secondary
                             hover:text-light-text dark:hover:text-dark-text transition-all"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-4">
                {/* File Input */}
                <div>
                  <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                    Select File
                  </label>
                  <input
                    type="file"
                    onChange={handleFileSelect}
                    accept=".pdf,.txt,.doc,.docx,.csv,.json"
                    className="w-full px-4 py-2.5 rounded-lg
                             bg-light-bg dark:bg-dark-bg
                             border border-border-primary
                             text-light-text dark:text-dark-text
                             file:mr-4 file:py-2 file:px-4
                             file:rounded-lg file:border-0
                             file:bg-accent file:text-white
                             file:cursor-pointer
                             hover:file:bg-accent/90
                             focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  {uploadFile && (
                    <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      Selected: {uploadFile.name}
                    </p>
                  )}
                </div>

                {/* Share with Admins Checkbox */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="shareWithAdmins"
                    checked={shareWithAdmins}
                    onChange={(e) => setShareWithAdmins(e.target.checked)}
                    className="w-4 h-4 rounded border-border-primary
                             bg-light-surface dark:bg-dark-surface
                             text-accent focus:ring-accent"
                  />
                  <label
                    htmlFor="shareWithAdmins"
                    className="text-sm text-light-text dark:text-dark-text cursor-pointer"
                  >
                    Share with all admins
                  </label>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="border-t border-border-primary p-6 flex gap-3">
                <button
                  onClick={handleCloseUploadModal}
                  disabled={isUploading}
                  className="flex-1 px-4 py-2.5 rounded-lg
                           bg-light-bg dark:bg-dark-bg
                           text-light-text dark:text-dark-text
                           border border-border-primary
                           hover:border-accent/50
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!uploadFile || isUploading}
                  className="flex-1 px-4 py-2.5 rounded-lg
                           bg-accent hover:bg-accent/90
                           text-white font-medium
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all
                           flex items-center justify-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={18} />
                      <span>Upload</span>
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
