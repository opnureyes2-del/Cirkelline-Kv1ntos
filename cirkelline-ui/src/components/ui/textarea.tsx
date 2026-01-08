import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Show error state */
  error?: boolean
  /** Error message to display */
  errorMessage?: string
  /** Show success state */
  success?: boolean
  /** Enable auto-grow behavior */
  autoGrow?: boolean
  /** Maximum height when auto-growing (in pixels) */
  maxHeight?: number
  /** Minimum height (in pixels) */
  minHeight?: number
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      error = false,
      errorMessage,
      success = false,
      autoGrow = false,
      maxHeight = 200,
      minHeight = 56,
      onChange,
      ...props
    },
    ref
  ) => {
    const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)

    // Handle auto-grow
    React.useEffect(() => {
      if (autoGrow && textareaRef.current) {
        const textarea = textareaRef.current
        textarea.style.height = 'auto'
        const scrollHeight = textarea.scrollHeight
        const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight)
        textarea.style.height = `${newHeight}px`
      }
    }, [autoGrow, maxHeight, minHeight, props.value])

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (autoGrow) {
        const textarea = e.target
        textarea.style.height = 'auto'
        const scrollHeight = textarea.scrollHeight
        const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight)
        textarea.style.height = `${newHeight}px`
      }
      onChange?.(e)
    }

    // Combine refs
    React.useImperativeHandle(ref, () => textareaRef.current!)

    return (
      <div className="relative w-full">
        <textarea
          ref={textareaRef}
          className={cn(
            // Base styles
            'flex w-full rounded-xl border bg-light-surface dark:bg-dark-surface px-4 py-3',
            'text-sm font-body text-light-text dark:text-dark-text',
            'placeholder:text-light-text-placeholder dark:placeholder:text-dark-text-placeholder',
            'transition-all duration-200',
            'resize-none', // Disable manual resize if autoGrow is enabled

            // Focus styles
            'focus:outline-none focus:ring-2 focus:ring-offset-2',

            // Scrollbar
            'scrollbar-thin scrollbar-thumb-border-primary scrollbar-track-transparent',

            // States
            error
              ? 'border-error focus:ring-error/50 focus:border-error'
              : success
              ? 'border-success focus:ring-success/50 focus:border-success'
              : 'border-border-primary focus:ring-accent-start/50 focus:border-accent-start',

            // Disabled
            'disabled:cursor-not-allowed disabled:opacity-50',

            className
          )}
          style={{
            minHeight: autoGrow ? `${minHeight}px` : undefined,
            maxHeight: autoGrow ? `${maxHeight}px` : undefined,
          }}
          onChange={handleChange}
          {...props}
        />

        {/* Error message */}
        {error && errorMessage && (
          <p className="mt-1.5 text-xs text-error font-body">
            {errorMessage}
          </p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

export { Textarea }