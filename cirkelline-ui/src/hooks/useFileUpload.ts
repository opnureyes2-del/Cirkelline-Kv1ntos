'use client'
import { useState } from 'react'

interface UploadedFile {
  id: string
  file: File
  preview?: string
  type: 'image' | 'audio' | 'video' | 'document'
  size: string
}

export function useFileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])

  const addFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles)

    const processedFiles: UploadedFile[] = fileArray.map(file => {
      const id = crypto.randomUUID()
      const type = getFileType(file)
      const size = formatFileSize(file.size)

      // Create preview for images
      let preview: string | undefined
      if (type === 'image') {
        preview = URL.createObjectURL(file)
      }

      return { id, file, preview, type, size }
    })

    setFiles(prev => [...prev, ...processedFiles])
  }

  const removeFile = (id: string) => {
    setFiles(prev => {
      const fileToRemove = prev.find(f => f.id === id)
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview)
      }
      return prev.filter(f => f.id !== id)
    })
  }

  const clearFiles = () => {
    files.forEach(f => {
      if (f.preview) URL.revokeObjectURL(f.preview)
    })
    setFiles([])
  }

  return { files, addFiles, removeFile, clearFiles }
}

// Helper functions
function getFileType(file: File): 'image' | 'audio' | 'video' | 'document' {
  if (file.type.startsWith('image/')) return 'image'
  if (file.type.startsWith('audio/')) return 'audio'
  if (file.type.startsWith('video/')) return 'video'
  return 'document'
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
