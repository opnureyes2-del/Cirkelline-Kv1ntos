import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'

export default {
  darkMode: 'class', // Class-based dark mode
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        // New Design System V2.0 Colors - Minimal & Clean
        light: {
          bg: '#FFFFFF',
          'bg-secondary': '#FFFFFF',
          surface: '#FFFFFF',
          elevated: '#FFFFFF',
          'event-bg': '#E4E4E2', // Custom gray for event pills
          text: '#212124',
          'text-secondary': '#6B6B6B',
          'text-tertiary': '#9B9B9B',
          'text-placeholder': '#B0B0B0',
        },
        dark: {
          bg: '#212124',
          'bg-secondary': '#212124',
          surface: '#212124',
          elevated: '#212124',
          'event-bg': '#2A2A2A', // Custom gray for event pills
          text: '#E0E0E0',
          'text-secondary': '#A0A0A0',
          'text-tertiary': '#808080',
          'text-placeholder': '#606060',
        },
        
        // Accent colors - DYNAMIC via CSS variable
        accent: {
          DEFAULT: 'rgb(var(--accent-rgb) / <alpha-value>)',
          start: 'rgb(var(--accent-rgb))',
          end: 'rgb(var(--accent-rgb))',
          'hover-start': 'rgb(var(--accent-rgb))',
          'hover-end': 'rgb(var(--accent-rgb))',
          'active-start': 'rgb(var(--accent-rgb))',
          'active-end': 'rgb(var(--accent-rgb))',
          secondary: '#F59E0B',
          'secondary-hover': '#D97706',
        },

        // Semantic colors
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6',

        // Border colors
        'border-primary': 'var(--border-primary)',
        'border-secondary': 'var(--border-secondary)',
        'border-focus': 'var(--border-focus)',

        // Legacy compatibility
        primary: '#FAFAFA',
        primaryAccent: '#18181B',
        brand: '#DD4814',
        background: {
          DEFAULT: '#0D1117',
          secondary: '#1C2128'
        },
        secondary: '#f5f5f5',
        border: 'rgba(var(--color-border-default))',
        muted: '#A1A1AA',
        destructive: '#EF4444',
        positive: '#10B981'
      },

      fontFamily: {
        // Default body font - Inter
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'],
        // Titles and headings - Alan Sans (logo, sidebar titles)
        heading: ['"Alan Sans"', 'system-ui', 'sans-serif'],
        // Code snippets - monospace
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'Consolas', 'monospace'],
        // Body text and paragraphs - Inter
        body: ['Inter', 'system-ui', 'sans-serif'],
        // Legacy mappings
        ubuntu: ['Inter', 'system-ui', 'sans-serif'],
        geist: ['Inter', 'system-ui', 'sans-serif'],
        dmmono: ['SF Mono', 'monospace']
      },

      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },

      borderRadius: {
        xl: '12px',
        '2xl': '16px',
        '3xl': '24px',
      },

      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
        'glow': '0 0 20px rgba(var(--accent-rgb), 0.4)',
        'glow-lg': '0 0 30px rgba(var(--accent-rgb), 0.6)',
      },

      animation: {
        // CSS keyframes
        'fade-in': 'fadeIn 0.15s ease-out',
        'slide-up': 'slideUpIn 0.25s ease-out',
        'slide-down': 'slideDown 0.3s ease-out forwards',
        'scale-in': 'scaleIn 0.25s ease-out',
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'gradient-shimmer': 'gradientShimmer 3s ease-in-out infinite',
        'bounce-dot': 'bounceDot 0.8s ease-in-out infinite',
        'bounce-dot-1': 'bounceDot 0.8s ease-in-out infinite 0s',
        'bounce-dot-2': 'bounceDot 0.8s ease-in-out infinite 0.15s',
        'bounce-dot-3': 'bounceDot 0.8s ease-in-out infinite 0.3s',
        'spin': 'spin 1s linear infinite',
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite',
        'slide-from-left': 'slideFromLeft 0.25s ease-out',
        'slide-from-right': 'slideFromRight 0.25s ease-out',
        'dropdown': 'dropdown 0.15s ease-out',
        'modal': 'modalIn 0.2s ease-out',
      },

      keyframes: {
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        slideUpIn: {
          'from': { opacity: '0', transform: 'translateY(20px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          'from': { opacity: '0', maxHeight: '0', transform: 'translateY(-10px)' },
          'to': { opacity: '1', maxHeight: '1000px', transform: 'translateY(0)' },
        },
        scaleIn: {
          'from': { opacity: '0', transform: 'scale(0.9)' },
          'to': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        gradientShimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        bounceDot: {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%': { transform: 'translateY(-8px)' },
        },
        spin: {
          'from': { transform: 'rotate(0deg)' },
          'to': { transform: 'rotate(360deg)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(var(--accent-rgb), 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(var(--accent-rgb), 0.8)' },
        },
        slideFromLeft: {
          'from': { opacity: '0', transform: 'translateX(-100%)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        },
        slideFromRight: {
          'from': { opacity: '0', transform: 'translateX(100%)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        },
        dropdown: {
          'from': { opacity: '0', transform: 'translateY(-8px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        modalIn: {
          'from': { opacity: '0', transform: 'scale(0.95) translateY(-20px)' },
          'to': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
      },

      transitionDuration: {
        '0': '0ms',
        '150': '150ms',
        '250': '250ms',
        '400': '400ms',
        '600': '600ms',
      },

      transitionTimingFunction: {
        'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'out': 'cubic-bezier(0, 0, 0.2, 1)',
        'in': 'cubic-bezier(0.4, 0, 1, 1)',
        'spring': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },

      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
    }
  },
  plugins: [tailwindcssAnimate]
} satisfies Config
