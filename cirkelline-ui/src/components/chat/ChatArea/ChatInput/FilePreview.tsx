'use client'
import { X, File, Image as ImageIcon, Music, Video } from 'lucide-react'

interface UploadedFile {
  id: string
  file: File
  preview?: string
  type: 'image' | 'audio' | 'video' | 'document'
  size: string
}

interface FilePreviewProps {
  files: UploadedFile[]
  onRemove: (id: string) => void
}

export default function FilePreview({ files, onRemove }: FilePreviewProps) {
  if (files.length === 0) return null

  return (
    <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {files.map(file => (
            <FilePreviewItem
              key={file.id}
              file={file}
              onRemove={onRemove}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function FilePreviewItem({
  file,
  onRemove
}: {
  file: UploadedFile
  onRemove: (id: string) => void
}) {
  const getIcon = () => {
    switch (file.type) {
      case 'image': return <ImageIcon size={20} />
      case 'audio': return <Music size={20} />
      case 'video': return <Video size={20} />
      default: return <File size={20} />
    }
  }

  return (
    <div className="relative flex-shrink-0 group">
      {/* Preview Container */}
      <div className="w-24 h-24 rounded-lg border border-gray-300 dark:border-gray-600 bg-light-surface dark:bg-dark-surface overflow-hidden">
        {file.type === 'image' && file.preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={file.preview}
            alt={file.file.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-1 p-2">
            <div className="text-light-text/60 dark:text-dark-text/60">
              {getIcon()}
            </div>
            <p className="text-xs text-light-text/60 dark:text-dark-text/60 text-center truncate w-full px-1">
              {file.file.name}
            </p>
            <p className="text-xs text-light-text/40 dark:text-dark-text/40">
              {file.size}
            </p>
          </div>
        )}
      </div>

      {/* Remove Button */}
      <button
        onClick={() => onRemove(file.id)}
        className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label="Remove file"
      >
        <X size={14} />
      </button>
    </div>
  )
}
