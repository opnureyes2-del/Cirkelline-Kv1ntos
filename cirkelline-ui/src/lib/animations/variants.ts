/**
 * Animation Variants
 * Reusable Framer Motion variants for consistent animations
 */

import { Variants } from 'framer-motion'
import { spring, springBouncy, springSmooth, duration, stagger, delay } from './constants'

// ============================================
// BASIC ANIMATIONS
// ============================================

export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

export const fadeInFast: Variants = {
  initial: { opacity: 0 },
  animate: { 
    opacity: 1,
    transition: { duration: duration.fast }
  },
  exit: { 
    opacity: 0,
    transition: { duration: duration.fast }
  },
}

export const slideUp: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: spring
  },
  exit: { 
    opacity: 0, 
    y: 10,
    transition: { duration: duration.fast }
  },
}

export const slideDown: Variants = {
  initial: { 
    opacity: 0, 
    y: -20,
    scaleY: 0.95
  },
  animate: { 
    opacity: 1, 
    y: 0,
    scaleY: 1,
    transition: springBouncy
  },
  exit: { 
    opacity: 0, 
    y: -10,
    scaleY: 0.98,
    transition: { duration: duration.fast }
  },
}

export const slideFromLeft: Variants = {
  initial: { 
    x: "-100%",
    opacity: 0
  },
  animate: { 
    x: 0,
    opacity: 1,
    transition: spring
  },
  exit: { 
    x: "-100%",
    opacity: 0,
    transition: { duration: duration.normal }
  },
}

export const slideFromRight: Variants = {
  initial: { 
    x: "100%",
    opacity: 0
  },
  animate: { 
    x: 0,
    opacity: 1,
    transition: spring
  },
  exit: { 
    x: "100%",
    opacity: 0,
    transition: { duration: duration.normal }
  },
}

export const scaleIn: Variants = {
  initial: { 
    scale: 0.9,
    opacity: 0
  },
  animate: { 
    scale: 1,
    opacity: 1,
    transition: springBouncy
  },
  exit: { 
    scale: 0.95,
    opacity: 0,
    transition: { duration: duration.fast }
  },
}

// ============================================
// COMPONENT ANIMATIONS
// ============================================

export const messageEntry: Variants = {
  initial: { 
    opacity: 0,
    y: 30,
    scale: 0.95
  },
  animate: { 
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      ...springSmooth,
      delay: delay.short
    }
  },
}

export const sessionItemHover: Variants = {
  rest: {
    scale: 1,
    backgroundColor: "transparent"
  },
  hover: {
    scale: 1.02,
    backgroundColor: "rgba(var(--accent-rgb), 0.1)",
    transition: {
      duration: duration.fast,
    }
  },
  tap: {
    scale: 0.98,
    transition: {
      duration: duration.instant
    }
  },
}

export const buttonInteraction: Variants = {
  idle: {
    scale: 1,
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)"
  },
  hover: {
    scale: 1.05,
    boxShadow: "0 4px 16px rgba(var(--accent-rgb), 0.3)",
    transition: {
      duration: duration.fast,
    }
  },
  tap: {
    scale: 0.95,
    transition: {
      duration: duration.instant
    }
  },
}

export const cardLift: Variants = {
  rest: {
    y: 0,
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)"
  },
  hover: {
    y: -4,
    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.15)",
    transition: {
      duration: duration.fast,
    }
  },
}

// ============================================
// LAYOUT ANIMATIONS
// ============================================

export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: stagger.normal,
      delayChildren: delay.short
    }
  },
  exit: {
    transition: {
      staggerChildren: stagger.fast,
      staggerDirection: -1
    }
  },
}

export const staggerContainerFast: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: stagger.fast,
      delayChildren: delay.none
    }
  },
}

export const staggerItem: Variants = {
  initial: { 
    opacity: 0,
    x: -20
  },
  animate: { 
    opacity: 1,
    x: 0,
    transition: spring
  },
  exit: {
    opacity: 0,
    x: -10,
    transition: {
      duration: duration.fast
    }
  },
}

