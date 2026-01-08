/**
 * Animation Hooks
 * Custom React hooks for animation utilities
 */

import { useEffect, useState } from 'react'

/**
 * Hook to detect if user prefers reduced motion
 * Respects system accessibility settings
 */
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches)
    }

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    } 
    // Fallback for older browsers
    else {
      mediaQuery.addListener(handleChange)
      return () => mediaQuery.removeListener(handleChange)
    }
  }, [])

  return prefersReducedMotion
}

/**
 * Hook to get animation config based on reduced motion preference
 * Returns simplified animations if user prefers reduced motion
 */
export function useAnimationConfig() {
  const shouldReduce = useReducedMotion()

  return {
    shouldReduce,
    transition: shouldReduce 
      ? { duration: 0.01 } 
      : undefined,
    initial: shouldReduce 
      ? { opacity: 0 } 
      : undefined,
    animate: shouldReduce 
      ? { opacity: 1 } 
      : undefined,
  }
}

/**
 * Hook to conditionally apply animation variants
 * Returns simple fade if reduced motion is preferred
 */
export function useConditionalVariant<T extends object>(
  fullVariant: T,
  reducedVariant?: T
): T | { initial: { opacity: number }; animate: { opacity: number } } {
  const shouldReduce = useReducedMotion()

  if (shouldReduce) {
    return reducedVariant || {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
    }
  }

  return fullVariant
}