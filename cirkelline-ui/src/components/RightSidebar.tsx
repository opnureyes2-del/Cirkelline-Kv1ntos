'use client'

import { useState, useEffect, useRef } from 'react'
import { X, FileText, Copy, Trash2, Maximize2, Minimize2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface RightSidebarProps {
  isOpen: boolean
  onClose: () => void
  isFullscreen?: boolean
  onFullscreenToggle?: () => void
  sidebarCollapsed?: boolean
}

export default function RightSidebar({
  isOpen,
  onClose,
  isFullscreen = false,
  onFullscreenToggle,
  sidebarCollapsed = false
}: RightSidebarProps) {
  const [content, setContent] = useState('')
  const [isSaved, setIsSaved] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Load content from localStorage on mount
  useEffect(() => {
    const savedContent = localStorage.getItem('cirkelline-notes')
    if (savedContent) {
      setContent(savedContent)
    }
  }, [])

  // Auto-save to localStorage
  useEffect(() => {
    const timer = setTimeout(() => {
      if (content) {
        localStorage.setItem('cirkelline-notes', content)
        setIsSaved(true)
      }
    }, 1000)

    return () => clearTimeout(timer)
  }, [content])

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value)
    setIsSaved(false)
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    // Show success feedback
    const button = document.getElementById('copy-button')
    if (button) {
      button.textContent = 'Copied!'
      setTimeout(() => {
        button.textContent = ''
      }, 2000)
    }
  }

  const handleClear = () => {
    if (confirm('Are you sure you want to clear all notes?')) {
      setContent('')
      localStorage.removeItem('cirkelline-notes')
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Sidebar */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className={cn(
              "fixed right-0 top-16 bg-light-surface dark:bg-dark-surface",
              "border-l border-border-primary z-30",
              "flex flex-col h-[calc(100vh-4rem)]",
              isFullscreen
                ? (sidebarCollapsed
                    ? "w-full"
                    : "w-[calc(100%-16rem)] left-64")
                : "w-full lg:w-[400px] xl:w-[500px]"
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border-primary">
              <div className="flex items-center gap-2">
                <FileText size={20} className="text-light-text-secondary dark:text-dark-text-secondary" />
                <h2 className="font-heading text-lg text-light-text dark:text-dark-text">
                  Workspace
                </h2>
                {!isSaved && (
                  <span className="text-xs text-accent">• Unsaved</span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onFullscreenToggle}
                      >
                        {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onClose}
                      >
                        <X size={16} />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Close workspace</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

            {/* Toolbar */}
            <div className="flex items-center gap-2 p-3 border-b border-border-primary bg-light-bg dark:bg-dark-bg">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopy}
                      className="gap-2"
                    >
                      <Copy size={14} />
                      <span id="copy-button" className="text-xs"></span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Copy all content</p>
                  </TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClear}
                      className="gap-2 hover:text-error"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Clear all notes</p>
                  </TooltipContent>
                </Tooltip>

                <div className="ml-auto text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  {content.length} characters
                </div>
              </TooltipProvider>
            </div>

            {/* Content area */}
            <div className="flex-1 p-4 overflow-hidden">
              <textarea
                ref={textareaRef}
                value={content}
                onChange={handleContentChange}
                placeholder="Start typing your notes here...

This is your personal workspace. Everything you write here is automatically saved locally and will persist even after refresh.

Tips:
• Copy responses from Cirkelline and paste them here
• Use this as a scratchpad for ideas
• Create documentation as you chat
• Keep important information handy"
                className="w-full h-full bg-transparent text-light-text dark:text-dark-text
                         placeholder:text-light-text-tertiary dark:placeholder:text-dark-text-tertiary
                         resize-none focus:outline-none font-mono text-sm leading-relaxed"
              />
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border-primary bg-light-bg dark:bg-dark-bg">
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center">
                💡 Tip: Select text in chat and press Ctrl+Shift+N to add to notes
              </p>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}