export const collapseExpand: Variants = {
  collapsed: {
    height: 0,
    opacity: 0,
    transition: {
      height: {
        duration: duration.slow,
      },
      opacity: {
        duration: duration.fast,
      }
    }
  },
  expanded: {
    height: "auto",
    opacity: 1,
    transition: {
      height: {
        duration: duration.slow,
      },
      opacity: {
        duration: duration.slow,
        delay: delay.short,
      }
    }
  },
}

export const modalOverlay: Variants = {
  initial: { 
    opacity: 0,
    backdropFilter: "blur(0px)"
  },
  animate: { 
    opacity: 1,
    backdropFilter: "blur(8px)",
    transition: {
      duration: duration.fast,
    }
  },
  exit: { 
    opacity: 0,
    backdropFilter: "blur(0px)",
    transition: {
      duration: duration.fast,
    }
  },
}

export const modalContent: Variants = {
  initial: { 
    scale: 0.9,
    opacity: 0,
    y: 20
  },
  animate: { 
    scale: 1,
    opacity: 1,
    y: 0,
    transition: spring
  },
  exit: { 
    scale: 0.95,
    opacity: 0,
    y: 10,
    transition: {
      duration: duration.fast
    }
  },
}

// ============================================
// INTERACTIVE ANIMATIONS
// ============================================

export const typingDot = (delayMultiplier: number = 0): Variants => ({
  animate: {
    y: [0, -8, 0],
    scale: [1, 1.1, 1],
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 0.8,
      repeat: Infinity,
      ease: "easeInOut",
      delay: delayMultiplier * 0.15
    }
  }
})

export const glowEffect: Variants = {
  idle: {
    boxShadow: "0 0 0 rgba(var(--accent-rgb), 0)"
  },
  hover: {
    boxShadow: "0 0 20px rgba(var(--accent-rgb), 0.4)",
    transition: {
      duration: duration.slow,
    }
  },
  focus: {
    boxShadow: "0 0 0 3px rgba(var(--accent-rgb), 0.3)",
    transition: {
      duration: duration.fast
    }
  },
}

export const dropZone: Variants = {
  idle: {
    scale: 1,
    borderColor: "rgba(209, 213, 219, 1)",
    backgroundColor: "transparent"
  },
  dragOver: {
    scale: 1.02,
    borderColor: "rgba(var(--accent-rgb), 1)",
    backgroundColor: "rgba(var(--accent-rgb), 0.05)",
    boxShadow: "0 0 0 3px rgba(var(--accent-rgb), 0.1)",
    transition: {
      duration: duration.fast,
    }
  },
  drop: {
    scale: 0.98,
    transition: {
      duration: duration.instant
    }
  },
}

export const sendButton: Variants = {
  idle: {
    scale: 1,
    rotate: 0
  },
  hover: {
    scale: 1.1,
    boxShadow: "0 4px 16px rgba(var(--accent-rgb), 0.4)",
    transition: {
      duration: duration.fast,
    }
  },
  tap: {
    scale: 0.9,
    transition: {
      duration: duration.instant
    }
  },
  sending: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear"
    }
  },
}

// ============================================
// SIDEBAR SPECIFIC
// ============================================

export const sidebarTransition: Variants = {
  collapsed: {
    width: 64,
    transition: {
      width: {
        duration: duration.slow,
      }
    }
  },
  expanded: {
    width: 280,
    transition: {
      width: {
        duration: duration.slow,
      }
    }
  },
}

export const sidebarContent: Variants = {
  collapsed: {
    opacity: 0,
    x: -10,
    transition: {
      duration: duration.fast
    }
  },
  expanded: {
    opacity: 1,
    x: 0,
    transition: {
      duration: duration.fast,
      delay: delay.short
    }
  },
}

export const iconRotate: Variants = {
  collapsed: { rotate: 0 },
  expanded: { rotate: 90 },
}