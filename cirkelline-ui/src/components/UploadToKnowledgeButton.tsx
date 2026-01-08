'use client'
import { useState, useRef } from 'react'
import { Upload, Loader2, CheckCircle, AlertCircle } from 'lucide-react'

export default function UploadToKnowledgeButton() {
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setStatus('idle')
    setMessage('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('Not authenticated')
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      const response = await fetch(`${apiUrl}/api/knowledge/upload`, {
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

      setStatus('success')
      setMessage(data.message || 'File uploaded successfully!')

      // Clear status after 3 seconds
      setTimeout(() => {
        setStatus('idle')
        setMessage('')
      }, 3000)

    } catch (err) {
      console.error('Upload error:', err)
      setStatus('error')
      setMessage('Failed to upload file. Please try again.')

      setTimeout(() => {
        setStatus('idle')
        setMessage('')
      }, 3000)
    } finally {
      setUploading(false)
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelected}
        className="hidden"
        accept=".pdf,.txt,.doc,.docx,.csv,.json"
      />

      <button
        onClick={handleUploadClick}
        disabled={uploading}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Upload to Knowledge Base"
      >
        {uploading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : status === 'success' ? (
          <CheckCircle className="w-4 h-4 text-green-500" />
        ) : status === 'error' ? (
          <AlertCircle className="w-4 h-4 text-red-500" />
        ) : (
          <Upload className="w-4 h-4" />
        )}

        <span className="text-sm font-medium">
          {uploading ? 'Uploading...' : 'Upload to Knowledge'}
        </span>
      </button>

      {message && (
        <div className={`absolute top-full mt-2 left-0 right-0 p-2 rounded-lg text-sm ${
          status === 'success'
            ? 'bg-green-500/10 text-green-600 dark:text-green-400'
            : 'bg-red-500/10 text-red-600 dark:text-red-400'
        }`}>
          {message}
        </div>
      )}
    </div>
  )
}
