/**
 * Centralized Color Configuration
 *
 * This file is the single source of truth for all accent colors used in Cirkelline.
 * Import from here instead of hardcoding colors in components.
 */

// Accent color definitions with RGB values (for CSS variables) and hex (for inline styles)
export const ACCENT_COLORS = {
  contrast: {
    name: 'Contrast',
    // Dynamic based on theme - light: dark text, dark: light text
    rgb: {
      light: '33, 33, 36',      // #212124 for light theme
      dark: '224, 224, 224',    // #E0E0E0 for dark theme
    },
    hex: {
      light: '#212124',
      dark: '#E0E0E0',
    },
  },
  purple: {
    name: 'Purple',
    rgb: '142, 11, 131',
    hex: '#8E0B83',
  },
  orange: {
    name: 'Orange',
    rgb: '236, 75, 19',
    hex: '#EC4B13',
  },
  green: {
    name: 'Green',
    rgb: '19, 236, 129',
    hex: '#13EC81',
  },
  blue: {
    name: 'Blue',
    rgb: '19, 128, 236',
    hex: '#1380EC',
  },
  pink: {
    name: 'Pink',
    rgb: '236, 19, 128',
    hex: '#EC1380',
  },
} as const

// Type for accent color keys
export type AccentColorKey = keyof typeof ACCENT_COLORS

// Get list of accent color keys for iteration
export const ACCENT_COLOR_KEYS = Object.keys(ACCENT_COLORS) as AccentColorKey[]

// Helper to get RGB value for an accent color
export function getAccentRGB(color: AccentColorKey, isDark: boolean = false): string {
  if (color === 'contrast') {
    const contrastConfig = ACCENT_COLORS.contrast
    return isDark ? contrastConfig.rgb.dark : contrastConfig.rgb.light
  }

  const colorConfig = ACCENT_COLORS[color]
  return colorConfig.rgb as string
}

// Helper to get hex value for an accent color (for inline styles/swatches)
export function getAccentHex(color: AccentColorKey, isDark: boolean = false): string {
  if (color === 'contrast') {
    const contrastConfig = ACCENT_COLORS.contrast
    return isDark ? contrastConfig.hex.dark : contrastConfig.hex.light
  }

  const colorConfig = ACCENT_COLORS[color]
  return colorConfig.hex as string
}

// Contrast text colors (for buttons with accent background)
export const CONTRAST_TEXT = {
  light: '#E0E0E0',  // Light text for dark backgrounds
  dark: '#212124',   // Dark text for light backgrounds
} as const

// Helper to get contrast text color based on accent and theme
export function getContrastText(accentColor: AccentColorKey, isDark: boolean): string {
  if (accentColor === 'contrast') {
    // Contrast mode: invert the text
    return isDark ? CONTRAST_TEXT.dark : CONTRAST_TEXT.light
  }
  // For all color accents, use white text
  return '#FFFFFF'
}
