'use client'

import { useState, useEffect, useCallback } from 'react'
import { Folder, FolderOpen, Lock, Star, RefreshCw } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
  SelectSeparator
} from '@/components/ui/select'
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

interface FolderContextState {
  user_id: string
  current_folder_id: string | null
  current_folder: CKCFolder | null
  recent_folders: string[]
  favorite_folders: string[]
}

interface FolderListResponse {
  folders: CKCFolder[]
  total: number
  categories: Record<string, number>
  current_folder_id: string | null
}

interface FolderSwitcherProps {
  variant?: 'dropdown' | 'compact'
  showFavorites?: boolean
  onFolderChange?: (folder: CKCFolder) => void
}

export default function FolderSwitcher({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  variant = 'dropdown',
  showFavorites = true,
  onFolderChange
}: FolderSwitcherProps) {
  // Note: variant is reserved for future compact mode implementation
  const { selectedEndpoint } = useStore()

  const [folders, setFolders] = useState<CKCFolder[]>([])
  const [currentFolder, setCurrentFolder] = useState<CKCFolder | null>(null)
  const [favorites, setFavorites] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSwitching, setIsSwitching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch folders from API
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
        const data: FolderListResponse = await foldersRes.json()
        setFolders(data.folders)
      }

      if (currentRes.ok) {
        const data: FolderContextState = await currentRes.json()
        setCurrentFolder(data.current_folder)
      }

      if (favoritesRes.ok) {
        const data = await favoritesRes.json()
        setFavorites(data.favorites || [])
      }
    } catch (err) {
      setError('Failed to load folders')
      console.error('FolderSwitcher error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedEndpoint])

  useEffect(() => {
    fetchFolders()
  }, [fetchFolders])

  // Switch folder
  const handleFolderSwitch = async (folderId: string) => {
    if (folderId === currentFolder?.folder_id) return

    try {
      setIsSwitching(true)

      const response = await fetch(APIRoutes.SwitchCKCFolder(selectedEndpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_id: folderId,
          method: 'dropdown'
        })
      })

      if (response.ok) {
        await response.json() // Consume response
        const newFolder = folders.find(f => f.folder_id === folderId) || null
        setCurrentFolder(newFolder)
        onFolderChange?.(newFolder!)
      }
    } catch (err) {
      console.error('Switch folder error:', err)
    } finally {
      setIsSwitching(false)
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

  // Group folders by category
  const groupedFolders = folders.reduce((acc, folder) => {
    const category = folder.category
    if (!acc[category]) acc[category] = []
    acc[category].push(folder)
    return acc
  }, {} as Record<string, CKCFolder[]>)

  const categoryLabels: Record<string, string> = {
    ckc_components: 'CKC Components (Frozen)',
    cirkelline_ckc: 'Cirkelline CKC (Active)',
    custom: 'Custom Folders'
  }

  const categoryOrder = ['cirkelline_ckc', 'ckc_components', 'custom']

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-red-500">
        <span>{error}</span>
        <button onClick={fetchFolders} className="hover:text-red-400">
          <RefreshCw size={14} />
        </button>
      </div>
    )
  }

  return (
    <div className="w-full">
      <Select
        value={currentFolder?.folder_id || ''}
        onValueChange={handleFolderSwitch}
        disabled={isLoading || isSwitching}
      >
        <SelectTrigger className="w-full bg-light-surface dark:bg-dark-surface border-border-primary">
          <div className="flex items-center gap-2">
            {isLoading ? (
              <RefreshCw size={16} className="animate-spin text-light-text-secondary" />
            ) : currentFolder?.frozen ? (
              <Lock size={16} className="text-amber-500" />
            ) : (
              <FolderOpen size={16} className="text-accent" />
            )}
            <SelectValue placeholder="Select CKC Folder">
              {currentFolder?.display_name || 'Select Folder'}
            </SelectValue>
          </div>
        </SelectTrigger>

        <SelectContent className="max-h-[400px]">
          {/* Favorites section */}
          {showFavorites && favorites.length > 0 && (
            <>
              <SelectGroup>
                <SelectLabel className="flex items-center gap-2 text-amber-500">
                  <Star size={14} fill="currentColor" />
                  Favorites
                </SelectLabel>
                {folders
                  .filter(f => favorites.includes(f.folder_id))
                  .map(folder => (
                    <FolderSelectItem
                      key={`fav-${folder.folder_id}`}
                      folder={folder}
                      isFavorite={true}
                      onToggleFavorite={handleToggleFavorite}
                    />
                  ))}
              </SelectGroup>
              <SelectSeparator />
            </>
          )}

          {/* All folders grouped by category */}
          {categoryOrder.map((category, idx) => {
            const categoryFolders = groupedFolders[category]
            if (!categoryFolders?.length) return null

            return (
              <SelectGroup key={category}>
                {idx > 0 && <SelectSeparator />}
                <SelectLabel className="flex items-center gap-2">
                  {category === 'ckc_components' && <Lock size={14} className="text-amber-500" />}
                  {category === 'cirkelline_ckc' && <FolderOpen size={14} className="text-accent" />}
                  {category === 'custom' && <Folder size={14} className="text-purple-500" />}
                  {categoryLabels[category]}
                </SelectLabel>
                {categoryFolders.map(folder => (
                  <FolderSelectItem
                    key={folder.folder_id}
                    folder={folder}
                    isFavorite={favorites.includes(folder.folder_id)}
                    onToggleFavorite={handleToggleFavorite}
                  />
                ))}
              </SelectGroup>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}

// Folder item component
function FolderSelectItem({
  folder,
  isFavorite,
  onToggleFavorite
}: {
  folder: CKCFolder
  isFavorite: boolean
  onToggleFavorite: (id: string, e: React.MouseEvent) => void
}) {
  return (
    <SelectItem value={folder.folder_id} className="flex items-center justify-between">
      <div className="flex items-center gap-2 flex-1">
        {folder.frozen ? (
          <Lock size={14} className="text-amber-500 flex-shrink-0" />
        ) : (
          <Folder size={14} className="text-accent flex-shrink-0" />
        )}
        <span className="truncate">{folder.display_name}</span>
        <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary ml-auto">
          {folder.files_count} files
        </span>
      </div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={(e) => onToggleFavorite(folder.folder_id, e)}
              className="ml-2 p-1 hover:bg-accent/10 rounded"
            >
              <Star
                size={12}
                className={isFavorite ? 'text-amber-500 fill-amber-500' : 'text-light-text-secondary'}
              />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>{isFavorite ? 'Remove from favorites' : 'Add to favorites'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </SelectItem>
  )
}
