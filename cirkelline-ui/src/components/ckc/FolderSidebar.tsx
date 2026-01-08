'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Folder,
  FolderOpen,
  Lock,
  Star,
  ChevronRight,
  RefreshCw,
  FileCode,
  Settings,
  Database,
  Cpu,
  Globe,
  Shield,
  Palette,
  Terminal
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { APIRoutes } from '@/api/routes'
import { useStore } from '@/store'

// Types matching backend API
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

interface FolderSidebarProps {
  onFolderSelect?: (folder: CKCFolder) => void
  compact?: boolean
}

// Icon mapping for folder types
const folderIcons: Record<string, typeof Folder> = {
  mastermind: Cpu,
  tegne_enhed: Palette,
  kommandant: Shield,
  infrastructure: Database,
  integrations: Globe,
  web3: Globe,
  connectors: Settings,
  api: Terminal,
  aws: Database,
  'legal-kommandant': Shield,
  'web3-kommandant': Globe,
  'research-team': FileCode,
  'law-team': Shield,
  kv1nt: Terminal,
}

export default function FolderSidebar({ onFolderSelect, compact = false }: FolderSidebarProps) {
  const { selectedEndpoint } = useStore()

  const [folders, setFolders] = useState<CKCFolder[]>([])
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [favorites, setFavorites] = useState<string[]>([])
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    cirkelline_ckc: true,
    ckc_components: false,
    custom: false
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch folders
  const fetchFolders = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const [foldersRes, currentRes, favoritesRes] = await Promise.all([
        fetch(APIRoutes.GetCKCFolders(selectedEndpoint)),
        fetch(APIRoutes.GetCKCCurrentFolder(selectedEndpoint)),
        fetch(APIRoutes.GetCKCFavorites(selectedEndpoint))
      ])

      if (foldersRes.ok) {
        const data = await foldersRes.json()
        setFolders(data.folders)
      }

      if (currentRes.ok) {
        const data = await currentRes.json()
        setCurrentFolderId(data.current_folder_id)
      }

      if (favoritesRes.ok) {
        const data = await favoritesRes.json()
        setFavorites(data.favorites || [])
      }
    } catch (err) {
      setError('Failed to load folders')
      console.error('FolderSidebar error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedEndpoint])

  useEffect(() => {
    fetchFolders()
  }, [fetchFolders])

  // Select folder
  const handleFolderClick = async (folder: CKCFolder) => {
    try {
      const response = await fetch(APIRoutes.SwitchCKCFolder(selectedEndpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_id: folder.folder_id,
          method: 'sidebar'
        })
      })

      if (response.ok) {
        setCurrentFolderId(folder.folder_id)
        onFolderSelect?.(folder)
      }
    } catch (err) {
      console.error('Select folder error:', err)
    }
  }

  // Toggle favorite
  const handleToggleFavorite = async (folderId: string, e: React.MouseEvent) => {
    e.stopPropagation()

    try {
      const response = await fetch(APIRoutes.ToggleCKCFavorite(selectedEndpoint, folderId), {
        method: 'POST'
      })

      if (response.ok) {
        setFavorites(prev =>
          prev.includes(folderId)
            ? prev.filter(id => id !== folderId)
            : [...prev, folderId]
        )
      }
    } catch (err) {
      console.error('Toggle favorite error:', err)
    }
  }

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  // Group folders by category
  const groupedFolders = folders.reduce((acc, folder) => {
    const category = folder.category
    if (!acc[category]) acc[category] = []
    acc[category].push(folder)
    return acc
  }, {} as Record<string, CKCFolder[]>)

  const categoryConfig = {
    cirkelline_ckc: {
      label: 'Cirkelline CKC',
      icon: FolderOpen,
      color: 'text-accent'
    },
    ckc_components: {
      label: 'CKC Components',
      icon: Lock,
      color: 'text-amber-500'
    },
    custom: {
      label: 'Custom Folders',
      icon: Folder,
      color: 'text-purple-500'
    }
  }

  const categoryOrder = ['cirkelline_ckc', 'ckc_components', 'custom']

  if (error) {
    return (
      <div className="p-4 text-sm text-red-500 flex items-center gap-2">
        <span>{error}</span>
        <button onClick={fetchFolders} className="hover:text-red-400">
          <RefreshCw size={14} />
        </button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-light-text-secondary" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border-primary">
        <span className="text-sm font-medium text-light-text dark:text-dark-text">
          CKC Folders
        </span>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={fetchFolders}
                className="p-1 rounded hover:bg-accent/10 transition-colors"
              >
                <RefreshCw size={14} className="text-light-text-secondary" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Refresh folders</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Favorites section */}
      {favorites.length > 0 && (
        <div className="p-2 border-b border-border-primary">
          <div className="flex items-center gap-2 px-2 py-1 text-xs font-medium text-amber-500">
            <Star size={12} fill="currentColor" />
            Favorites
          </div>
          {folders
            .filter(f => favorites.includes(f.folder_id))
            .map(folder => (
              <FolderItem
                key={`fav-${folder.folder_id}`}
                folder={folder}
                isSelected={folder.folder_id === currentFolderId}
                isFavorite={true}
                onClick={() => handleFolderClick(folder)}
                onToggleFavorite={handleToggleFavorite}
                compact={compact}
              />
            ))}
        </div>
      )}

      {/* Folder tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {categoryOrder.map(category => {
          const categoryFolders = groupedFolders[category]
          if (!categoryFolders?.length) return null

          const config = categoryConfig[category as keyof typeof categoryConfig]
          const isExpanded = expandedCategories[category]
          const CategoryIcon = config.icon

          return (
            <div key={category} className="mb-2">
              {/* Category header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
              >
                <motion.div
                  animate={{ rotate: isExpanded ? 90 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronRight size={14} className="text-light-text-secondary" />
                </motion.div>
                <CategoryIcon size={14} className={config.color} />
                <span className="text-xs font-medium text-light-text dark:text-dark-text">
                  {config.label}
                </span>
                <span className="text-xs text-light-text-secondary ml-auto">
                  {categoryFolders.length}
                </span>
              </button>

              {/* Category folders */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="ml-4 mt-1 space-y-0.5">
                      {categoryFolders.map(folder => (
                        <FolderItem
                          key={folder.folder_id}
                          folder={folder}
                          isSelected={folder.folder_id === currentFolderId}
                          isFavorite={favorites.includes(folder.folder_id)}
                          onClick={() => handleFolderClick(folder)}
                          onToggleFavorite={handleToggleFavorite}
                          compact={compact}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>

      {/* Footer with current selection */}
      {currentFolderId && (
        <div className="p-3 border-t border-border-primary bg-accent/5">
          <div className="text-xs text-light-text-secondary">Current:</div>
          <div className="text-sm font-medium text-accent truncate">
            {folders.find(f => f.folder_id === currentFolderId)?.display_name}
          </div>
        </div>
      )}
    </div>
  )
}

// Folder item component
function FolderItem({
  folder,
  isSelected,
  isFavorite,
  onClick,
  onToggleFavorite,
  compact
}: {
  folder: CKCFolder
  isSelected: boolean
  isFavorite: boolean
  onClick: () => void
  onToggleFavorite: (id: string, e: React.MouseEvent) => void
  compact: boolean
}) {
  const IconComponent = folderIcons[folder.folder_id] || Folder

  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-2 px-2 py-1.5 rounded-lg transition-all
        ${isSelected
          ? 'bg-accent/10 text-accent border-l-2 border-accent'
          : 'text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg'
        }
      `}
    >
      {folder.frozen ? (
        <Lock size={14} className="text-amber-500 flex-shrink-0" />
      ) : (
        <IconComponent size={14} className={isSelected ? 'text-accent' : 'text-light-text-secondary'} />
      )}

      <span className={`text-sm truncate ${compact ? 'max-w-[100px]' : 'flex-1'}`}>
        {folder.display_name}
      </span>

      {!compact && (
        <>
          <span className="text-xs text-light-text-secondary ml-auto">
            {folder.files_count}
          </span>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={(e) => onToggleFavorite(folder.folder_id, e)}
                  className="p-0.5 hover:bg-accent/10 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Star
                    size={12}
                    className={isFavorite ? 'text-amber-500 fill-amber-500' : 'text-light-text-secondary'}
                  />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right">
                {isFavorite ? 'Remove from favorites' : 'Add to favorites'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </>
      )}
    </button>
  )
}
