import { useState, useEffect, useRef } from 'react'

/**
 * Simple hook to animate text character-by-character
 *
 * This hook takes incoming text chunks and animates them smoothly
 * letter-by-letter for a typewriter effect. It only animates NEW content
 * that gets appended, not the entire message.
 *
 * @param targetText - The full text to display (updates as chunks arrive)
 * @param speed - Characters per frame (higher = faster). Default: 2
 */
export function useStreamingText(targetText: string, speed: number = 2) {
  const [displayedText, setDisplayedText] = useState('')
  const animationRef = useRef<number | undefined>(undefined)
  const currentIndexRef = useRef(0)

  useEffect(() => {
    // If target text is shorter (message was cleared), reset
    if (targetText.length < displayedText.length) {
      setDisplayedText(targetText)
      currentIndexRef.current = targetText.length
      return
    }

    // If target text hasn't changed, do nothing
    if (targetText === displayedText) {
      return
    }

    // Cancel any ongoing animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
    }

    // Start animating from current position to target length
    const animate = () => {
      const currentIndex = currentIndexRef.current
      const targetLength = targetText.length

      if (currentIndex < targetLength) {
        // Add 'speed' characters per frame (60fps = smooth animation)
        const newIndex = Math.min(currentIndex + speed, targetLength)
        setDisplayedText(targetText.substring(0, newIndex))
        currentIndexRef.current = newIndex

        // Continue animation
        animationRef.current = requestAnimationFrame(animate)
      }
    }

    // Start animation
    animationRef.current = requestAnimationFrame(animate)

    // Cleanup on unmount
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [targetText, speed, displayedText])

  return displayedText
}
