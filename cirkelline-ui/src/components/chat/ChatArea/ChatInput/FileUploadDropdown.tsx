'use client'

import { useState, useRef, useEffect } from 'react'
import { FileText, Image, Video, AudioWaveform, Paperclip } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface FileUploadDropdownProps {
  onFileSelect: (files: FileList) => void
  disabled?: boolean
}

const fileTypes = [
  { type: 'document', icon: FileText, label: 'Document', accept: '.pdf,.txt,.doc,.docx' },
  { type: 'image', icon: Image, label: 'Image', accept: 'image/*' },
  { type: 'video', icon: Video, label: 'Video', accept: 'video/*' },
  { type: 'audio', icon: AudioWaveform, label: 'Audio', accept: 'audio/*' },
]

export default function FileUploadDropdown({ onFileSelect, disabled }: FileUploadDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({})
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleFileClick = (type: string) => {
    fileInputRefs.current[type]?.click()
    setIsOpen(false)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onFileSelect(files)
    }
    // Reset input
    e.target.value = ''
    setIsOpen(false)
  }

  return (
    <TooltipProvider delayDuration={300}>
      <div className="relative" ref={dropdownRef}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => setIsOpen(!isOpen)}
              disabled={disabled}
              className={cn(
                "p-2 rounded-full transition-all duration-200",
                "hover:bg-accent/10 text-light-text dark:text-dark-text",
                "disabled:opacity-30 disabled:cursor-not-allowed",
                isOpen && "bg-accent/10"
              )}
              aria-label="Attach file"
            >
              <Paperclip size={16} strokeWidth={2} />
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Attach files</p>
          </TooltipContent>
        </Tooltip>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="absolute bottom-full left-0 mb-2 min-w-[140px] py-1 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-lg overflow-hidden"
            >
              {fileTypes.map((fileType) => {
                const Icon = fileType.icon
                return (
                  <motion.button
                    key={fileType.type}
                    onClick={() => handleFileClick(fileType.type)}
                    className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors text-sm"
                    whileHover={{ x: 4 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Icon size={16} strokeWidth={2} />
                    <span>{fileType.label}</span>
                    <input
                      ref={(el) => {
                        if (el) fileInputRefs.current[fileType.type] = el
                      }}
                      type="file"
                      multiple
                      accept={fileType.accept}
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </motion.button>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </TooltipProvider>
  )
}
