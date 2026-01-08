'use client'
import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import { useStore } from '@/store'
import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useQueryState } from 'nuqs'
import { Send, Square, Upload, Loader2, CheckCircle, AlertCircle, Microscope, CirclePlus, MessageSquarePlus, Mail, Calendar, ListTodo, StickyNote, FileText, File } from 'lucide-react'
import useChatActions from '@/hooks/useChatActions'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useCancelRun } from '@/hooks/useCancelRun'
import FilePreview from './FilePreview'
import FileUploadDropdown from './FileUploadDropdown'
import { motion, AnimatePresence } from 'framer-motion'
import { dropZone } from '@/lib/animations'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const ChatInput = () => {
  const { chatInputRef } = useStore()
  const { handleStreamResponse } = useAIChatStreamHandler()
  const { cancelRun, isCancelling } = useCancelRun()
  const { clearChat, focusChatInput } = useChatActions()
  const [selectedAgent] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [sessionId] = useQueryState('session')  // ✅ v1.2.24: Get session from URL
  const [inputMessage, setInputMessage] = useState('')
  const isStreaming = useStore((state) => state.isStreaming)
  const messages = useStore((state) => state.messages)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const knowledgeFileInputRef = useRef<HTMLInputElement>(null)
  const plusMenuRef = useRef<HTMLDivElement>(null)
  const { files, addFiles, removeFile, clearFiles } = useFileUpload()
  const [isDragging, setIsDragging] = useState(false)
  const [uploadingKnowledge, setUploadingKnowledge] = useState(false)
  const [knowledgeStatus, setKnowledgeStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [iconColor, setIconColor] = useState('#FFFFFF')
  const [deepResearch, setDeepResearch] = useState(false)  // ✅ v1.2.24: Deep Research toggle state
  const [isPlusMenuOpen, setIsPlusMenuOpen] = useState(false)

  // Update icon color when theme changes
  useEffect(() => {
    const updateIconColor = () => {
      const accentColor = localStorage.getItem('accentColor')
      const isDark = document.documentElement.classList.contains('dark')

      console.log('🎨 SEND BUTTON updateIconColor:', { accentColor, isDark })

      if (accentColor === 'contrast' || accentColor === null) {
        // CONTRAST MODE:
        // Dark theme: white button (#E0E0E0) → black icon (#212124)
        // Light theme: black button (#212124) → white icon (#E0E0E0)
        const color = isDark ? '#212124' : '#E0E0E0'
        console.log('🎨 SEND BUTTON setting CONTRAST color:', color)
        setIconColor(color)
      } else {
        // COLOR ACCENTS (green, blue, etc.): Always white icon
        console.log('🎨 SEND BUTTON setting COLOR ACCENT: #FFFFFF (white)')
        setIconColor('#FFFFFF')
      }
    }

    updateIconColor()

    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          updateIconColor()
        }
      })
    })

    observer.observe(document.documentElement, { attributes: true })

    // Listen for accent color changes
    const handleAccentChange = () => {
      updateIconColor()
    }

    window.addEventListener('accentColorChange', handleAccentChange)

    return () => {
      observer.disconnect()
      window.removeEventListener('accentColorChange', handleAccentChange)
    }
  }, [])

  // ✅ v1.2.24: Load Deep Research state from session
  useEffect(() => {
    if (sessionId) {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      fetch(`${apiUrl}/api/sessions/${sessionId}/state`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
        .then(res => res.json())
        .then(data => {
          setDeepResearch(data.deep_research || false)
        })
        .catch(err => console.error('Failed to load session state:', err))
    } else {
      // New session - reset to default (false)
      setDeepResearch(false)
    }
  }, [sessionId])

  // Click outside handler for plus menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (plusMenuRef.current && !plusMenuRef.current.contains(event.target as Node)) {
        setIsPlusMenuOpen(false)
      }
    }

    if (isPlusMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isPlusMenuOpen])

  // Handle new conversation
  const handleNewChat = () => {
    clearChat()
    focusChatInput()
    setIsPlusMenuOpen(false)
  }

  // Auto-grow functionality
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }

  // File upload handler for FileUploadDropdown
  const handleFilesSelected = (selectedFiles: FileList) => {
    if (selectedFiles && selectedFiles.length > 0) {
      addFiles(selectedFiles)
    }
  }

  // Knowledge upload handlers
  const handleKnowledgeUploadClick = () => {
    knowledgeFileInputRef.current?.click()
  }

  const handleKnowledgeFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadingKnowledge(true)
    setKnowledgeStatus('idle')

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

      setKnowledgeStatus('success')
      toast.success(data.message || 'File uploaded to knowledge base successfully!')

      // Clear status after 3 seconds
      setTimeout(() => {
        setKnowledgeStatus('idle')
      }, 3000)

    } catch (err) {
      console.error('Upload error:', err)
      setKnowledgeStatus('error')
      toast.error('Failed to upload file. Please try again.')

      setTimeout(() => {
        setKnowledgeStatus('idle')
      }, 3000)
    } finally {
      setUploadingKnowledge(false)
      // Clear file input
      if (knowledgeFileInputRef.current) {
        knowledgeFileInputRef.current.value = ''
      }
    }
  }

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set to false if leaving the main container
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles)
    }
  }

  const handleSubmit = async () => {
    if (!inputMessage.trim()) return

    const currentMessage = inputMessage
    const currentFiles = files.map(f => f.file)

    setInputMessage('')
    clearFiles()

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      // Create FormData with message and files
      const formData = new FormData()
      formData.append('message', currentMessage)
      formData.append('deep_research', deepResearch.toString())  // ✅ v1.2.24: Include Deep Research flag

      // Append files if any
      currentFiles.forEach((file) => {
        formData.append('files', file)
      })

      await handleStreamResponse(formData)
    } catch (error) {
      toast.error(
        `Error in handleSubmit: ${
          error instanceof Error ? error.message : String(error)
        }`
      )
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      e.key === 'Enter' &&
      !e.nativeEvent.isComposing &&
      !e.shiftKey &&
      !isStreaming
    ) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Sync chatInputRef for external focus
  useEffect(() => {
    if (chatInputRef && 'current' in chatInputRef) {
      chatInputRef.current = textareaRef.current
    }
  }, [chatInputRef])

  const isDisabled = !(selectedAgent || teamId)

  return (
    <div
      className={`
        w-full
        border-t border-border-primary
        bg-light-surface dark:bg-dark-surface
        z-20
      `}
    >
      {/* File Preview */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <FilePreview files={files} onRemove={removeFile} />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        className="max-w-4xl mx-auto px-4 sm:px-6 pb-4 sm:pb-6 pt-4 relative"
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        animate={isDragging ? "dragOver" : "idle"}
        variants={dropZone}
      >
        {/* Drag Overlay */}
        <AnimatePresence>
          {isDragging && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute inset-0 bg-gradient-to-br from-accent-start/10 to-accent-end/10 border-2 border-dashed border-accent-start rounded-2xl flex items-center justify-center z-10 pointer-events-none backdrop-blur-sm"
            >
              <p className="text-accent-start font-semibold text-lg">Drop files here</p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl border border-border-primary">
          {/* Input Field */}
          <textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="What's on your mind?"
            rows={1}
            disabled={isDisabled}
            className="w-full px-4 pt-3 pb-1 bg-transparent text-light-text dark:text-dark-text placeholder:text-light-text/40 dark:placeholder:text-dark-text/40 focus:outline-none resize-none text-sm font-body transition-colors disabled:opacity-50 disabled:cursor-not-allowed rounded-t-2xl"
            style={{ minHeight: '40px', maxHeight: '150px' }}
          />

          {/* Hidden Knowledge File Input */}
          <input
            ref={knowledgeFileInputRef}
            type="file"
            accept=".pdf,.txt,.doc,.docx,.csv,.json"
            onChange={handleKnowledgeFileSelected}
            className="hidden"
          />

          {/* Button Row - separate from textarea, no overlap */}
          <div className="flex items-center justify-between px-2 pb-2">
            <TooltipProvider>
              {/* Left Side Buttons */}
              <div className="flex items-center gap-1">
                {/* File Upload Dropdown */}
                <FileUploadDropdown
                  onFileSelect={handleFilesSelected}
                  disabled={isDisabled}
                />

                {/* Upload to Knowledge Base Button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={handleKnowledgeUploadClick}
                      disabled={isDisabled || uploadingKnowledge}
                      className="p-2 rounded-full hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                      aria-label="Upload to Knowledge Base"
                    >
                      {uploadingKnowledge ? (
                        <Loader2 size={18} className="animate-spin text-light-text-secondary dark:text-dark-text-secondary" />
                      ) : knowledgeStatus === 'success' ? (
                        <CheckCircle size={18} className="text-success" />
                      ) : knowledgeStatus === 'error' ? (
                        <AlertCircle size={18} className="text-error" />
                      ) : (
                        <Upload size={16} strokeWidth={2} className="text-light-text dark:text-dark-text" />
                      )}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Upload to Knowledge Base</p>
                  </TooltipContent>
                </Tooltip>

                {/* Deep Research Toggle */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => setDeepResearch(!deepResearch)}
                      disabled={isDisabled}
                      className={`p-2 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${
                        deepResearch
                          ? ''
                          : 'hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60'
                      }`}
                      style={deepResearch ? {
                        backgroundColor: 'rgb(var(--accent-rgb))',
                        color: iconColor,
                      } : {}}
                      aria-label="Deep Research"
                    >
                      <Microscope size={16} strokeWidth={2} className={deepResearch ? '' : 'text-light-text dark:text-dark-text'} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Deep Research</p>
                  </TooltipContent>
                </Tooltip>
              </div>

              {/* Right Side Buttons */}
              <div className="flex items-center gap-3">
                {/* Plus Menu Button */}
                <div className="relative" ref={plusMenuRef}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setIsPlusMenuOpen(!isPlusMenuOpen)}
                        disabled={isDisabled}
                        className={`p-2 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${
                          isPlusMenuOpen ? 'bg-accent/10' : 'hover:bg-accent/10'
                        } text-light-text dark:text-dark-text`}
                        aria-label="Create new"
                      >
                        <CirclePlus size={16} strokeWidth={2} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Create new</p>
                    </TooltipContent>
                  </Tooltip>

                  <AnimatePresence>
                    {isPlusMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.15, ease: "easeOut" }}
                        className="absolute bottom-full right-0 mb-2 min-w-[200px] py-1 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-lg overflow-hidden"
                      >
                        {/* New conversation */}
                        <motion.button
                          onClick={handleNewChat}
                          disabled={messages.length === 0}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors text-sm disabled:opacity-30 disabled:cursor-not-allowed"
                          whileHover={{ x: 4 }}
                          transition={{ duration: 0.2 }}
                        >
                          <MessageSquarePlus size={16} strokeWidth={2} />
                          <span>New conversation</span>
                        </motion.button>

                        {/* New email */}
                        <motion.button
                          onClick={() => { setIsPlusMenuOpen(false); toast.info('Coming soon') }}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors text-sm"
                          whileHover={{ x: 4 }}
                          transition={{ duration: 0.2 }}
                        >
                          <Mail size={16} strokeWidth={2} />
                          <span>New email</span>
                        </motion.button>

                        {/* New calendar event */}
                        <motion.button
                          onClick={() => { setIsPlusMenuOpen(false); toast.info('Coming soon') }}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors text-sm"
                          whileHover={{ x: 4 }}
                          transition={{ duration: 0.2 }}
                        >
                          <Calendar size={16} strokeWidth={2} />
                          <span>New calendar event</span>
                        </motion.button>

                        {/* New task */}
                        <motion.button
                          onClick={() => { setIsPlusMenuOpen(false); toast.info('Coming soon') }}
                          className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors text-sm"
                          whileHover={{ x: 4 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ListTodo size={16} strokeWidth={2} />
                          <span>New task</span>
                        </motion.button>

                        {/* Divider */}
                        <div className="my-1 border-t border-border-primary" />

                        {/* New note - coming soon */}
                        <motion.button
                          disabled
                          className="w-full flex items-center gap-3 px-3 py-2 text-light-text/25 dark:text-dark-text/25 text-sm cursor-not-allowed"
                        >
                          <StickyNote size={16} strokeWidth={2} />
                          <span>New note</span>
                          <span className="ml-auto text-xs">Soon</span>
                        </motion.button>

                        {/* New document - coming soon */}
                        <motion.button
                          disabled
                          className="w-full flex items-center gap-3 px-3 py-2 text-light-text/25 dark:text-dark-text/25 text-sm cursor-not-allowed"
                        >
                          <FileText size={16} strokeWidth={2} />
                          <span>New document</span>
                          <span className="ml-auto text-xs">Soon</span>
                        </motion.button>

                        {/* New file - coming soon */}
                        <motion.button
                          disabled
                          className="w-full flex items-center gap-3 px-3 py-2 text-light-text/25 dark:text-dark-text/25 text-sm cursor-not-allowed"
                        >
                          <File size={16} strokeWidth={2} />
                          <span>New file</span>
                          <span className="ml-auto text-xs">Soon</span>
                        </motion.button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Send/Stop Button - transforms based on streaming state */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={isStreaming ? cancelRun : handleSubmit}
                      disabled={isStreaming ? isCancelling : (isDisabled || !inputMessage.trim())}
                      className="w-10 h-10 rounded-full disabled:cursor-not-allowed flex items-center justify-center transition-all"
                      style={{
                        backgroundColor: 'rgb(var(--accent-rgb))',
                        color: iconColor,
                      }}
                      onMouseEnter={(e) => {
                        const canHover = isStreaming ? !isCancelling : (!isDisabled && inputMessage.trim())
                        if (canHover) {
                          e.currentTarget.style.backgroundColor = 'rgba(var(--accent-rgb), 0.9)'
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgb(var(--accent-rgb))'
                      }}
                      aria-label={isStreaming ? "Stop response" : "Send message"}
                    >
                      {isStreaming ? (
                        isCancelling ? (
                          <Loader2 size={18} className="animate-spin" />
                        ) : (
                          <Square size={14} fill="currentColor" />
                        )
                      ) : (
                        <Send size={18} />
                      )}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{isStreaming ? (isCancelling ? "Stopping..." : "Stop response") : "Send message (Enter)"}</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            </TooltipProvider>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default ChatInput
