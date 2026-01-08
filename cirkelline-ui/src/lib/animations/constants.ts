/**
 * Animation Constants
 * Centralized animation configuration for consistent timing and behavior
 */

// Spring configurations for Framer Motion
export const spring = {
  type: "spring" as const,
  stiffness: 300,
  damping: 30,
}

export const springBouncy = {
  type: "spring" as const,
  stiffness: 400,
  damping: 20,
}

export const springSmooth = {
  type: "spring" as const,
  stiffness: 200,
  damping: 25,
}

export const springGentle = {
  type: "spring" as const,
  stiffness: 100,
  damping: 15,
}

// Duration constants (in seconds for Framer Motion)
export const duration = {
  instant: 0,
  fast: 0.15,
  normal: 0.25,
  slow: 0.4,
  slower: 0.6,
}

// Easing curves
export const easing = {
  inOut: [0.4, 0, 0.2, 1] as const,
  out: [0, 0, 0.2, 1] as const,
  in: [0.4, 0, 1, 1] as const,
  spring: [0.68, -0.55, 0.265, 1.55] as const,
}

// Stagger configuration
export const stagger = {
  fast: 0.03,
  normal: 0.05,
  slow: 0.1,
}

// Delay configuration
export const delay = {
  none: 0,
  short: 0.1,
  medium: 0.2,
  long: 0.3,
}