# Cirkelline Design System v2.0

> A modern, elegant, and highly animated design system inspired by Gemini's structure, Claude's elegance, and VSCode's technical prowess.

---

## 🎨 Design Philosophy

**Vision:** Create a sophisticated, universally accessible AI assistant interface that feels alive through rich animations while maintaining professional polish and technical depth.

**Core Principles:**
1. **Elegance First** - Clean, spacious layouts with purposeful whitespace
2. **Rich Animations** - Every interaction should feel fluid and delightful
3. **Universal Access** - Design for everyone, from developers to general users
4. **Information Dense** - Sidebar as the command center for all features
5. **Performance** - Smooth 60fps animations without compromising speed

---

## 🌈 Color System

### Primary Palette

**Light Theme:**
```css
--bg-primary: #FAFBFC;           /* Main background - soft white */
--bg-secondary: #F4F6F8;         /* Secondary surfaces */
--bg-surface: #FFFFFF;           /* Cards, panels, elevated surfaces */
--bg-elevated: #FFFFFF;          /* Modals, dropdowns - with shadow */

--text-primary: #0D1117;         /* Main text - near black */
--text-secondary: #57606A;       /* Secondary text - cool gray */
--text-tertiary: #8B949E;        /* Tertiary text - lighter gray */
--text-placeholder: #A8B1BB;     /* Placeholder text */

--border-primary: #D0D7DE;       /* Main borders */
--border-secondary: #E7ECF0;     /* Subtle borders */
--border-focus: #0969DA;         /* Focus states */
```

**Dark Theme:**
```css
--bg-primary: #0D1117;           /* Main background - deep space */
--bg-secondary: #161B22;         /* Secondary surfaces */
--bg-surface: #1C2128;           /* Cards, panels, elevated surfaces */
--bg-elevated: #22272E;          /* Modals, dropdowns */

--text-primary: #E6EDF3;         /* Main text - soft white */
--text-secondary: #9DA5B0;       /* Secondary text - cool gray */
--text-tertiary: #6E7681;        /* Tertiary text - darker gray */
--text-placeholder: #4F5661;     /* Placeholder text */

--border-primary: #30363D;       /* Main borders */
--border-secondary: #21262D;     /* Subtle borders */
--border-focus: #1F6FEB;         /* Focus states */
```

### Accent & Semantic Colors

**Brand Accent (Gradient-Based):**
```css
/* Primary Gradient: Purple → Blue */
--accent-start: #8B5CF6;         /* Vibrant purple */
--accent-end: #3B82F6;           /* Bright blue */
--accent-gradient: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%);

/* Hover states */
--accent-hover-start: #7C3AED;
--accent-hover-end: #2563EB;

/* Active states */
--accent-active-start: #6D28D9;
--accent-active-end: #1D4ED8;
```

**Secondary Accent (Warm):**
```css
--secondary-accent: #F59E0B;     /* Amber for highlights */
--secondary-accent-hover: #D97706;
```

**Semantic Colors:**
```css
/* Success - Green */
--success: #10B981;
--success-bg: rgba(16, 185, 129, 0.1);
--success-border: rgba(16, 185, 129, 0.2);

/* Error - Red */
--error: #EF4444;
--error-bg: rgba(239, 68, 68, 0.1);
--error-border: rgba(239, 68, 68, 0.2);

/* Warning - Amber */
--warning: #F59E0B;
--warning-bg: rgba(245, 158, 11, 0.1);
--warning-border: rgba(245, 158, 11, 0.2);

/* Info - Blue */
--info: #3B82F6;
--info-bg: rgba(59, 130, 246, 0.1);
--info-border: rgba(59, 130, 246, 0.2);
```

### Color Usage Guidelines

1. **Backgrounds:** Use the layered system (primary → secondary → surface → elevated)
2. **Gradients:** Apply to CTAs, accents, and highlights only
3. **Semantic Colors:** Reserve for status indicators and feedback
4. **Text Hierarchy:** primary (headings) → secondary (body) → tertiary (captions)

---

## 📝 Typography

### Font Stack

```css
--font-sans: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
--font-heading: 'Alan Sans', 'Ubuntu', system-ui, sans-serif;
--font-mono: 'Ubuntu Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace;
```

### Type Scale

**Display (Hero text):**
```css
font-size: 48px;
line-height: 56px;
font-weight: 700;
letter-spacing: -0.02em;
```

**H1 (Page titles):**
```css
font-size: 32px;
line-height: 40px;
font-weight: 600;
letter-spacing: -0.01em;
font-family: var(--font-heading);
```

