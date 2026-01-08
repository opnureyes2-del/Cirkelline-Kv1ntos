import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-900 disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 font-sans',
  {
    variants: {
      variant: {
        // Primary gradient button - THE star of the show!
        gradient:
          'active:scale-95',

        // Default solid button
        default:
          'bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:border-accent/40 active:scale-95',

        // Destructive/danger button
        destructive:
          'bg-error text-white hover:bg-error/90 active:scale-95',

        // Success button
        success:
          'bg-success text-white hover:bg-success/90 active:scale-95',

        // Outline button
        outline:
          'border-2 border-border-primary bg-transparent hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:border-accent active:scale-95',

        // Secondary button
        secondary:
          'bg-light-bg-secondary dark:bg-dark-bg-secondary text-light-text dark:text-dark-text hover:bg-light-text-secondary/10 dark:hover:bg-dark-text-secondary/10 active:scale-95',

        // Ghost button
        ghost:
          'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-accent active:scale-95',

        // Link button
        link:
          'text-accent-start underline-offset-4 hover:underline hover:text-accent-hover-start font-mono',
      },
      size: {
        default: 'h-10 px-4 py-2 text-sm rounded-xl',
        sm: 'h-8 px-3 py-1.5 text-xs rounded-lg',
        lg: 'h-12 px-6 py-3 text-base rounded-xl',
        xl: 'h-14 px-8 py-4 text-lg rounded-2xl',
        icon: 'h-10 w-10 rounded-xl',
        'icon-sm': 'h-8 w-8 rounded-lg',
        'icon-lg': 'h-12 w-12 rounded-xl',
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  /** Show loading state */
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, children, disabled, ...props }, ref) => {
    const isDisabled = disabled || loading
    const [textColor, setTextColor] = React.useState('#FFFFFF')

    // Update text color when component mounts and when theme changes
    React.useEffect(() => {
      if (variant !== 'gradient') return

      const updateTextColor = () => {
        const accentColor = localStorage.getItem('accentColor')
        const isDark = document.documentElement.classList.contains('dark')

        if (accentColor === 'contrast' || accentColor === null) {
          // CONTRAST MODE:
          // Dark theme: white button → black text (var(--contrast-dark))
          // Light theme: black button → white text (var(--contrast-light))
          const style = getComputedStyle(document.documentElement)
          const color = isDark
            ? style.getPropertyValue('--contrast-dark').trim() || '#212124'
            : style.getPropertyValue('--contrast-light').trim() || '#E0E0E0'
          setTextColor(color)
        } else {
          // COLOR ACCENTS (green, blue, etc.): Always white text
          setTextColor('#FFFFFF')
        }
      }

      updateTextColor()

      // Listen for theme changes
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'class') {
            updateTextColor()
          }
        })
      })

      observer.observe(document.documentElement, { attributes: true })

      // Listen for accent color changes
      const handleAccentChange = () => {
        updateTextColor()
      }

      window.addEventListener('accentColorChange', handleAccentChange)

      return () => {
        observer.disconnect()
        window.removeEventListener('accentColorChange', handleAccentChange)
      }
    }, [variant])

    const buttonContent = (
      <>
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </>
    )

    if (asChild) {
      return (
        <Slot
          className={cn(buttonVariants({ variant, size, className }))}
          ref={ref}
          {...props}
        >
          {buttonContent}
        </Slot>
      )
    }

    const buttonStyle = variant === 'gradient' ? {
      backgroundColor: 'rgb(var(--accent-rgb))',
      color: textColor,
    } : undefined

    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        style={buttonStyle}
        ref={ref}
        disabled={isDisabled}
        onMouseEnter={(e) => {
          if (variant === 'gradient' && !isDisabled) {
            e.currentTarget.style.backgroundColor = 'rgba(var(--accent-rgb), 0.9)'
          }
        }}
        onMouseLeave={(e) => {
          if (variant === 'gradient') {
            e.currentTarget.style.backgroundColor = 'rgb(var(--accent-rgb))'
          }
        }}
        {...props}
      >
        {buttonContent}
      </button>
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
