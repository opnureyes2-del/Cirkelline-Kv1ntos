# Integration Design Pattern

**Last Updated:** 2025-11-11
**Status:** ✅ Production Standard

This document defines the **exact design pattern** for all service integrations (Gmail, Calendar, Notion, Tasks, and future services). Following this pattern ensures visual consistency, smooth animations, and a unified user experience.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture: Unified Container](#architecture-unified-container)
3. [Design Specifications](#design-specifications)
4. [Header Control System](#header-control-system)
5. [Fullscreen System](#fullscreen-system)
6. [Calendar Header Design](#calendar-header-design)
7. [Scrollbar Architecture](#scrollbar-architecture)
8. [User-Adjustable Panel Height](#user-adjustable-panel-height)
9. [Adding a New Service](#adding-a-new-service)
10. [Color System](#color-system)
11. [Animation Standards](#animation-standards)
12. [Testing Checklist](#testing-checklist)
13. [Examples](#examples)

---

## Overview

### The Problem We Solved

**Before:** Separate components for each service caused "flashing" when switching:
- `GooglePanelContainer` (email + calendar)
- `NotionPanel` (separate component)
- Result: Switching between services unmounted one component and mounted another, causing visible close/open animations

**After:** Single unified container handles all services:
- `ServicePanelContainer` (email + calendar + notion + future services)
- Result: Switching just swaps content smoothly - panel stays open, no flashing

### Key Principle

> **"All integrations MUST live in the same container and follow the same design system."**

---

## Architecture: Unified Container

### File Structure

```
/src/components/
  ├── ServicePanelContainer.tsx     ← MAIN: Handles ALL services
  ├── TopBar.tsx                     ← Service icon buttons
  └── [Old files - DO NOT USE]
      ├── GooglePanelContainer.tsx   ← Deprecated
      ├── EmailPanel.tsx             ← Deprecated
      ├── CalendarPanel.tsx          ← Deprecated
      └── NotionPanel.tsx            ← Deprecated
```

### Component Hierarchy

```typescript
ServicePanelContainer
  ├── Header (sticky, conditional back button)
  ├── Error Display (conditional)
  └── Content (switches based on openPanel)
      ├── Email Content (when openPanel === 'email')
      ├── Calendar Content (when openPanel === 'calendar')
      ├── Notion Content (when openPanel === 'notion')
      └── [Future Service] (when openPanel === 'newservice')
```

### Integration Flow

```
User clicks service icon in TopBar
  ↓
TopBar calls onPanelChange('servicename')
  ↓
page.tsx updates openPanel state
  ↓
ServicePanelContainer receives new openPanel prop
  ↓
Content area swaps to new service (smooth, no unmount)
  ↓
Header updates title accordingly
```

---

## Design Specifications

### Container Dimensions

```typescript
// Exact specifications
height: 'calc((100vh - 64px) * {panelHeight})'  // User-adjustable (default: 0.5 = 50%)
width: '100%'                                    // Full width (no max-width constraint)
overflow: 'hidden'                               // Outer container
overflowY: 'auto'                                // Inner scrollable area
position: 'relative'                             // For resize handle positioning

// Height constraints
minHeight: 20% (0.2)  // Minimum panel height
maxHeight: 80% (0.8)  // Maximum panel height
default: 50% (0.5)    // Default panel height
```

**NEW:** The panel is now **full width** (no max-width constraint) and **user-resizable** via drag handle. Users can adjust the panel height between 20% and 80% of the viewport.

### Header Specifications

```typescript
// Header (sticky at top)
padding: 'px-6 py-1.5'           // Horizontal 24px, Vertical 6px
position: 'sticky top-0 z-10'
background: 'bg-light-bg dark:bg-dark-bg'
border: 'border-b border-gray-200 dark:border-gray-700'

// Title
fontSize: 'text-sm'              // 14px
fontWeight: 'font-medium'        // 500
color: 'text-light-text dark:text-dark-text'

// Icons (back button, close button)
size: 16                         // pixels
padding: 'p-1'                   // 4px
border-radius: 'rounded-lg'      // 8px
hover: 'hover:bg-accent/10'
color: 'text-light-text/60 dark:text-dark-text/60'
```

### Content Specifications

```typescript
// List items
padding: 'px-6 py-4'             // Horizontal 24px, Vertical 16px
hover: 'hover:bg-light-bg dark:hover:bg-dark-bg'
divider: 'divide-y divide-gray-200 dark:divide-gray-700'

// Text hierarchy
Primary title:   'text-sm font-medium text-light-text dark:text-dark-text'
Secondary text:  'text-xs text-light-text/70 dark:text-dark-text/70'
Muted text:      'text-xs text-light-text/50 dark:text-dark-text/50'

// Empty states
padding: 'px-6 py-12'
alignment: 'text-center'
color: 'text-light-text/60 dark:text-dark-text/60'

// Forms
padding: 'p-6 space-y-4'
inputs: 'px-4 py-2 rounded-lg'
border: 'border-gray-300 dark:border-gray-600'
focus: 'focus:border-accent'
```

---

## Header Control System

### The Unified Button Pattern

**⚠️ CRITICAL RULE:** All service panels MUST have the same header control buttons in the exact same order.

### Button Order (Left to Right)

```
[Back Button] [Service Title/Controls] [SPACER] [Sync Button] [Fullscreen Button] [Close Button]
```

**File:** `ServicePanelContainer.tsx` (Lines 471-555)

### Visual Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  [←] Service Title      [🗘] [⛶] [✕]                             │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │
│                                                                  │
│  [Service Content]                                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Sync Button Specification

**Purpose:** Refresh service data (emails, calendar events, tasks, notion databases)

**Implementation:**

```typescript
// Lines 471-516 in ServicePanelContainer.tsx
{/* Sync Button - show for all panels */}
{(openPanel === 'email' || openPanel === 'calendar' || openPanel === 'tasks' || openPanel === 'notion') && (
  <button
    onClick={() => {
      if (openPanel === 'email') {
        emailData.fetchEmails(20);
      } else if (openPanel === 'calendar') {
        calendarData.fetchEvents();
      } else if (openPanel === 'tasks') {
        tasksData.fetchTaskLists();
      } else if (openPanel === 'notion') {
        handleSyncDatabases();
      }
    }}
    disabled={
      openPanel === 'email' ? emailData.loading :
      openPanel === 'calendar' ? calendarData.loading :
      openPanel === 'tasks' ? tasksData.loading :
      (isSyncing || notionData.loading)
    }
    className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    aria-label={`Sync ${openPanel}`}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={
        (openPanel === 'email' && emailData.loading) ||
        (openPanel === 'calendar' && calendarData.loading) ||
        (openPanel === 'tasks' && tasksData.loading) ||
        (openPanel === 'notion' && isSyncing)
          ? 'animate-spin'
          : ''
      }
    >
      <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
    </svg>
  </button>
)}
```

**Visual Specifications:**
- **Icon Size:** 13x13 pixels (width="13" height="13")
- **Padding:** p-1 (4px all around)
- **Border Radius:** rounded-lg (8px)
- **Hover:** bg-accent/10 (10% accent color)
- **Disabled:** opacity-50 + cursor-not-allowed
- **Loading State:** animate-spin class applied to SVG
- **Color:** text-light-text/60 dark:text-dark-text/60 (60% opacity)

**Behavior:**
- Calls service-specific fetch function when clicked
- Shows spinning animation while loading
- Disabled during loading to prevent duplicate requests
- Loading state managed independently per service

### Fullscreen Button Specification

**Purpose:** Toggle fullscreen mode (panel expands to 100%, chat area hidden)

**Implementation:**

```typescript
// Lines 518-544 in ServicePanelContainer.tsx
{/* Fullscreen Toggle Button */}
<button
  onClick={onFullscreenToggle}
  className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
  aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
>
  {isFullscreen ? (
    <Minimize2 size={13} />
  ) : (
    <Maximize2 size={13} />
  )}
</button>
```

**Visual Specifications:**
- **Icon Size:** 13 pixels (Lucide icons)
- **Padding:** p-1 (4px all around)
- **Border Radius:** rounded-lg (8px)
- **Hover:** bg-accent/10 (10% accent color)
- **Color:** text-light-text/60 dark:text-dark-text/60 (60% opacity)
- **Icons Used:**
  - `Maximize2` - When not fullscreen (expand icon)
  - `Minimize2` - When fullscreen (compress icon)

**Behavior:**
- Toggles `isFullscreen` state via `onFullscreenToggle` callback
- Icon changes based on current fullscreen state
- See [Fullscreen System](#fullscreen-system) for complete details

### Close Button Specification

**Purpose:** Close the service panel

**Implementation:**

```typescript
// Lines 546-555 in ServicePanelContainer.tsx
{/* Close button */}
<button
  onClick={onClose}
  className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
  aria-label="Close panel"
>
  <X size={13} />
</button>
```

**Visual Specifications:**
- **Icon Size:** 13 pixels (X icon from Lucide)
- **Padding:** p-1 (4px all around)
- **Border Radius:** rounded-lg (8px)
- **Hover:** bg-accent/10 (10% accent color)
- **Color:** text-light-text/60 dark:text-dark-text/60 (60% opacity)

**Behavior:**
- Calls `onClose` callback which sets `openPanel` to null
- Panel closes with smooth animation
- If in fullscreen mode, also resets fullscreen state (see defensive useEffect)

### Button Spacing

```typescript
// All control buttons are within a gap-2 container
<div className="flex items-center gap-2">
  {/* Sync Button */}
  {/* Fullscreen Button */}
  {/* Close Button */}
</div>
```

**Gap:** 8px between buttons (gap-2)

### Adding Sync/Fullscreen to New Services

When adding a new service, ensure:

1. **Sync button condition includes new service:**
   ```typescript
   {(openPanel === 'email' || openPanel === 'calendar' || openPanel === 'tasks' || openPanel === 'notion' || openPanel === 'newservice') && (
   ```

2. **Sync handler includes new service:**
   ```typescript
   onClick={() => {
     if (openPanel === 'email') {
       emailData.fetchEmails(20);
     } else if (openPanel === 'calendar') {
       calendarData.fetchEvents();
     } else if (openPanel === 'tasks') {
       tasksData.fetchTaskLists();
     } else if (openPanel === 'notion') {
       handleSyncDatabases();
     } else if (openPanel === 'newservice') {
       handleNewServiceSync();
     }
   }}
   ```

3. **Disabled state includes new service:**
   ```typescript
   disabled={
     openPanel === 'email' ? emailData.loading :
     openPanel === 'calendar' ? calendarData.loading :
     openPanel === 'tasks' ? tasksData.loading :
     openPanel === 'notion' ? (isSyncing || notionData.loading) :
     newServiceData.loading
   }
   ```

4. **Loading animation includes new service:**
   ```typescript
   className={
     (openPanel === 'email' && emailData.loading) ||
     (openPanel === 'calendar' && calendarData.loading) ||
     (openPanel === 'tasks' && tasksData.loading) ||
     (openPanel === 'notion' && isSyncing) ||
     (openPanel === 'newservice' && newServiceData.loading)
       ? 'animate-spin'
       : ''
   }
   ```

### Common Mistakes to Avoid

❌ **DON'T create service-specific sync buttons in content areas:**
```typescript
// WRONG - This was removed from Notion panel
<button onClick={handleSyncDatabases}>
  <RefreshCw size={18} className={isSyncing ? 'animate-spin' : ''} />
  {isSyncing ? 'Syncing...' : 'Sync'}
</button>
```

✅ **DO use the unified header sync button:**
```typescript
// CORRECT - One sync button in header for all services
{(openPanel === 'email' || openPanel === 'calendar' || ...) && (
  <button onClick={handleSync}>
    <svg className="animate-spin">...</svg>
  </button>
)}
```

---

## Fullscreen System

### Overview

The fullscreen system allows any service panel to expand to take up 100% of the viewport (minus TopBar), hiding the chat area completely. This provides maximum space for viewing emails, calendars, tasks, etc.

### Architecture

**Files Involved:**
1. `src/app/page.tsx` - Manages fullscreen state and ChatArea visibility
2. `src/components/ServicePanelContainer.tsx` - Handles fullscreen toggle and animation

### State Management

**File:** `src/app/page.tsx`

```typescript
// Line 23: Fullscreen state
const [isPanelFullscreen, setIsPanelFullscreen] = useState(false)

// Lines 26-31: Defensive state synchronization
useEffect(() => {
  if (openPanel === null) {
    setIsPanelFullscreen(false)
  }
}, [openPanel])
```

**Why the defensive useEffect?**
- Ensures `isPanelFullscreen` is always reset when panel closes
- Prevents bug where ChatArea stays hidden after closing fullscreen panel
- Guarantees clean state management

### Props Interface

```typescript
interface ServicePanelContainerProps {
  openPanel: PanelType
  onClose: () => void
  panelHeight: number
  onPanelHeightChange: (height: number) => void
  onResizingChange: (isResizing: boolean) => void
  isFullscreen: boolean                          // NEW: Current fullscreen state
  onFullscreenToggle: () => void                  // NEW: Toggle callback
}
```

### Panel Container Animation

**File:** `ServicePanelContainer.tsx` (Lines 260-316)

```typescript
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{
    height: isFullscreen ? 'calc(100vh - 64px)' : `calc((100vh - 64px) * ${panelHeight})`,
    opacity: 1
  }}
  exit={{ height: 0, opacity: 0 }}
  transition={
    isDragging
      ? { duration: 0 }
      : { type: 'spring', damping: 25, stiffness: 300 }
  }
  className="
    fixed
    top-16
    left-0
    right-0
    z-50
    relative
    w-full
    bg-light-surface dark:bg-dark-surface
    shadow-lg
    flex flex-col
  "
>
```

**Height Calculation:**
- **Fullscreen:** `calc(100vh - 64px)` (100% viewport minus TopBar)
- **Normal:** `calc((100vh - 64px) * ${panelHeight})` (user-adjustable percentage)
- **TopBar Height:** 64px (4rem)

**Animation:**
- **Spring animation** for smooth, natural motion
- **Damping:** 25 (controls bounce)
- **Stiffness:** 300 (controls speed)
- **Disabled during drag:** `duration: 0` for instant resizing

### Chat Area Visibility Control

**File:** `page.tsx` (Lines 77-91)

```typescript
<motion.div
  initial={{ opacity: 1 }}
  animate={{
    opacity: isPanelFullscreen ? 0 : 1,
  }}
  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
  className="w-full bg-light-bg dark:bg-dark-bg"
  style={{
    height: openPanel ? `calc((100vh - 64px) * ${1 - panelHeight})` : 'calc(100vh - 64px)',
    transition: isResizing ? 'none' : 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    display: isPanelFullscreen ? 'none' : 'block'
  }}
>
  <ChatArea />
</motion.div>
```

**Visibility Strategy:**
1. **Opacity fade:** Animates to 0 when fullscreen
2. **Display none:** Completely removes from layout after fade
3. **Height calculation:** Inverse of panel height when not fullscreen
4. **Smooth transition:** Matches panel animation timing

### User Experience Flow

**Entering Fullscreen:**
```
1. User clicks fullscreen button (Maximize2 icon)
   ↓
2. onFullscreenToggle() called → isPanelFullscreen = true
   ↓
3. Panel height animates to calc(100vh - 64px)
   ↓
4. Chat area opacity fades to 0
   ↓
5. Chat area display set to 'none'
   ↓
6. Button icon changes to Minimize2
```

**Exiting Fullscreen:**
```
1. User clicks fullscreen button (Minimize2 icon)
   ↓
2. onFullscreenToggle() called → isPanelFullscreen = false
   ↓
3. Panel height animates to calc((100vh - 64px) * 0.5)  [50% default]
   ↓
4. Chat area display set to 'block'
   ↓
5. Chat area opacity fades to 1
   ↓
6. Button icon changes to Maximize2
```

**Closing Panel (from fullscreen):**
```
1. User clicks close button (X)
   ↓
2. onClose() called → openPanel = null
   ↓
3. Defensive useEffect triggers → isPanelFullscreen = false
   ↓
4. Panel height animates to 0
   ↓
5. Chat area display set to 'block'
   ↓
6. Chat area opacity back to 1
   ↓
7. Panel exits completely
```

### Fullscreen Button Toggle Logic

**File:** `page.tsx` (Line 73)

```typescript
<ServicePanelContainer
  openPanel={openPanel}
  onClose={() => {
    setOpenPanel(null)
    setIsPanelFullscreen(false)  // Also reset fullscreen
  }}
  panelHeight={panelHeight}
  onPanelHeightChange={setPanelHeight}
  onResizingChange={setIsResizing}
  isFullscreen={isPanelFullscreen}
  onFullscreenToggle={() => setIsPanelFullscreen(!isPanelFullscreen)}
/>
```

**Toggle behavior:**
- Simple state flip: `!isPanelFullscreen`
- No side effects, just pure state toggle
- All animation handled automatically by Framer Motion

### Testing Fullscreen

After implementing fullscreen:

- [ ] Fullscreen button appears in header for all services
- [ ] Clicking fullscreen expands panel to full viewport
- [ ] Icon changes from Maximize2 to Minimize2
- [ ] Chat area fades out completely
- [ ] Clicking minimize restores panel to previous height
- [ ] Icon changes from Minimize2 to Maximize2
- [ ] Chat area fades back in
- [ ] Closing panel from fullscreen shows chat area
- [ ] No flash or layout shift during transitions
- [ ] Animations are smooth (spring physics)
- [ ] Resize handle still works in normal mode
- [ ] ESC key closes panel correctly from fullscreen

### Common Fullscreen Issues

**Problem:** Chat area stays hidden after closing panel from fullscreen

**Cause:** `isPanelFullscreen` not reset when `openPanel` becomes null

**Fix:** Defensive useEffect in page.tsx (lines 26-31)
```typescript
useEffect(() => {
  if (openPanel === null) {
    setIsPanelFullscreen(false)
  }
}, [openPanel])
```

**Problem:** Fullscreen animation stutters or lags

**Cause:** CSS transitions conflicting with Framer Motion

**Fix:** Disable transitions during resize (isResizing check)

**Problem:** Panel height wrong after exiting fullscreen

**Cause:** panelHeight state not preserved

**Fix:** Only animate height, don't change panelHeight value during fullscreen

---

## Calendar Header Design

### Overview

The Calendar service has a **unique header design** with custom controls for view selection and date navigation. This is the ONLY service with these special controls.

**File:** `ServicePanelContainer.tsx` (Lines 354-473)

### Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Calendar  [Month ▼]  [◀]  November 2025  [▶]      [🗘] [⛶] [✕]         │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │
│                                                                         │
│  [Calendar Month/Week/Day View]                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Typography Standards

**CRITICAL: These are the EXACT sizes that must be used:**

```typescript
// "Calendar" Label
text-sm              // 14px
font-bold            // 700 weight
font-heading         // Heading font family

// View Dropdown Button Text ("Month", "Week", "Day")
text-xs              // 12px
font-medium          // 500 weight

// Month/Year Display ("November 2025")
text-xs              // 12px
font-medium          // 500 weight

// Navigation Arrow Icons (< >)
12x12 pixels         // width="12" height="12"

// Dropdown Arrow Icon (▼)
12x12 pixels         // width="12" height="12"
```

### Calendar Label

**Purpose:** Shows "Calendar" as the section title

```typescript
{/* Calendar Label */}
<h2 className="text-sm font-heading font-bold text-light-text dark:text-dark-text">
  Calendar
</h2>
```

**Specifications:**
- **Size:** text-sm (14px)
- **Weight:** font-bold (700)
- **Font:** font-heading (Inter or system heading font)
- **Color:** text-light-text dark:text-dark-text

**Position:** Far left of header, before all other controls

### View Dropdown

**Purpose:** Switch between Month, Week, and Day views

```typescript
{/* View Dropdown */}
<div className="relative" onMouseEnter={() => setShowViewDropdown(true)} onMouseLeave={() => setShowViewDropdown(false)}>
  <button className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-light-text dark:text-dark-text hover:bg-accent/10 dark:hover:bg-accent/20 rounded transition-colors">
    <span>{calendarData.activeView.charAt(0).toUpperCase() + calendarData.activeView.slice(1)}</span>
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform ${showViewDropdown ? 'rotate-180' : ''}`}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  </button>

  {/* Dropdown Menu */}
  {showViewDropdown && (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -5 }}
      className="absolute top-[calc(100%-2px)] left-0 bg-light-surface dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden z-[9999] min-w-[100px] pt-2"
    >
      {(['month', 'week', 'day'] as const).map((view) => (
        <button
          key={view}
          onClick={() => calendarData.setActiveView(view)}
          className={`w-full px-4 py-1.5 text-xs text-left transition-colors ${
            calendarData.activeView === view
              ? 'bg-accent text-white'
              : 'text-light-text dark:text-dark-text hover:bg-accent/10 dark:hover:bg-accent/20'
          }`}
        >
          {view.charAt(0).toUpperCase() + view.slice(1)}
        </button>
      ))}
    </motion.div>
  )}
</div>
```

**Button Specifications:**
- **Padding:** px-2.5 py-1 (10px horizontal, 4px vertical)
- **Text:** text-xs font-medium (12px, weight 500)
- **Border Radius:** rounded (4px)
- **Hover:** bg-accent/10 dark:bg-accent/20
- **Gap:** gap-1.5 between text and icon (6px)

**Dropdown Arrow:**
- **Size:** 12x12 pixels
- **Rotation:** 180deg when dropdown open
- **Transition:** transition-transform for smooth rotation

**Dropdown Menu:**
- **Position:** absolute, top-[calc(100%-2px)] (2px overlap with button)
- **Width:** min-w-[100px]
- **Padding:** pt-2 (8px top padding for overlap)
- **Z-index:** z-[9999] (above all content)
- **Animation:** Framer Motion fade + slide (y: -5 to 0)

**Dropdown Items:**
- **Padding:** px-4 py-1.5 (16px horizontal, 6px vertical)
- **Text:** text-xs (12px)
- **Active State:** bg-accent text-white
- **Hover:** bg-accent/10 dark:bg-accent/20

**Behavior:**
- Opens on mouse enter (hover trigger)
- Closes on mouse leave
- Arrow rotates 180° when open
- Smooth animation via Framer Motion
- Active view highlighted with accent background

### Date Navigation

**Purpose:** Navigate forward/backward through months

```typescript
{/* Date Navigation */}
<div className="flex items-center gap-2">
  {/* Previous Month Button */}
  <button
    onClick={() => {
      const newDate = new Date(calendarData.selectedDate);
      newDate.setMonth(newDate.getMonth() - 1);
      calendarData.setSelectedDate(newDate);
    }}
    className="p-1 hover:bg-accent/10 dark:hover:bg-accent/20 rounded transition-colors"
    aria-label="Previous month"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-light-text dark:text-dark-text">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  </button>

  {/* Month/Year Display */}
  <span className="text-xs font-medium text-light-text dark:text-dark-text">
    {calendarData.selectedDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
  </span>

  {/* Next Month Button */}
  <button
    onClick={() => {
      const newDate = new Date(calendarData.selectedDate);
      newDate.setMonth(newDate.getMonth() + 1);
      calendarData.setSelectedDate(newDate);
    }}
    className="p-1 hover:bg-accent/10 dark:hover:bg-accent/20 rounded transition-colors"
    aria-label="Next month"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-light-text dark:text-dark-text">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  </button>
</div>
```

**Navigation Button Specifications:**
- **Padding:** p-1 (4px all around)
- **Icon Size:** 12x12 pixels
- **Border Radius:** rounded (4px)
- **Hover:** bg-accent/10 dark:bg-accent/20
- **Color:** text-light-text dark:text-dark-text

**Month/Year Display:**
- **Text:** text-xs font-medium (12px, weight 500)
- **Color:** text-light-text dark:text-dark-text
- **Format:** "November 2025" (month long, year numeric)

**Container:**
- **Gap:** gap-2 between elements (8px)
- **Display:** flex items-center

**Behavior:**
- Left arrow: Subtract 1 month from selectedDate
- Right arrow: Add 1 month to selectedDate
- Month/Year display updates automatically
- Hover effects on arrow buttons

### Complete Header Structure

```typescript
{openPanel === 'calendar' && (
  <div className="flex items-center gap-3">
    {/* Calendar Label */}
    <h2 className="text-sm font-heading font-bold text-light-text dark:text-dark-text">
      Calendar
    </h2>

    {/* View Dropdown */}
    <div className="relative">
      {/* Dropdown button and menu */}
    </div>

    {/* Date Navigation */}
    <div className="flex items-center gap-2">
      {/* Previous, Display, Next */}
    </div>
  </div>
)}
```

**Gap Specifications:**
- **Outer gap:** gap-3 (12px) between major sections (Label, Dropdown, Navigation)
- **Inner gap:** gap-2 (8px) within navigation (buttons and display)
- **Dropdown gap:** gap-1.5 (6px) between text and arrow

### Why Calendar Has Custom Controls

**Other services:**
- Simple list views (emails, tasks, notion databases)
- Only need: Back button (conditional), Title, Sync, Fullscreen, Close

**Calendar:**
- Multiple view modes (Month, Week, Day)
- Date-based navigation (previous/next month)
- Current date display (November 2025)
- Requires interactive controls beyond simple list navigation

**Design Decision:**
- Keep unified header pattern (Sync, Fullscreen, Close on right)
- Add calendar-specific controls on left (Label, View, Navigation)
- Maintain visual consistency with other services

### Testing Calendar Header

- [ ] "Calendar" label is 14px bold
- [ ] View dropdown button is 12px medium
- [ ] Month/Year display is 12px medium
- [ ] All icons are exactly 12x12 pixels
- [ ] Gap between major sections is 12px (gap-3)
- [ ] Gap within navigation is 8px (gap-2)
- [ ] Dropdown opens on hover
- [ ] Dropdown closes on mouse leave
- [ ] Arrow rotates when dropdown opens
- [ ] Active view highlighted in dropdown
- [ ] Previous/Next buttons change date
- [ ] Month/Year display updates correctly
- [ ] Sync, Fullscreen, Close buttons present
- [ ] All buttons have hover effects
- [ ] Visual hierarchy clear (14px label stands out)

---

## Scrollbar Architecture

### The Critical Rule

**⚠️ ONLY THE PARENT CONTAINER SHOULD HANDLE SCROLLING**

All child components (TasksBoardView, NotionTableView, TaskColumn, etc.) should **NEVER** have overflow properties. This ensures scrollbars appear at the viewport level (always visible) rather than at the content level (requiring scrolling to see them).

### Implementation

**File:** `ServicePanelContainer.tsx`

```typescript
// Line 318: Parent container handles ALL scrolling
// CRITICAL: Use overflow-y-scroll (not overflow-auto) to prevent header icon layout shift
<div className="w-full max-w-7xl mx-auto flex flex-col h-full overflow-y-scroll tasks-board-scroll">
  {/* Header (sticky) */}
  {/* Content (no overflow properties) */}
</div>
```

### CRITICAL: overflow-y-scroll vs overflow-auto

**⚠️ ALWAYS USE `overflow-y-scroll` (not `overflow-auto`)** on the main content container.

**Why?**

- **overflow-auto:** Scrollbar only appears when content overflows
  - Problem: When scrollbar appears/disappears, it takes up space (~8-15px)
  - Result: Header icons shift left/right during view changes or sync operations
  - User Experience: Icons "jump around" which feels janky

- **overflow-y-scroll:** Scrollbar gutter always reserved, even when not needed
  - Benefit: Layout space for scrollbar is always present
  - Result: Header icons stay in exact same position at all times
  - User Experience: Stable, professional, no layout shift

**Example of the Problem:**
```
// ❌ WRONG - Causes header icon shift
<div className="overflow-auto">  // Scrollbar appears/disappears

[Before content loads]
│ Calendar [Month] [◀] Nov 2025 [▶]         [🗘][⛶][✕]│
                                             ↑ Icons here

[After content loads with scrollbar]
│ Calendar [Month] [◀] Nov 2025 [▶]      [🗘][⛶][✕]│▐
                                          ↑ Icons shifted left

// ✅ CORRECT - Icons stay in place
<div className="overflow-y-scroll">  // Scrollbar always reserved

[Before content loads]
│ Calendar [Month] [◀] Nov 2025 [▶]      [🗘][⛶][✕]│▐
                                          ↑ Icons here

[After content loads with scrollbar]
│ Calendar [Month] [◀] Nov 2025 [▶]      [🗘][⛶][✕]│▐
                                          ↑ Icons stay in same place
```

**Fixed in:** v1.2.19 (2025-11-11) - ServicePanelContainer.tsx line 318

### Child Component Rules

**❌ DO NOT ADD overflow properties to child components:**

```typescript
// ❌ WRONG: Don't add overflow to children
<div className="flex-1 overflow-x-auto">  // NO!
<div className="overflow-y-auto">          // NO!
<div className="overflow-auto">            // NO!
```

**✅ CORRECT: Let parent handle scrolling:**

```typescript
// ✅ CORRECT: No overflow properties
<div className="flex-1">                   // YES
<div className="px-4 py-3">                // YES
```

### Files and Their Scroll Configuration

| File | Line | Class | Notes |
|------|------|-------|-------|
| ServicePanelContainer.tsx | 318 | `overflow-y-scroll tasks-board-scroll` | ✅ Parent handles all scrolling (CRITICAL: y-scroll not auto) |
| TasksBoardView.tsx | 288 | `flex-1` | ✅ No overflow properties |
| TaskColumn.tsx | 145 | `flex-1 px-4 py-3` | ✅ No overflow properties |
| NotionTableView.tsx | 728 | No classes | ✅ No overflow properties |

### Custom Scrollbar Styling

The `.tasks-board-scroll` class provides thin, styled scrollbars:

```css
/* src/app/globals.css lines 307-337 */
.tasks-board-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgb(156 163 175) transparent;
}

.tasks-board-scroll::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.tasks-board-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.tasks-board-scroll::-webkit-scrollbar-thumb {
  background-color: rgb(156 163 175);
  border-radius: 4px;
}

.tasks-board-scroll::-webkit-scrollbar-thumb:hover {
  background-color: rgb(107 114 128);
}
```

### Why This Architecture Works

**Problem Before:**
- Child components had `overflow-x-auto` or `overflow-y-auto`
- Scrollbars appeared at bottom of CONTENT (below fold)
- User had to scroll DOWN to see horizontal scrollbar
- Multiple nested scrollbars caused confusion

**Solution Now:**
- Only parent has `overflow-auto`
- Scrollbars appear at bottom of VIEWPORT (always visible)
- No nested scrolling containers
- Consistent, predictable behavior

### Visual Result

```
┌─────────────────────────────────┐
│ ServicePanelContainer           │ ← overflow-auto (handles scrolling)
│ ┌─────────────────────────────┐ │
│ │ Header (sticky)             │ │
│ ├─────────────────────────────┤ │
│ │ TasksBoardView              │ │ ← NO overflow
│ │   ┌─────────────────────┐   │ │
│ │   │ TaskColumn          │   │ │ ← NO overflow
│ │   │ - Task 1            │   │ │
│ │   │ - Task 2            │   │ │
│ │   └─────────────────────┘   │ │
│ └─────────────────────────────┘ │
│ [═══════════════════════]       │ ← Scrollbar ALWAYS visible here
└─────────────────────────────────┘
```

### Common Mistakes to Avoid

```typescript
// ❌ MISTAKE 1: Adding overflow to board container
<div className="flex-1 overflow-x-auto">
  {/* This creates scrollbar at content level */}
</div>

// ❌ MISTAKE 2: Adding overflow to columns
<div className="flex-1 overflow-y-auto">
  {/* This creates nested scrolling */}
</div>

// ❌ MISTAKE 3: Adding max-height constraints
<div className="max-h-[calc(100vh-300px)] overflow-y-auto">
  {/* This forces scrollbar at content level */}
</div>

// ✅ CORRECT: Clean containers without overflow
<div className="flex-1">
  {/* Parent handles scrolling */}
</div>
```

### Debugging Scrollbar Issues

If scrollbars are not appearing correctly or header icons are shifting:

1. **Check parent container** (`ServicePanelContainer.tsx` line 318):
   - MUST have: `overflow-y-scroll tasks-board-scroll` (NOT overflow-auto)
   - MUST NOT have: `overflow-hidden` or `overflow-auto`
   - **Critical:** Using `overflow-auto` causes header icon layout shift

2. **Check child components**:
   - TasksBoardView.tsx line 288: Should be `flex-1` only
   - TaskColumn.tsx line 145: Should be `flex-1 px-4 py-3` only
   - NotionTableView.tsx line 728: Should have NO overflow classes

3. **Check for header icon shift**:
   - Open service panel (calendar, email, etc.)
   - Trigger sync or view change
   - Watch header icons on the right (Sync, Fullscreen, Close)
   - Icons should NOT move left/right when scrollbar appears
   - If icons shift: Parent container is using `overflow-auto` instead of `overflow-y-scroll`

4. **Run build**: `pnpm build` to verify compilation

5. **Clear browser cache**: Hard refresh (Ctrl+Shift+R) to see changes

### Testing Checklist

After making scrollbar changes:

- [ ] Horizontal scrollbar visible at bottom of viewport (not hidden)
- [ ] Vertical scrollbar visible at right of viewport
- [ ] Scrollbar gutter always present (even with no overflow)
- [ ] Header icons (Sync, Fullscreen, Close) do NOT shift when content changes
- [ ] No layout shift when switching calendar views
- [ ] No layout shift when pressing sync button
- [ ] No double scrollbars (nested scrolling)
- [ ] Tasks board scrolls horizontally when columns overflow
- [ ] Notion table scrolls horizontally when columns overflow
- [ ] Task columns do NOT have internal scrollbars
- [ ] Scrollbars use custom thin styling (`.tasks-board-scroll`)
- [ ] Panel resize handle works without affecting scrollbars

---

## User-Adjustable Panel Height

### Overview

Users can dynamically resize the integration panel by dragging a resize handle at the bottom of the panel. This provides flexibility to view more of either the integration panel or the chat area based on their current needs.

### Implementation Details

#### State Management (page.tsx)

```typescript
// State for panel height and resizing status
const [panelHeight, setPanelHeight] = useState(0.5)      // 50% by default
const [isResizing, setIsResizing] = useState(false)       // Track drag state

// Props passed to ServicePanelContainer
<ServicePanelContainer
  openPanel={openPanel}
  onClose={() => setOpenPanel(null)}
  panelHeight={panelHeight}
  onPanelHeightChange={setPanelHeight}
  onResizingChange={setIsResizing}
/>

// Chat area height adjusts dynamically
<div
  className="w-full bg-light-bg dark:bg-dark-bg"
  style={{
    height: openPanel
      ? `calc((100vh - 64px) * ${1 - panelHeight})`
      : 'calc(100vh - 64px)',
    transition: isResizing
      ? 'none'
      : 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  }}
>
  <ChatArea />
</div>
```

#### Resize Handle (ServicePanelContainer.tsx)

```typescript
// State for drag tracking
const [isDragging, setIsDragging] = useState(false)

// Resize handle at bottom of panel
<div
  onMouseDown={() => setIsDragging(true)}
  className={`
    absolute bottom-0 left-0 right-0 h-1.5
    bg-gray-200 dark:bg-gray-700
    hover:bg-accent dark:hover:bg-accent
    cursor-row-resize
    transition-colors
    ${isDragging ? 'bg-accent' : ''}
  `}
  title="Drag to resize panel"
>
  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-1 bg-gray-400 dark:bg-gray-500 rounded-full" />
</div>
```

#### Drag Handler Logic

```typescript
// Handle resize dragging
useEffect(() => {
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return

    const viewportHeight = window.innerHeight - 64 // Subtract TopBar height
    const mouseY = e.clientY - 64                   // Subtract TopBar height
    const newHeight = Math.max(0.2, Math.min(0.8, mouseY / viewportHeight))

    onPanelHeightChange(newHeight)
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    onResizingChange(false)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  if (isDragging) {
    onResizingChange(true)
    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }
}, [isDragging, onPanelHeightChange, onResizingChange])
```

### Performance Optimizations

To ensure smooth, lag-free resizing:

1. **Disable Spring Animation During Drag:**
   ```typescript
   transition={isDragging ? { duration: 0 } : { type: 'spring', damping: 25, stiffness: 300 }}
   ```

2. **Disable CSS Transitions During Drag:**
   ```typescript
   style={{
     transition: isResizing ? 'none' : 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
   }}
   ```

3. **Prevent Text Selection:**
   ```typescript
   document.body.style.userSelect = 'none'
   ```

4. **Update Cursor Globally:**
   ```typescript
   document.body.style.cursor = 'row-resize'
   ```

### Visual Specifications

```typescript
// Resize handle dimensions
height: 'h-1.5'  // 6px tall
width: '100%'    // Full panel width

// Colors
default: 'bg-gray-200 dark:bg-gray-700'
hover: 'bg-accent dark:bg-accent'
dragging: 'bg-accent'

// Cursor
cursor: 'cursor-row-resize'

// Handle indicator (visual grip)
width: 'w-12'    // 48px
height: 'h-1'    // 4px
color: 'bg-gray-400 dark:bg-gray-500'
shape: 'rounded-full'
position: 'centered'
```

### User Experience

- **Hover:** Handle changes color to indicate it's interactive
- **Drag:** Handle turns accent color, cursor changes to row-resize
- **Constraints:** Height is constrained between 20% and 80% of viewport
- **Smooth:** No lag or stuttering during drag operations
- **Persistent:** Height preference persists during the session

### Props Interface

```typescript
interface ServicePanelContainerProps {
  openPanel: PanelType
  onClose: () => void
  panelHeight: number                        // Current height (0.0-1.0)
  onPanelHeightChange: (height: number) => void  // Update height callback
  onResizingChange: (isResizing: boolean) => void // Notify drag state
}
```

---

## Adding a New Service

Follow these steps EXACTLY to add a new service integration:

### Step 1: Update Type Definitions

**File:** `src/components/ServicePanelContainer.tsx`

```typescript
// Add your service to the union type (line 11)
type PanelType = 'email' | 'calendar' | 'notion' | 'yourservice' | null
```

**File:** `src/components/TopBar.tsx`

```typescript
// Add your service to the union type (line 11)
type PanelType = 'email' | 'calendar' | 'notion' | 'yourservice' | null
```

**File:** `src/app/page.tsx`

```typescript
// Add your service to the union type (line 12)
type PanelType = 'email' | 'calendar' | 'notion' | 'yourservice' | null
```

### Step 2: Add Service Icon to TopBar

**File:** `src/components/TopBar.tsx`

```typescript
// After line 190, add your service icon button
<Tooltip>
  <TooltipTrigger asChild>
    <motion.button
      onClick={() => onPanelChange?.(openPanel === 'yourservice' ? null : 'yourservice')}
      className="p-2 rounded-xl text-light-text-secondary dark:text-dark-text-secondary transition-all"
      style={{
        opacity: !yourServiceConnected ? 0.2 : openPanel === 'yourservice' ? 0.8 : 0.5
      }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      aria-label="Your Service"
    >
      <YourServiceIcon size={18} />
    </motion.button>
  </TooltipTrigger>
  <TooltipContent>
    <p>
      {yourServiceConnected
        ? 'Your Service Name'
        : isLoggedIn
        ? 'Please connect to your service account'
        : 'Please login and connect to your service'}
    </p>
  </TooltipContent>
</Tooltip>
```

### Step 3: Add Service State to ServicePanelContainer

**File:** `src/components/ServicePanelContainer.tsx`

Add after line 45:

```typescript
// Your service state
const yourServiceData = useYourServiceData()  // Create this hook
const [yourServiceView, setYourServiceView] = useState<YourServiceView>('list')
const [yourServiceConnected, setYourServiceConnected] = useState(false)
```

### Step 4: Add Connection Status Check

**File:** `src/components/ServicePanelContainer.tsx`

Add inside the `checkStatus` function (after line 83):

```typescript
// Check Your Service connection
const yourServiceResponse = await fetch(`${apiUrl}/api/oauth/yourservice/status`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
if (yourServiceResponse.ok) {
  const data = await yourServiceResponse.json()
  setYourServiceConnected(data.connected)
}
```

### Step 5: Add Data Loading Logic

**File:** `src/components/ServicePanelContainer.tsx`

Add inside the data loading `useEffect` (after line 105):

```typescript
} else if (openPanel === 'yourservice' && yourServiceConnected) {
  yourServiceData.fetchData()
  setYourServiceView('list')
}
```

### Step 6: Add Header Title Logic

**File:** `src/components/ServicePanelContainer.tsx`

Add after line 292:

```typescript
{openPanel === 'yourservice' && (
  <h2 className="text-sm font-heading font-medium text-light-text dark:text-dark-text">
    {yourServiceView === 'list' && 'Your Service Name'}
    {yourServiceView === 'detail' && 'Item Details'}
    {yourServiceView === 'create' && 'Create Item'}
  </h2>
)}
```

### Step 7: Add Back Button Handler

**File:** `src/components/ServicePanelContainer.tsx`

Add the condition to line 265:

```typescript
{((openPanel === 'email' && emailView !== 'list') ||
  (openPanel === 'calendar' && calendarView !== 'list') ||
  (openPanel === 'notion' && notionView !== 'list') ||
  (openPanel === 'yourservice' && yourServiceView !== 'list')) && (
```

And update the onClick (line 270):

```typescript
onClick={
  openPanel === 'email' ? handleEmailBack :
  openPanel === 'calendar' ? handleCalendarBack :
  openPanel === 'notion' ? handleNotionBack :
  handleYourServiceBack
}
```

### Step 8: Add Content Rendering

**File:** `src/components/ServicePanelContainer.tsx`

Add after line 636 (after Notion content):

```typescript
{/* Your Service Content */}
{isConnected && openPanel === 'yourservice' && !yourServiceData.loading && (
  <>
    {yourServiceView === 'list' && (
      <div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {yourServiceData.items.length === 0 ? (
            <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
              No items found
            </div>
          ) : (
            yourServiceData.items.map((item) => (
              <button
                key={item.id}
                onClick={() => handleYourServiceItemClick(item)}
                className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                      {item.title}
                    </p>
                    {item.description && (
                      <p className="text-xs text-light-text/70 dark:text-dark-text/70 mt-1 truncate">
                        {item.description}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    )}
    {/* Add other views (detail, create, etc.) here */}
  </>
)}
```

---

## Color System

### Semantic Colors (USE THESE)

```typescript
// Primary text (titles, labels, main content)
'text-light-text dark:text-dark-text'

// Secondary text (descriptions, metadata) - 70% opacity
'text-light-text/70 dark:text-dark-text/70'

// Muted text (empty states, placeholders) - 60% opacity
'text-light-text/60 dark:text-dark-text/60'

// Faded text (timestamps, subtle info) - 50% opacity
'text-light-text/50 dark:text-dark-text/50'

// Accent color (highlights, active states)
'text-accent' or 'bg-accent'

// Backgrounds
'bg-light-bg dark:bg-dark-bg'           // Main background
'bg-light-surface dark:bg-dark-surface' // Surface/card background

// Borders
'border-gray-200 dark:border-gray-700'  // Standard borders
'border-gray-300 dark:border-gray-600'  // Input borders
```

### Status Badge Colors

```typescript
// Success/Complete
'bg-green-500/10 text-green-600 dark:text-green-400'

// In Progress
'bg-blue-500/10 text-blue-600 dark:text-blue-400'

// Warning/Medium
'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'

// Error/High Priority
'bg-red-500/10 text-red-600 dark:text-red-400'

// Neutral/Default
'bg-gray-500/10 text-gray-600 dark:text-gray-300'
```

### NEVER Use Hardcoded Colors

❌ **DO NOT USE:**
- `text-gray-900`, `text-gray-600`, etc.
- `text-white`, `text-black`
- Any hardcoded color values

✅ **ALWAYS USE:**
- Semantic theme variables listed above
- Opacity modifiers (`/70`, `/60`, `/50`)

---

## Animation Standards

### Container Animation

```typescript
// Panel open/close animation (with dynamic height)
initial={{ height: 0, opacity: 0 }}
animate={{ height: `calc((100vh - 64px) * ${panelHeight})`, opacity: 1 }}
exit={{ height: 0, opacity: 0 }}
transition={isDragging ? { duration: 0 } : { type: 'spring', damping: 25, stiffness: 300 }}
```

**IMPORTANT:** Animation is disabled during drag operations (duration: 0) to ensure instant, lag-free resizing.

### Button Interactions

```typescript
// Icon buttons (TopBar)
whileHover={{ scale: 1.05 }}
whileTap={{ scale: 0.95 }}

// List items
hover: 'hover:bg-light-bg dark:hover:bg-dark-bg'
transition: 'transition-colors'

// Action buttons
hover: 'hover:bg-accent/90'
transition: 'transition-colors'
```

### Content Swapping

**IMPORTANT:** When switching services, content should swap **WITHOUT** animations. The container stays mounted, only the content changes.

```typescript
// ✅ CORRECT: No animation on content swap
{openPanel === 'email' && <EmailContent />}
{openPanel === 'calendar' && <CalendarContent />}
{openPanel === 'notion' && <NotionContent />}

// ❌ WRONG: Don't wrap content in AnimatePresence
<AnimatePresence>
  {openPanel === 'email' && <EmailContent />}
</AnimatePresence>
```

---

## Testing Checklist

After adding a new service, verify:

### Visual Consistency

- [ ] Header height matches other services (py-1.5)
- [ ] Title size is text-sm font-medium
- [ ] Icon sizes are 16px
- [ ] Padding matches (px-6 py-4 for items)
- [ ] Colors use semantic theme variables
- [ ] Empty states are centered with correct color
- [ ] Hover effects work on all interactive elements

### Functionality

- [ ] Service icon appears in TopBar
- [ ] Clicking icon opens panel
- [ ] Clicking icon again closes panel
- [ ] Switching between services is smooth (no flash)
- [ ] Back button appears when not in list view
- [ ] Back button returns to list view
- [ ] Close button (X) closes panel
- [ ] ESC key closes panel
- [ ] Connection status is checked on mount
- [ ] Data loads when service is opened
- [ ] Loading spinner appears during data fetch
- [ ] Error messages display correctly

### Responsive Behavior

- [ ] Panel is full width (no max-width constraint)
- [ ] Panel scrolls when content overflows
- [ ] Header stays sticky at top
- [ ] Works on mobile
- [ ] Works on desktop

### Resize Functionality

- [ ] Resize handle is visible at bottom of panel
- [ ] Resize handle changes color on hover
- [ ] Resize handle turns accent color when dragging
- [ ] Cursor changes to row-resize during drag
- [ ] Panel resizes smoothly without lag
- [ ] Panel height constrained between 20% and 80%
- [ ] Chat area height adjusts inversely
- [ ] Text selection disabled during drag
- [ ] Cursor resets after drag completes
- [ ] Panel height persists during session

---

## Examples

### Example 1: Gmail/Calendar Pattern (Minimal)

For services with simple list views:

```typescript
{openPanel === 'yourservice' && !yourServiceData.loading && (
  <div>
    <div className="divide-y divide-gray-200 dark:divide-gray-700">
      {yourServiceData.items.length === 0 ? (
        <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
          No items found
        </div>
      ) : (
        yourServiceData.items.map((item) => (
          <button
            key={item.id}
            onClick={() => handleItemClick(item)}
            className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                  {item.title}
                </p>
                <p className="text-xs text-light-text/70 dark:text-dark-text/70 mt-1 truncate">
                  {item.description}
                </p>
              </div>
            </div>
          </button>
        ))
      )}
    </div>
  </div>
)}
```

### Example 2: Notion Pattern (With Filters/Categories)

For services with multiple views or categories:

```typescript
{openPanel === 'yourservice' && !yourServiceData.loading && (
  <div>
    {/* Filter/Category Selector */}
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
      <div className="flex gap-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-sans transition-colors ${
              selectedCategory === category
                ? 'bg-accent text-white'
                : 'text-light-text/70 dark:text-dark-text/70 hover:bg-light-surface dark:hover:bg-dark-surface'
            }`}
          >
            <Icon size={14} />
            {category} ({counts[category]})
          </button>
        ))}
      </div>

      {/* Action Button (optional) */}
      {selectedCategory === 'main' && (
        <button
          onClick={handleCreate}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
        >
          <Plus size={18} />
          Create New
        </button>
      )}
    </div>

    {/* Item List */}
    <div className="divide-y divide-gray-200 dark:divide-gray-700">
      {/* Items here */}
    </div>
  </div>
)}
```

### Example 3: Form View Pattern

For create/edit views:

```typescript
{yourServiceView === 'create' && (
  <div className="p-6 space-y-4">
    <div>
      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
        Title *
      </label>
      <input
        type="text"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-sans transition-colors"
        placeholder="Enter title"
      />
    </div>

    <div className="flex items-center gap-2">
      <button
        onClick={handleSubmit}
        disabled={!formData.title}
        className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Create
      </button>
      <button
        onClick={handleBack}
        className="px-4 py-2 rounded-lg hover:bg-accent/10 text-light-text dark:text-dark-text font-sans transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
)}
```

---

## Quick Reference

### Standard Padding

```typescript
Header:       px-6 py-1.5
List items:   px-6 py-4
Forms:        p-6
Empty states: px-6 py-12
Buttons:      px-4 py-2 (secondary), px-6 py-2 (primary)
```

### Standard Text Sizes

```typescript
Titles:       text-sm font-medium
Body:         text-xs
Micro:        text-xs (for timestamps, subtle info)
```

### Standard Icon Sizes

```typescript
Header icons: 16px
Content icons: 14px (filters/categories)
Action buttons: 18px (create, add)
```

### Standard Spacing

```typescript
Gap between elements:    gap-2 (8px), gap-3 (12px)
Vertical spacing:        space-y-4 (16px) for forms
Margin top for metadata: mt-1 (4px), mt-2 (8px)
```

---

## Migration Notes

### Deprecating Old Components

When you've confirmed the new unified container works:

1. **DO NOT DELETE** old files immediately
2. Comment them as `@deprecated` and add removal date
3. Update imports to point to `ServicePanelContainer`
4. After 1 week in production, delete old files

```typescript
/**
 * @deprecated Use ServicePanelContainer instead
 * @removal-date 2025-11-10
 */
```

---

## Support

**Questions?** Check these resources:
- Gmail/Calendar: Reference implementation in `ServicePanelContainer.tsx` lines 400-500
- Notion: Reference implementation in `ServicePanelContainer.tsx` lines 501-636
- Colors: See `src/app/globals.css` for theme variable definitions
- Icons: Using `lucide-react` - search at https://lucide.dev

**Problems?**
1. Check browser console for errors
2. Verify connection status is being checked correctly
3. Ensure data hooks return expected structure
4. Test in both light and dark mode

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0 | 2025-11-11 | **MAJOR UPDATE:** Added unified header control system (Sync/Fullscreen/Close buttons for all panels), complete fullscreen system with ChatArea management, calendar-specific header design documentation, critical scrollbar fix (overflow-y-scroll vs overflow-auto) to prevent header icon layout shift, comprehensive typography standards (14px bold "Calendar", 12px controls), defensive state synchronization, expanded testing checklists |
| 1.2.0 | 2025-11-10 | Added comprehensive scrollbar architecture documentation - parent-only overflow pattern, viewport-level scrollbars, debugging guide |
| 1.1.0 | 2025-11-08 | Added user-adjustable panel height with drag-to-resize functionality, performance optimizations, full-width layout |
| 1.0.0 | 2025-11-03 | Initial pattern documented (Gmail, Calendar, Notion) |

---

**Document Status:** ✅ Complete and Production-Ready
**Maintained By:** Development Team
**Last Reviewed:** 2025-11-11

---

**Remember:** Consistency is key! Follow this pattern EXACTLY for all future integrations to maintain the polished, professional feel across all services.