**H2 (Section headers):**
```css
font-size: 24px;
line-height: 32px;
font-weight: 600;
letter-spacing: -0.005em;
font-family: var(--font-heading);
```

**H3 (Subsection headers):**
```css
font-size: 18px;
line-height: 28px;
font-weight: 600;
font-family: var(--font-heading);
```

**Body Large:**
```css
font-size: 16px;
line-height: 24px;
font-weight: 400;
```

**Body (Default):**
```css
font-size: 14px;
line-height: 20px;
font-weight: 400;
```

**Body Small:**
```css
font-size: 12px;
line-height: 18px;
font-weight: 400;
```

**Caption:**
```css
font-size: 11px;
line-height: 16px;
font-weight: 400;
color: var(--text-tertiary);
```

**Code:**
```css
font-family: var(--font-mono);
font-size: 13px;
line-height: 20px;
```

---

## 📏 Spacing Scale

**Base unit:** 4px (0.25rem)

```css
--space-1: 4px;    /* 0.25rem */
--space-2: 8px;    /* 0.5rem */
--space-3: 12px;   /* 0.75rem */
--space-4: 16px;   /* 1rem */
--space-5: 20px;   /* 1.25rem */
--space-6: 24px;   /* 1.5rem */
--space-8: 32px;   /* 2rem */
--space-10: 40px;  /* 2.5rem */
--space-12: 48px;  /* 3rem */
--space-16: 64px;  /* 4rem */
--space-20: 80px;  /* 5rem */
--space-24: 96px;  /* 6rem */
```

**Usage:**
- **Tight:** space-1, space-2 (inline elements, icons)
- **Normal:** space-3, space-4 (component padding)
- **Relaxed:** space-6, space-8 (section spacing)
- **Spacious:** space-12, space-16 (page sections)

---

## 🎬 Animation System

### Animation Principles

1. **Purpose-Driven:** Every animation should communicate state or guide attention
2. **Performant:** Use transforms and opacity (GPU-accelerated)
3. **Natural:** Prefer spring physics over linear easing
4. **Consistent:** Reuse timing functions and durations

### Core Timing

```css
/* Durations */
--duration-instant: 0ms;
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;
--duration-slower: 600ms;

/* Easing curves */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-spring: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Framer Motion Presets

**Spring Config (Default):**
```typescript
const spring = {
  type: "spring",
  stiffness: 300,
  damping: 30
}
```

**Spring Config (Bouncy):**
```typescript
const springBouncy = {
  type: "spring",
  stiffness: 400,
  damping: 20
}
```

**Spring Config (Smooth):**
```typescript
const springSmooth = {
  type: "spring",
  stiffness: 200,
  damping: 25
}
```

### Animation Patterns

**1. Fade In (Entry):**
```typescript
const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.15 }
}
```

**2. Slide Up (Messages, Modals):**
```typescript
const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
  transition: { type: "spring", stiffness: 300, damping: 30 }
}
```

**3. Scale (Buttons, Interactive Elements):**
```typescript
const scale = {
  whileHover: { scale: 1.05 },
  whileTap: { scale: 0.95 },
  transition: { type: "spring", stiffness: 400, damping: 20 }
}
```

**4. Stagger (Lists, Sessions):**
```typescript
const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.05
    }
  }
}

