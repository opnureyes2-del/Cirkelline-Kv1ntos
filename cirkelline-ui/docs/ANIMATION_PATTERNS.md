# Animation Patterns Library

> Complete reference for all animation patterns used in Cirkelline UI

---

## Table of Contents

1. [Basic Animations](#basic-animations)
2. [Component Animations](#component-animations)
3. [Layout Animations](#layout-animations)
4. [Interactive Animations](#interactive-animations)
5. [Loading States](#loading-states)
6. [Implementation Examples](#implementation-examples)

---

## Basic Animations

### Fade In

**When to use:** Element entry, content reveal, modal overlays

```typescript
// Animation config
const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { 
    duration: 0.15,
    ease: "easeOut"
  }
}

// Usage
<motion.div {...fadeIn}>
  Content
</motion.div>
```

### Slide Up

**When to use:** Messages, notifications, modals

```typescript
const slideUp = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0 
  },
  exit: { 
    opacity: 0, 
    y: 10 
  },
  transition: { 
    type: "spring",
    stiffness: 300,
    damping: 30
  }
}
```

### Slide Down

**When to use:** Dropdowns, expanding sections

```typescript
const slideDown = {
  initial: { 
    opacity: 0, 
    y: -20,
    scaleY: 0.95
  },
  animate: { 
    opacity: 1, 
    y: 0,
    scaleY: 1
  },
  exit: { 
    opacity: 0, 
    y: -10,
    scaleY: 0.98
  },
  transition: { 
    type: "spring",
    stiffness: 400,
    damping: 25
  }
}
```

### Slide From Left

**When to use:** Mobile sidebar, drawer panels

```typescript
const slideFromLeft = {
  initial: { 
    x: "-100%",
    opacity: 0
  },
  animate: { 
    x: 0,
    opacity: 1
  },
  exit: { 
    x: "-100%",
    opacity: 0
  },
  transition: {
    type: "spring",
    stiffness: 300,
    damping: 30
  }
}
```

### Scale In

**When to use:** Modals, popovers, tooltips

```typescript
const scaleIn = {
  initial: { 
    scale: 0.9,
    opacity: 0
  },
  animate: { 
    scale: 1,
    opacity: 1
  },
  exit: { 
    scale: 0.95,
    opacity: 0
  },
  transition: {
    type: "spring",
    stiffness: 400,
    damping: 25
  }
}
```

---

## Component Animations

### Message Entry

**When to use:** New chat messages appearing

```typescript
const messageEntry = {
  initial: { 
    opacity: 0,
    y: 30,
    scale: 0.95
  },
  animate: { 
    opacity: 1,
    y: 0,
    scale: 1
  },
  transition: {
    type: "spring",
    stiffness: 260,
    damping: 20,
    delay: 0.1 // Slight delay for natural feel
  }
}
```

### Session Item Hover

**When to use:** Sidebar session items

```typescript
const sessionHover = {
  rest: { 
    scale: 1,
    backgroundColor: "transparent"
  },
  hover: { 
    scale: 1.02,
    backgroundColor: "rgba(139, 92, 246, 0.1)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  tap: { 
    scale: 0.98,
    transition: {
      duration: 0.1
    }
  }
}

// Usage
<motion.div
  initial="rest"
  whileHover="hover"
  whileTap="tap"
  variants={sessionHover}
>
  Session content
</motion.div>
```

### Button Interactions

**When to use:** All interactive buttons

```typescript
const buttonInteraction = {
  idle: {
    scale: 1,
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)"
  },
  hover: {
    scale: 1.05,
    boxShadow: "0 4px 16px rgba(139, 92, 246, 0.3)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  tap: {
    scale: 0.95,
    transition: {
      duration: 0.1
    }
  }
}

// With gradient shift
const gradientButton = {
  hover: {
    backgroundPosition: "200% center",
    transition: {
      duration: 0.5,
      ease: "easeInOut"
    }
  }
}
```

### Card Lift Effect

**When to use:** Hoverable cards, panels

```typescript
const cardLift = {
  rest: {
    y: 0,
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)"
  },
  hover: {
    y: -4,
    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.15)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  }
}
```

---

## Layout Animations

### Stagger Children

**When to use:** Lists, session lists, message threads

```typescript
// Container
const staggerContainer = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  },
  exit: {
    transition: {
      staggerChildren: 0.03,
      staggerDirection: -1
    }
  }
}

// Item
const staggerItem = {
  initial: { 
    opacity: 0,
    x: -20
  },
  animate: { 
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 24
    }
  },
  exit: {
    opacity: 0,
    x: -10,
    transition: {
      duration: 0.2
    }
  }
}

// Usage
<motion.ul variants={staggerContainer} initial="initial" animate="animate">
  {items.map(item => (
    <motion.li key={item.id} variants={staggerItem}>
      {item.content}
    </motion.li>
  ))}
</motion.ul>
```

### Collapse/Expand Section

**When to use:** Sidebar sections, accordions

```typescript
const collapseExpand = {
  collapsed: {
    height: 0,
    opacity: 0,
    transition: {
      height: {
        duration: 0.3,
        ease: "easeInOut"
      },
      opacity: {
        duration: 0.2,
        ease: "easeIn"
      }
    }
  },
  expanded: {
    height: "auto",
    opacity: 1,
    transition: {
      height: {
        duration: 0.3,
        ease: "easeOut"
      },
      opacity: {
        duration: 0.3,
        delay: 0.1,
        ease: "easeOut"
      }
    }
  }
}

// Usage with AnimatePresence
<AnimatePresence initial={false}>
  {isExpanded && (
    <motion.div
      initial="collapsed"
      animate="expanded"
      exit="collapsed"
      variants={collapseExpand}
      style={{ overflow: "hidden" }}
    >
      Content
    </motion.div>
  )}
</AnimatePresence>
```

### Sidebar Collapse/Expand

**When to use:** Main sidebar width transition

```typescript
const sidebarTransition = {
  collapsed: {
    width: 64,
    transition: {
      width: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }
    }
  },
  expanded: {
    width: 280,
    transition: {
      width: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }
    }
  }
}

// Content fade based on sidebar state
const sidebarContent = {
  collapsed: {
    opacity: 0,
    x: -10,
    transition: {
      duration: 0.15
    }
  },
  expanded: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.2,
      delay: 0.15
    }
  }
}
```

### Modal Overlay

**When to use:** Modal backgrounds

```typescript
const modalOverlay = {
  initial: { 
    opacity: 0,
    backdropFilter: "blur(0px)"
  },
  animate: { 
    opacity: 1,
    backdropFilter: "blur(8px)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  exit: { 
    opacity: 0,
    backdropFilter: "blur(0px)",
    transition: {
      duration: 0.15,
      ease: "easeIn"
    }
  }
}
```

---

## Interactive Animations

### Typing Indicator

**When to use:** AI is thinking/responding

```typescript
const typingDot = {
  animate: {
    y: [0, -8, 0],
    scale: [1, 1.1, 1],
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 0.8,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
}

// Create three dots with staggered delays
const dot1Variant = {
  animate: {
    ...typingDot.animate,
    transition: {
      ...typingDot.animate.transition,
      delay: 0
    }
  }
}

const dot2Variant = {
  animate: {
    ...typingDot.animate,
    transition: {
      ...typingDot.animate.transition,
      delay: 0.15
    }
  }
}

const dot3Variant = {
  animate: {
    ...typingDot.animate,
    transition: {
      ...typingDot.animate.transition,
      delay: 0.3
    }
  }
}

// Usage
<div className="flex gap-1">
  <motion.div variants={dot1Variant} animate="animate" />
  <motion.div variants={dot2Variant} animate="animate" />
  <motion.div variants={dot3Variant} animate="animate" />
</div>
```

### File Upload Progress

**When to use:** File upload indicators

```typescript
const uploadProgress = {
  initial: { 
    scaleX: 0,
    opacity: 0.7
  },
  animate: (progress: number) => ({
    scaleX: progress / 100,
    opacity: 1,
    transition: {
      scaleX: {
        duration: 0.3,
        ease: "easeOut"
      },
      opacity: {
        duration: 0.2
      }
    }
  })
}

// Usage
<motion.div
  initial="initial"
  animate="animate"
  custom={uploadProgress}
  style={{ transformOrigin: "left" }}
  className="h-1 bg-gradient-to-r from-purple-500 to-blue-500"
/>
```

### Drag and Drop Zone

**When to use:** File drop areas in chat input

```typescript
const dropZone = {
  idle: {
    scale: 1,
    borderColor: "rgba(209, 213, 219, 1)",
    backgroundColor: "transparent"
  },
  dragOver: {
    scale: 1.02,
    borderColor: "rgba(139, 92, 246, 1)",
    backgroundColor: "rgba(139, 92, 246, 0.05)",
    boxShadow: "0 0 0 3px rgba(139, 92, 246, 0.1)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  drop: {
    scale: 0.98,
    transition: {
      duration: 0.1
    }
  }
}
```

### Send Button States

**When to use:** Chat input send button

```typescript
const sendButton = {
  idle: {
    scale: 1,
    rotate: 0
  },
  hover: {
    scale: 1.1,
    boxShadow: "0 4px 16px rgba(139, 92, 246, 0.4)",
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  tap: {
    scale: 0.9,
    transition: {
      duration: 0.1
    }
  },
  sending: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear"
    }
  }
}
```

### Glow Effect (Focus/Hover)

**When to use:** Important CTAs, active inputs

```typescript
const glowEffect = {
  idle: {
    boxShadow: "0 0 0 rgba(139, 92, 246, 0)"
  },
  hover: {
    boxShadow: "0 0 20px rgba(139, 92, 246, 0.4)",
    transition: {
      duration: 0.3,
      ease: "easeOut"
    }
  },
  focus: {
    boxShadow: "0 0 0 3px rgba(139, 92, 246, 0.3)",
    transition: {
      duration: 0.2
    }
  }
}
```

---

## Loading States

### Skeleton Loader

**When to use:** Content loading placeholders

```typescript
const shimmer = {
  animate: {
    backgroundPosition: ["200% 0", "-200% 0"],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "linear"
    }
  }
}

// Apply to element with gradient background
const shimmerGradient = 
  "linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.1), transparent)"

// Usage
<motion.div
  variants={shimmer}
  animate="animate"
  style={{
    background: shimmerGradient,
    backgroundSize: "200% 100%"
  }}
  className="h-4 rounded"
/>
```

### Spinner

**When to use:** General loading states

```typescript
const spinner = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear"
    }
  }
}

// With gradient border
<motion.div
  variants={spinner}
  animate="animate"
  className="w-8 h-8 rounded-full border-2 border-transparent"
  style={{
    borderTopColor: "#8B5CF6",
    borderRightColor: "#3B82F6"
  }}
/>
```

### Pulse

**When to use:** Subtle loading indicators

```typescript
const pulse = {
  animate: {
    opacity: [0.5, 1, 0.5],
    scale: [1, 1.05, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
}
```

### Progress Bar

**When to use:** Determinate progress

```typescript
const progressBar = {
  initial: { 
    width: "0%" 
  },
  animate: (progress: number) => ({
    width: `${progress}%`,
    transition: {
      duration: 0.5,
      ease: "easeOut"
    }
  })
}
```

---

## Implementation Examples

### Complete Message Component

```typescript
import { motion } from 'framer-motion'

const Message = ({ content, isNew }) => {
  const messageVariants = {
    initial: { 
      opacity: 0,
      y: 20,
      scale: 0.95
    },
    animate: { 
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 260,
        damping: 20
      }
    }
  }

  return (
    <motion.div
      variants={messageVariants}
      initial={isNew ? "initial" : false}
      animate="animate"
      className="message"
    >
      {content}
    </motion.div>
  )
}
```

### Complete Session List

```typescript
import { motion, AnimatePresence } from 'framer-motion'

const SessionList = ({ sessions }) => {
  const containerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1
      }
    }
  }

  const itemVariants = {
    initial: { 
      opacity: 0,
      x: -20
    },
    animate: { 
      opacity: 1,
      x: 0
    },
    exit: {
      opacity: 0,
      x: -10
    },
    hover: {
      scale: 1.02,
      backgroundColor: "rgba(139, 92, 246, 0.1)"
    },
    tap: {
      scale: 0.98
    }
  }

  return (
    <motion.ul
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <AnimatePresence>
        {sessions.map(session => (
          <motion.li
            key={session.id}
            variants={itemVariants}
            exit="exit"
            whileHover="hover"
            whileTap="tap"
            layout
          >
            {session.title}
          </motion.li>
        ))}
      </AnimatePresence>
    </motion.ul>
  )
}
```

### Complete Modal

```typescript
import { motion, AnimatePresence } from 'framer-motion'

const Modal = ({ isOpen, onClose, children }) => {
  const overlayVariants = {
    initial: { 
      opacity: 0,
      backdropFilter: "blur(0px)"
    },
    animate: { 
      opacity: 1,
      backdropFilter: "blur(8px)"
    },
    exit: { 
      opacity: 0,
      backdropFilter: "blur(0px)"
    }
  }

  const modalVariants = {
    initial: { 
      scale: 0.9,
      opacity: 0,
      y: 20
    },
    animate: { 
      scale: 1,
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 25
      }
    },
    exit: { 
      scale: 0.95,
      opacity: 0,
      y: 10,
      transition: {
        duration: 0.2
      }
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            onClick={onClose}
            className="fixed inset-0 bg-black/50"
          />
          <motion.div
            variants={modalVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed inset-0 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl p-8 max-w-md w-full">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
```

### Complete Collapsible Section

```typescript
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

const CollapsibleSection = ({ title, children }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  const iconVariants = {
    collapsed: { rotate: 0 },
    expanded: { rotate: 90 }
  }

  const contentVariants = {
    collapsed: {
      height: 0,
      opacity: 0,
      transition: {
        height: { duration: 0.3, ease: "easeInOut" },
        opacity: { duration: 0.2, ease: "easeIn" }
      }
    },
    expanded: {
      height: "auto",
      opacity: 1,
      transition: {
        height: { duration: 0.3, ease: "easeOut" },
        opacity: { duration: 0.3, delay: 0.1, ease: "easeOut" }
      }
    }
  }

  return (
    <div>
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full"
        whileHover={{ backgroundColor: "rgba(139, 92, 246, 0.05)" }}
        whileTap={{ scale: 0.98 }}
      >
        <span>{title}</span>
        <motion.div
          variants={iconVariants}
          animate={isExpanded ? "expanded" : "collapsed"}
          transition={{ duration: 0.2 }}
        >
          →
        </motion.div>
      </motion.button>

      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            variants={contentVariants}
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            style={{ overflow: "hidden" }}
          >
            <div className="pt-2">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
```

---

## Performance Tips

### 1. Use Layout Animations Wisely

```typescript
// ✅ Good - Animate transform/opacity
<motion.div animate={{ x: 100, opacity: 1 }} />

// ❌ Bad - Animate width/height
<motion.div animate={{ width: 200, height: 100 }} />

// ✅ Better - Use scale instead
<motion.div animate={{ scaleX: 2, scaleY: 1 }} />
```

### 2. Reduce Motion Support

```typescript
import { useReducedMotion } from 'framer-motion'

const MyComponent = () => {
  const shouldReduceMotion = useReducedMotion()

  const variants = shouldReduceMotion
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 }
      }
    : {
        initial: { opacity: 0, y: 20, scale: 0.95 },
        animate: { opacity: 1, y: 0, scale: 1 }
      }

  return <motion.div variants={variants} />
}
```

### 3. Batch Animations

```typescript
// ✅ Good - Single animation for multiple properties
<motion.div animate={{ x: 100, y: 100, opacity: 1 }} />

// ❌ Bad - Multiple separate animations
<motion.div animate={{ x: 100 }}>
  <motion.div animate={{ y: 100 }}>
    <motion.div animate={{ opacity: 1 }} />
  </motion.div>
</motion.div>
```

### 4. Use will-change Sparingly

```typescript
// Only for animations you know will happen soon
<motion.div
  style={{ willChange: "transform" }}
  whileHover={{ scale: 1.1 }}
/>

// Remove after animation completes
<motion.div
  onAnimationStart={() => element.style.willChange = "transform"}
  onAnimationComplete={() => element.style.willChange = "auto"}
/>
```

---

**Last Updated:** 2025-10-12
**Version:** 1.0.0
**Status:** ✅ Ready for Implementation