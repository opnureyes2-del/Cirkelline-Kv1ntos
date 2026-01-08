'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  FolderOpen,
  Folder,
  Lock,
  FileCode,
  RefreshCw,
  Search,
  Filter,
  ChevronRight,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { FolderSidebar } from '@/components/ckc'
import { APIRoutes } from '@/api/routes'
import { useStore } from '@/store'

interface CKCFolder {
  folder_id: string
  name: string
  display_name: string
  path: string
  category: 'ckc_components' | 'cirkelline_ckc' | 'custom'
  status: 'active' | 'frozen' | 'development'
  frozen: boolean
  files_count: number
  components_count: number
}

interface FolderContents {
  files: string[]
  subfolders: string[]
  total_files: number
}

interface FolderStatus {
  total_folders: number
  categories: Record<string, number>
  frozen_count: number
  active_count: number
  current_folder_id: string | null
  last_switch: string | null
}

export default function CKCFoldersPage() {
  const { selectedEndpoint } = useStore()

  const [folders, setFolders] = useState<CKCFolder[]>([])
  const [selectedFolder, setSelectedFolder] = useState<CKCFolder | null>(null)
  const [folderContents, setFolderContents] = useState<FolderContents | null>(null)
  const [status, setStatus] = useState<FolderStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [contentsLoading, setContentsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // Fetch initial data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const [foldersRes, statusRes, currentRes] = await Promise.all([
        fetch(APIRoutes.GetCKCFolders(selectedEndpoint)),
        fetch(APIRoutes.GetCKCStatus(selectedEndpoint)),
        fetch(APIRoutes.GetCKCCurrentFolder(selectedEndpoint))
      ])

      if (foldersRes.ok) {
        const data = await foldersRes.json()
        setFolders(data.folders)
      }

      if (statusRes.ok) {
        const data = await statusRes.json()
        setStatus(data)
      }

      if (currentRes.ok) {
        const data = await currentRes.json()
        if (data.current_folder) {
          setSelectedFolder(data.current_folder)
          fetchFolderContents(data.current_folder.folder_id)
        }
      }
    } catch (err) {
      setError('Failed to load CKC folders')
      console.error('CKC Page error:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedEndpoint])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Fetch folder contents
  const fetchFolderContents = async (folderId: string) => {
    try {
      setContentsLoading(true)
      const response = await fetch(APIRoutes.GetCKCFolderContents(selectedEndpoint, folderId))
      if (response.ok) {
        const data = await response.json()
        setFolderContents(data)
      }
    } catch (err) {
      console.error('Fetch contents error:', err)
    } finally {
      setContentsLoading(false)
    }
  }

  // Handle folder selection from sidebar
  const handleFolderSelect = (folder: CKCFolder) => {
    setSelectedFolder(folder)
    fetchFolderContents(folder.folder_id)
  }

  // Filter folders
  const filteredFolders = folders.filter(folder => {
    const matchesSearch = folder.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         folder.folder_id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = categoryFilter === 'all' || folder.category === categoryFilter
    return matchesSearch && matchesCategory
  })

  const categoryLabels: Record<string, string> = {
    ckc_components: 'CKC Components',
    cirkelline_ckc: 'Cirkelline CKC',
    custom: 'Custom'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw size={40} className="animate-spin text-accent mx-auto" />
          <p className="mt-4 text-light-text-secondary dark:text-dark-text-secondary">Loading CKC Folders...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle size={40} className="text-red-500 mx-auto" />
          <p className="mt-4 text-red-500">{error}</p>
          <button
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Left Panel - Folder Tree */}
      <div className="w-72 border-r border-border-primary bg-light-surface dark:bg-dark-surface flex-shrink-0">
        <FolderSidebar onFolderSelect={handleFolderSelect} />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-heading font-semibold text-light-text dark:text-dark-text flex items-center gap-3">
                <FolderOpen size={32} className="text-accent" />
                CKC Folder Management
              </h1>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                Navigate and manage CKC folder contexts for Super Admin operations
              </p>
            </div>
            <button
              onClick={fetchData}
              className="p-2 rounded-lg hover:bg-accent/10 transition-colors"
            >
              <RefreshCw size={20} className="text-light-text-secondary" />
            </button>
          </div>
        </motion.div>

        {/* Status Cards */}
        {status && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
          >
            <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-4 border border-border-primary">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-light-text-secondary">Total Folders</p>
                <Folder size={18} className="text-accent" />
              </div>
              <p className="text-2xl font-semibold text-light-text dark:text-dark-text">
                {status.total_folders}
              </p>
            </div>

            <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-4 border border-border-primary">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-light-text-secondary">Active</p>
                <FolderOpen size={18} className="text-green-500" />
              </div>
              <p className="text-2xl font-semibold text-green-500">
                {status.active_count}
              </p>
            </div>

            <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-4 border border-border-primary">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-light-text-secondary">Frozen</p>
                <Lock size={18} className="text-amber-500" />
              </div>
              <p className="text-2xl font-semibold text-amber-500">
                {status.frozen_count}
              </p>
            </div>

            <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-4 border border-border-primary">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-light-text-secondary">Current</p>
                <CheckCircle size={18} className="text-accent" />
              </div>
              <p className="text-lg font-semibold text-accent truncate">
                {selectedFolder?.display_name || 'None'}
              </p>
            </div>
          </motion.div>
        )}

        {/* Search and Filter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex gap-4 mb-6"
        >
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary" />
            <input
              type="text"
              placeholder="Search folders..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-light-text-secondary" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="all">All Categories</option>
              <option value="cirkelline_ckc">Cirkelline CKC</option>
              <option value="ckc_components">CKC Components</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </motion.div>

        {/* Selected Folder Details */}
        {selectedFolder && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary mb-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {selectedFolder.frozen ? (
                  <Lock size={24} className="text-amber-500" />
                ) : (
                  <FolderOpen size={24} className="text-accent" />
                )}
                <div>
                  <h2 className="text-xl font-semibold text-light-text dark:text-dark-text">
                    {selectedFolder.display_name}
                  </h2>
                  <p className="text-sm text-light-text-secondary">
                    {selectedFolder.path}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  selectedFolder.frozen
                    ? 'bg-amber-500/10 text-amber-500'
                    : 'bg-green-500/10 text-green-500'
                }`}>
                  {selectedFolder.frozen ? 'Frozen' : 'Active'}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent">
                  {categoryLabels[selectedFolder.category]}
                </span>
              </div>
            </div>

            {/* Folder Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="p-3 rounded-lg bg-light-bg dark:bg-dark-bg">
                <p className="text-xs text-light-text-secondary mb-1">Files</p>
                <p className="text-lg font-semibold text-light-text dark:text-dark-text">
                  {selectedFolder.files_count}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-light-bg dark:bg-dark-bg">
                <p className="text-xs text-light-text-secondary mb-1">Components</p>
                <p className="text-lg font-semibold text-light-text dark:text-dark-text">
                  {selectedFolder.components_count}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-light-bg dark:bg-dark-bg">
                <p className="text-xs text-light-text-secondary mb-1">Status</p>
                <p className="text-lg font-semibold text-light-text dark:text-dark-text capitalize">
                  {selectedFolder.status}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-light-bg dark:bg-dark-bg">
                <p className="text-xs text-light-text-secondary mb-1">Category</p>
                <p className="text-lg font-semibold text-light-text dark:text-dark-text">
                  {categoryLabels[selectedFolder.category]}
                </p>
              </div>
            </div>

            {/* Folder Contents */}
            {contentsLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw size={24} className="animate-spin text-accent" />
              </div>
            ) : folderContents && (
              <div>
                <h3 className="text-sm font-medium text-light-text dark:text-dark-text mb-3">
                  Contents ({folderContents.total_files} files)
                </h3>
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {folderContents.subfolders.map(subfolder => (
                    <div
                      key={subfolder}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg"
                    >
                      <Folder size={16} className="text-accent" />
                      <span className="text-sm text-light-text dark:text-dark-text">{subfolder}</span>
                    </div>
                  ))}
                  {folderContents.files.slice(0, 20).map(file => (
                    <div
                      key={file}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg"
                    >
                      <FileCode size={16} className="text-light-text-secondary" />
                      <span className="text-sm text-light-text dark:text-dark-text">{file}</span>
                    </div>
                  ))}
                  {folderContents.files.length > 20 && (
                    <p className="text-xs text-light-text-secondary text-center py-2">
                      + {folderContents.files.length - 20} more files
                    </p>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* All Folders Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4">
            All Folders ({filteredFolders.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFolders.map(folder => (
              <button
                key={folder.folder_id}
                onClick={() => handleFolderSelect(folder)}
                className={`
                  text-left p-4 rounded-xl border transition-all
                  ${selectedFolder?.folder_id === folder.folder_id
                    ? 'border-accent bg-accent/5'
                    : 'border-border-primary bg-light-surface dark:bg-dark-surface hover:border-accent/50'
                  }
                `}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {folder.frozen ? (
                      <Lock size={18} className="text-amber-500" />
                    ) : (
                      <Folder size={18} className="text-accent" />
                    )}
                    <span className="font-medium text-light-text dark:text-dark-text">
                      {folder.display_name}
                    </span>
                  </div>
                  <ChevronRight size={16} className="text-light-text-secondary" />
                </div>
                <p className="text-xs text-light-text-secondary truncate mb-2">
                  {folder.path}
                </p>
                <div className="flex items-center gap-3 text-xs text-light-text-secondary">
                  <span>{folder.files_count} files</span>
                  <span className={`px-2 py-0.5 rounded ${
                    folder.frozen ? 'bg-amber-500/10 text-amber-500' : 'bg-green-500/10 text-green-500'
                  }`}>
                    {folder.frozen ? 'Frozen' : 'Active'}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