const staggerItem = {
  initial: { opacity: 0, x: -10 },
  animate: { opacity: 1, x: 0 }
}
```

**5. Collapse/Expand (Sections):**
```typescript
const collapse = {
  initial: { height: 0, opacity: 0 },
  animate: { 
    height: "auto", 
    opacity: 1,
    transition: { duration: 0.3, ease: "easeOut" }
  },
  exit: { 
    height: 0, 
    opacity: 0,
    transition: { duration: 0.2, ease: "easeIn" }
  }
}
```

**6. Typing Indicator:**
```typescript
const typingDot = {
  animate: {
    y: [0, -8, 0],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
}

// Stagger the dots
const dot1 = { ...typingDot, transition: { ...typingDot.transition, delay: 0 } }
const dot2 = { ...typingDot, transition: { ...typingDot.transition, delay: 0.1 } }
const dot3 = { ...typingDot, transition: { ...typingDot.transition, delay: 0.2 } }
```

**7. File Upload Progress:**
```typescript
const uploadProgress = {
  initial: { scaleX: 0, opacity: 0.7 },
  animate: { 
    scaleX: 1, 
    opacity: 1,
    transition: { duration: 0.8, ease: "easeOut" }
  }
}
```

**8. Glow Effect (Focus, Hover):**
```typescript
const glow = {
  whileHover: {
    boxShadow: "0 0 20px rgba(139, 92, 246, 0.3)",
    transition: { duration: 0.2 }
  }
}
```

---

## 🎯 Component Specifications

### Sidebar

**Layout:**
- Width: 280px (expanded), 64px (collapsed)
- Height: 100vh
- Position: Fixed left
- Transition: 300ms ease-in-out

**Structure:**
```
┌─────────────────────────────┐
│ Header + Logo + Collapse    │ 64px
├─────────────────────────────┤
│ New Session Button          │ Auto
├─────────────────────────────┤
│ Sessions (Collapsible)      │ Scroll
│ ├─ Session Item 1           │
│ ├─ Session Item 2           │
│ └─ Session Item 3           │
├─────────────────────────────┤
│ Projects (Collapsible)      │ Scroll
├─────────────────────────────┤
│ Journals (Collapsible)      │ Scroll
└─────────────────────────────┘
```

**Animations:**
- **Collapse/Expand:** Width transition + content fade
- **Section Toggle:** Smooth height animation with rotation icon
- **Session Items:** Stagger on load, hover scale (1.02)
- **New Button:** Gradient shimmer on hover, scale on click

### Top Bar

**Layout:**
- Height: 64px
- Position: Fixed top
- Background: Translucent with backdrop blur
- Elevation: Shadow on scroll

**Structure:**
```
┌──────────────────────────────────────────────────┐
│ [Mobile Menu] [Logo?] ... [User Dropdown]        │
└──────────────────────────────────────────────────┘
```

**Animations:**
- **Scroll Elevation:** Shadow intensity increases on scroll
- **User Dropdown:** Slide down + fade in
- **Mobile Menu:** Slide from left with overlay

### Chat Area

**Layout:**
- Max Width: 800px
- Margin: 0 auto
- Padding: 24px
- Scroll: Smooth with stick-to-bottom

**Structure:**
```
┌─────────────────────────────────────┐
│                                     │
│  [Blank State / Messages]           │
│                                     │
│  Message 1                          │
│  Message 2                          │
│  Message 3                          │
│  [Typing Indicator]                 │
│                                     │
└─────────────────────────────────────┘
```

**Message Layout:**
```
[Icon] [Content]
       ├─ Text (Markdown)
       ├─ Images (Grid)
       ├─ Videos (Grid)
       └─ Audios (List)
```

**Animations:**
- **Message Entry:** Slide up + fade (100ms delay between messages)
- **Typing Indicator:** Three bouncing dots
- **Code Blocks:** Syntax highlight with fade-in
- **Images:** Progressive blur-up loading
- **Scroll to Bottom:** Smooth scroll with FAB button

### Chat Input

**Layout:**
- Position: Fixed bottom (within main content)
- Background: Surface color
- Border: Top border
- Padding: 16px

**Structure:**
```
┌─────────────────────────────────────┐
│ [File Previews]                     │
├─────────────────────────────────────┤
│ [Upload to Knowledge Button]        │
├─────────────────────────────────────┤
│ ┌────────────────────────────────┐  │
│ │ Textarea                     ↑│  │
│ │ [Attach] [@] [/] [Send ●]    ││  │
│ └────────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Animations:**
- **Textarea Auto-grow:** Smooth height transition
- **Send Button:** 
  - Idle: Subtle pulse
  - Hover: Gradient shimmer + scale (1.1)
  - Click: Scale (0.9) → Loading spinner
- **File Attach:** Ripple effect on click
- **Drag & Drop:** 
  - Drag Over: Border glow + scale (1.02)
  - Drop: Success bounce
- **File Preview:** Slide up + stagger

### Modals

**Layout:**
- Max Width: 500px
- Background: Elevated surface
- Border Radius: 16px
- Padding: 32px
- Overlay: rgba(0, 0, 0, 0.5) with backdrop blur

**Animations:**
- **Open:** Scale (0.9 → 1) + fade + backdrop blur
- **Close:** Scale (1 → 0.95) + fade out
- **Form Fields:** Sequential fade-in (50ms stagger)

---

## 🎪 Micro-Interactions

### Hover States

**Default Interactive Elements:**
```css
transition: all 0.15s ease;
transform: translateY(-1px);
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
```

**Buttons:**
- Scale: 1.05
- Gradient shift (if gradient)
- Shadow elevation
- Cursor: pointer

**Links:**
- Color shift to accent
- Underline animation (left → right)

**Cards:**
- Lift effect (translateY -2px)
- Border glow (accent color)
- Shadow elevation

### Focus States

**All Focusable Elements:**
```css
outline: 2px solid var(--border-focus);
outline-offset: 2px;
border-radius: 4px;
```

**With Animation:**
- Ring expands from center
- Glow pulse effect

### Loading States

**Skeleton Loaders:**
- Background gradient animation (shimmer effect)
- Pulse opacity (0.5 → 1)

**Spinners:**
- Rotate 360° (1s infinite)
- Smooth easing

**Progress Bars:**
- Width animation (0% → 100%)
- Gradient slide animation

---

## 📱 Responsive Breakpoints

```css
/* Mobile First Approach */
--breakpoint-sm: 640px;   /* Small devices */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large desktop */
--breakpoint-2xl: 1536px; /* Extra large */
```

**Sidebar Behavior:**
- Mobile (< 768px): Hidden, overlay on trigger
- Desktop (>= 768px): Persistent, collapsible

**Chat Width:**
- Mobile: 100% - 32px padding
- Desktop: 800px max-width, centered

---

## 🔧 Implementation Utilities

### CSS Custom Properties Structure

```css
:root {
  /* Colors */
  --color-bg-primary: ...;
  --color-text-primary: ...;
  
  /* Spacing */
  --space-4: 16px;
  
  /* Typography */
  --font-sans: ...;
  --text-body: ...;
  
  /* Animation */
  --duration-normal: 250ms;
  --ease-in-out: ...;
  
  /* Shadows */
  --shadow-sm: ...;
  --shadow-md: ...;
  --shadow-lg: ...;
}
```

### Tailwind Extensions

**Custom Utilities:**
```javascript
// tailwind.config.ts
extend: {
  animation: {
    'fade-in': 'fadeIn 0.15s ease-out',
    'slide-up': 'slideUp 0.25s ease-out',
    'shimmer': 'shimmer 2s infinite',
    'bounce-dot': 'bounceDot 0.6s infinite ease-in-out',
  },
  keyframes: {
    fadeIn: { ... },
    slideUp: { ... },
    shimmer: { ... },
    bounceDot: { ... },
  }
}
```

---

## ✅ Accessibility

**Keyboard Navigation:**
- All interactive elements: Tab-accessible
- Custom focus indicators (high contrast)
- Skip links for main content

**Screen Readers:**
- Semantic HTML
- ARIA labels for icons
- Live regions for dynamic content

**Color Contrast:**
- WCAG AA minimum (4.5:1 text)
- AAA for important text (7:1)
- Test with color blindness simulators

**Motion:**
- Respect `prefers-reduced-motion`
- Provide toggle in settings
- Essential animations only when reduced

---

## 🚀 Performance Guidelines

**Animation Performance:**
1. Use `transform` and `opacity` only (GPU-accelerated)
2. Avoid animating: width, height, margin, padding
3. Use `will-change` sparingly
4. Batch animations with `AnimatePresence`

**Loading Strategy:**
1. Lazy load images with blur placeholders
2. Code-split by route
3. Preload critical fonts
4. Use React.memo for expensive components

**Bundle Size:**
1. Tree-shake unused Framer Motion features
2. Use dynamic imports for modals
3. Optimize SVG icons
4. Compress assets

---

## 📦 Component Library Structure

```
components/
├── animations/
│   ├── FadeIn.tsx
│   ├── SlideUp.tsx
│   ├── Stagger.tsx
│   └── TypingIndicator.tsx
├── ui/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Modal.tsx
│   └── Card.tsx
├── chat/
│   ├── ChatArea/
│   ├── ChatInput/
│   ├── Message/
│   └── TypingIndicator/
├── sidebar/
│   ├── Sidebar.tsx
│   ├── SessionItem.tsx
│   └── SidebarSection.tsx
└── layout/
    ├── TopBar.tsx
    └── MainContent.tsx
```

---

## 🎨 Design Tokens (Figma/Code Sync)

**Recommended Tool:** Style Dictionary

**Token Structure:**
```json
{
  "color": {
    "bg": {
      "primary": { "value": "#FAFBFC" },
      "surface": { "value": "#FFFFFF" }
    }
  },
  "spacing": {
    "4": { "value": "16px" }
  }
}
```

---

## 📚 Resources

**Inspiration Sources:**
- Gemini: Mobile structure, button styles
- Claude: Elegant spacing, professional tone
- VSCode: Technical depth, information density
- Linear: Smooth animations, micro-interactions
- Vercel: Clean aesthetics, gradient usage

**Tools:**
- Figma: Design mockups
- Framer: Prototype animations
- Tailwind: Utility-first CSS
- Framer Motion: React animations
- Radix UI: Accessible primitives

---

**Last Updated:** 2025-10-12
**Version:** 2.0.0
**Status:** ✅ Ready for Implementation