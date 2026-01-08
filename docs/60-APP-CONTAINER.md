# App Container Architecture

**Version:** v1.3.7
**Last Updated:** 2025-12-19

---

## Overview

The App Container is a flexible panel system that displays apps (Calendar, Email, Tasks, Notion) alongside the chat interface. It supports two layout modes and adapts to mobile/desktop.

**Key Files:**
| File | Purpose |
|------|---------|
| `cirkelline-ui/src/app/page.tsx` | State management, layout structure |
| `cirkelline-ui/src/components/ServicePanelContainer.tsx` | Panel component with header |
| `cirkelline-ui/src/components/TopBar.tsx` | Mobile controls integration |
| `cirkelline-ui/src/app/globals.css` | CSS variables for colors |

---

## Layout Modes

### STACKED (Default)

App panel above chat. Used on all screen sizes.

```
┌─────────────────────────────────────┐
│ TOPBAR (64px fixed)                 │
├─────────────────────────────────────┤
│                                     │
│ APP PANEL                           │  ← Height: panelHeight × remaining
│ (ServicePanelContainer)             │     (default 50%, range 20-80%)
│                                     │
├─────────────────────────────────────┤  ← RESIZE HANDLE (8px, draggable)
│                                     │
│ CHAT AREA                           │  ← Height: (1 - panelHeight) × remaining
│                                     │
└─────────────────────────────────────┘
```

**Height Calculation:**
- Viewport = 100vh
- TopBar = 64px
- Remaining = 100vh - 64px
- Panel height = remaining × panelHeight (default 0.5)
- Chat height = remaining × (1 - panelHeight)

### SIDE-BY-SIDE (Desktop Only)

App panel beside chat. Only available on screens ≥768px.

```
┌─────────────────────────────────────────────────────────┐
│ TOPBAR (64px fixed)                                     │
├───────────────────────┬─┬───────────────────────────────┤
│                       │R│                               │
│ CHAT AREA             │E│ APP PANEL                     │
│ (60% width default)   │S│ (40% width default)           │
│                       │I│                               │
│                       │Z│                               │
│                       │E│                               │
└───────────────────────┴─┴───────────────────────────────┘
                        ↑
                  Vertical resize bar (4px wide)
```

**Width Calculation:**
- Chat width = (1 - panelWidth) × 100% (default 60%)
- Panel width = panelWidth × 100% (default 40%)
- Constraints: panelWidth 0.25 to 0.75

---

## State Management

All layout state lives in `page.tsx` and flows down to components:

```typescript
// page.tsx state
const [openPanel, setOpenPanel] = useState<PanelType>(null)
const [panelHeight, setPanelHeight] = useState(0.5)        // 0.2 to 0.8
const [panelWidth, setPanelWidth] = useState(0.4)          // 0.25 to 0.75
const [isResizing, setIsResizing] = useState(false)
const [isPanelFullscreen, setIsPanelFullscreen] = useState(false)
const [layoutMode, setLayoutMode] = useState<LayoutMode>('stacked')

type PanelType = 'email' | 'calendar' | 'tasks' | 'docs' | 'drive' | 'notion' | 'slack' | 'git' | null
type LayoutMode = 'stacked' | 'side-by-side'
```

**Persistence (localStorage):**
- `cirkelline-layout-mode` → Remembers stacked vs side-by-side
- `cirkelline-google-calendar-sync` → Remembers sync preference

---

## Mobile Behavior

**Mobile ALWAYS uses stacked layout** - side-by-side is disabled via forced `layoutMode="stacked"`.

When an app is open on mobile:
1. **Panel header is HIDDEN** (`hidden md:block`)
2. **TopBar shows app controls** instead of user dropdown
3. **Panel switcher appears** (e.g., calendar grid vs events list)

```
MOBILE TOPBAR (when calendar open):
┌─────────────────────────────────────────────────────────┐
│ [Grid|List] [Month▼] [◀ Dec ▶]         [Settings▼] [✕] │
│ panel       view     date nav          dropdown   close │
│ switcher    dropdown                                    │
└─────────────────────────────────────────────────────────┘
```

**Why mobile is different:**
- Narrow screens need vertical space
- Controls in TopBar saves panel header space
- Panel switcher lets users toggle between views

---

## ServicePanelContainer Component

Located at: `cirkelline-ui/src/components/ServicePanelContainer.tsx`

### Props Interface

```typescript
interface ServicePanelContainerProps {
  openPanel: PanelType
  onClose: () => void
  panelHeight: number                      // For stacked layout
  onPanelHeightChange: (h: number) => void
  onResizingChange: (r: boolean) => void
  isFullscreen: boolean
  onFullscreenToggle: () => void
  layoutMode: 'stacked' | 'side-by-side'
  onLayoutChange: (mode: LayoutMode) => void
  panelWidth?: number                      // For side-by-side layout
  onPanelWidthChange?: (w: number) => void
  externalCalendarState?: CalendarState    // Shared calendar state
  mobilePanel?: 'calendar' | 'events'      // Mobile view switcher
  googleSyncEnabled?: boolean
  onGoogleSyncToggle?: (enabled: boolean) => void
}
```

### Animation (Framer Motion)

```typescript
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{
    height: layoutMode === 'side-by-side' ? '100%' : targetHeight,
    opacity: 1
  }}
  exit={{ height: 0, opacity: 0 }}
  transition={{
    height: { duration: 0.6, type: 'tween', ease: [0.4, 0, 0.2, 1] },
    opacity: { duration: 0.3 }
  }}
>
```

**During resize:** `transition: { duration: 0 }` to disable animation while dragging.

---

## Header Patterns

### CALENDAR HEADER (Single Row)

Used for calendar app. Clean, compact design.

```
┌──────────────┬─────────────────┬────────────────────────┐
│ [Month ▼]    │ [◀ Dec 2025 ▶]  │ [⚙️][↻][▤][⛶][✕]    │
│ view         │ date navigation │ settings, refresh,     │
│ dropdown     │                 │ layout, fullscreen,    │
│              │                 │ close                  │
└──────────────┴─────────────────┴────────────────────────┘
```

**CSS Pattern:**
```tsx
<div className="hidden md:block sticky top-0 z-10 bg-light-surface dark:bg-dark-surface border-b border-border-primary px-4 py-2">
  <div className="flex items-center justify-between gap-2">
    {/* Left: View dropdown */}
    {/* Center: Date navigation */}
    {/* Right: Action buttons */}
  </div>
</div>
```

### EMAIL HEADER (Two Rows)

Used for Email app. More space for folder tabs.

```
ROW 1: [Title]                    [+ Compose][↻][▤][⛶][✕]
ROW 2: [Inbox] [Sent] [Drafts] [Trash]
```

**CSS Pattern:**
```tsx
<div className="space-y-2 sticky top-0 z-10 bg-light-surface dark:bg-dark-surface border-b border-border-primary px-4 py-2">
  {/* Row 1: Title + actions */}
  <div className="flex items-center justify-between">
    <h2 className="text-sm font-heading font-bold">Title</h2>
    <div className="flex items-center gap-2">{/* buttons */}</div>
  </div>
  {/* Row 2: Tabs */}
  <div className="flex items-center gap-1">
    {tabs.map(tab => <button>...</button>)}
  </div>
</div>
```

### TASKS HEADER (v1.3.7)

Used for Tasks app. Single row with settings dropdown.

**Stacked Mode:**
```
┌────────────────────────────────────────────────────────────┐
│ Tasks                            [⚙️ Settings▼][▤][⛶][✕] │
│                                  (dropdown: show/hide      │
│                                   completed, Google sync)  │
└────────────────────────────────────────────────────────────┘
```

**Side-by-Side Mode:**
```
┌────────────────────────────────────────────────────────────┐
│ Tasks    [List Selector▼]        [⚙️ Settings▼][▤][⛶][✕] │
│          (dropdown to switch                               │
│           between lists)                                   │
└────────────────────────────────────────────────────────────┘
```

**Settings Dropdown Structure:**
```tsx
<div className="settings-dropdown">
  {/* View Options Section */}
  <div className="section-label">View Options</div>
  <button>Show completed tasks</button>

  {/* Google Sync Section (if connected) */}
  <div className="section-label">Sync</div>
  <button>Sync with Google Tasks</button>
</div>
```

**Key Features:**
- List selector appears in header for side-by-side mode
- Settings dropdown with section labels
- Consistent button styling with other apps

---

## Resize Handles

### Stacked Layout (Vertical Resize)

- **Location:** Bottom of ServicePanelContainer
- **Size:** `h-2` (8px tall)
- **Cursor:** `cursor-row-resize`
- **Constraints:** panelHeight 0.2 to 0.8

```tsx
<div
  className="flex-shrink-0 w-full h-2 border-t border-border-primary hover:border-accent transition-colors cursor-row-resize"
  onMouseDown={() => setIsDragging(true)}
/>
```

**Resize Logic (page.tsx):**
```javascript
const handleMouseMove = (e: MouseEvent) => {
  const viewportHeight = window.innerHeight - 64  // minus TopBar
  const mouseY = e.clientY - 64
  const newHeight = Math.max(0.2, Math.min(0.8, mouseY / viewportHeight))
  setPanelHeight(newHeight)
}
```

### Side-by-Side Layout (Horizontal Resize)

- **Location:** Between chat and panel
- **Size:** `w-1` (4px), hover `w-1.5` (6px)
- **Cursor:** `cursor-col-resize`
- **Constraints:** panelWidth 0.25 to 0.75

```tsx
<div
  className="hidden md:block w-1 hover:w-1.5 bg-border-primary hover:bg-accent cursor-col-resize transition-all flex-shrink-0"
  onMouseDown={(e) => {
    e.preventDefault()
    setIsResizing(true)
    // ... mouse move/up handlers
  }}
/>
```

**Resize Logic:**
```javascript
const handleMouseMove = (e: MouseEvent) => {
  const container = document.querySelector('.side-by-side-container')
  const rect = container.getBoundingClientRect()
  const newPanelWidth = 1 - ((e.clientX - rect.left) / rect.width)
  setPanelWidth(Math.max(0.25, Math.min(0.75, newPanelWidth)))
}
```

### During Resize

While dragging:
```javascript
isResizing = true
document.body.style.cursor = 'row-resize'  // or 'col-resize'
document.body.style.userSelect = 'none'    // Prevent text selection

// CSS transitions disabled:
style={{ transition: isResizing ? 'none' : 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}
```

---

## Fullscreen Mode

When `isPanelFullscreen = true`:
- Panel takes 100% of viewport (below TopBar)
- Chat area: `opacity: 0` and `display: none`
- Toggle via maximize/minimize button in header

```typescript
<motion.div
  animate={{ opacity: isPanelFullscreen ? 0 : 1 }}
  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
  style={{ display: isPanelFullscreen ? 'none' : 'flex' }}
>
  <ChatArea />
</motion.div>
```

---

## Z-Index Hierarchy

```
9999  Dropdown menus (settings, view selector, date picker)
 100  Calendar settings dropdown (desktop)
  50  ServicePanelContainer
  30  TopBar (fixed, always visible)
   0  Chat area (implicit)
```

---

## CSS Patterns

### Backgrounds
```css
/* Panel backgrounds */
bg-light-surface dark:bg-dark-surface

/* Page background */
bg-light-bg dark:bg-dark-bg

/* Semi-transparent (TopBar) */
bg-light-surface/80 dark:bg-dark-surface/80 backdrop-blur-md
```

### Borders
```css
/* Standard button/input borders */
border border-border-primary rounded-lg

/* Dividers */
border-b border-border-primary

/* Focus state */
hover:border-accent
```

### Buttons
```css
/* Standard action button */
p-1.5 rounded-lg hover:bg-accent/10 transition-colors

/* Active tab */
bg-accent text-white

/* Inactive tab */
text-light-text-secondary/60 dark:text-dark-text-secondary/60 hover:bg-accent/10

/* Close button */
hover:text-red-500 hover:bg-red-500/10

/* Primary action (Compose, Create) */
flex items-center gap-1.5 px-2.5 py-1 text-xs bg-accent text-white rounded
```

### Transitions
```css
/* Height/width changes */
transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1)

/* Disabled during resize */
transition: isResizing ? 'none' : '...'

/* Spring animation (fullscreen toggle) */
type: 'spring', damping: 25, stiffness: 300
```

### Responsive Breakpoints
```css
md:           /* 768px - Desktop breakpoint */
hidden md:block    /* Hidden on mobile */
hidden md:flex     /* Hidden on mobile */
block md:hidden    /* Show only on mobile */
```

---

## Building a New App

Follow these steps to add a new app to the container:

### Step 1: Add Panel Type

```typescript
// page.tsx
type PanelType = 'email' | 'calendar' | 'tasks' | 'your-app' | null
```

### Step 2: Create Panel Component

```typescript
// components/YourAppPanel.tsx
interface YourAppPanelProps {
  layoutMode: 'stacked' | 'side-by-side'
  isFullscreen: boolean
}

export default function YourAppPanel({ layoutMode, isFullscreen }: YourAppPanelProps) {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Your app content */}
    </div>
  )
}
```

### Step 3: Add Header in ServicePanelContainer

```typescript
// ServicePanelContainer.tsx - in the header section
{openPanel === 'your-app' && (
  <div className="hidden md:block space-y-2 sticky top-0 z-10 bg-light-surface dark:bg-dark-surface border-b border-border-primary px-4 py-2">
    {/* Row 1: Title + actions */}
    <div className="flex items-center justify-between">
      <h2 className="text-sm font-heading font-bold text-light-text dark:text-dark-text">
        Your App
      </h2>
      <div className="flex items-center gap-2">
        {/* Refresh button */}
        <button className="p-1.5 rounded-lg hover:bg-accent/10 transition-colors">
          <RefreshCw size={16} />
        </button>
        {/* Layout toggle (desktop only) */}
        <button
          className="hidden md:block p-1.5 rounded-lg hover:bg-accent/10 transition-colors"
          onClick={() => onLayoutChange(layoutMode === 'stacked' ? 'side-by-side' : 'stacked')}
        >
          {layoutMode === 'stacked' ? <Columns2 size={16} /> : <LayoutPanelTop size={16} />}
        </button>
        {/* Fullscreen toggle */}
        <button
          className="p-1.5 rounded-lg hover:bg-accent/10 transition-colors"
          onClick={onFullscreenToggle}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
        {/* Close button */}
        <button
          className="p-1.5 rounded-lg hover:text-red-500 hover:bg-red-500/10 transition-colors"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </div>
    </div>
    {/* Row 2: Tabs (optional) */}
    <div className="flex items-center gap-1">
      {['Tab 1', 'Tab 2', 'Tab 3'].map(tab => (
        <button
          key={tab}
          className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
            activeTab === tab
              ? 'bg-accent text-white'
              : 'text-light-text-secondary/60 hover:bg-accent/10'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  </div>
)}
```

### Step 4: Add Content Renderer

```typescript
// ServicePanelContainer.tsx - in the content area
{openPanel === 'your-app' && (
  <YourAppPanel
    layoutMode={layoutMode}
    isFullscreen={isFullscreen}
  />
)}
```

### Step 5: Add Sidebar Icon

```typescript
// Sidebar.tsx
<button
  onClick={() => setOpenPanel('your-app')}
  className={`p-2 rounded-lg transition-colors ${
    openPanel === 'your-app'
      ? 'bg-accent text-white'
      : 'hover:bg-accent/10'
  }`}
>
  <YourAppIcon size={20} />
</button>
```

### Step 6: Add Mobile TopBar Controls (Optional)

If your app needs mobile controls in TopBar:

```typescript
// TopBar.tsx
interface YourAppControls {
  // Define your controls
  onRefresh: () => void
  onClose: () => void
}

// In TopBar component
{showYourAppControls && (
  <div className="flex md:hidden items-center gap-2">
    {/* Your mobile controls */}
  </div>
)}
```

---

## State Flow Diagram

```
USER ACTION                    STATE CHANGE                 UI UPDATE
─────────────────────────────────────────────────────────────────────
Click app icon           →     openPanel = 'app'       →   Panel opens
Drag resize handle       →     panelHeight changes     →   Heights recalculate
Click layout toggle      →     layoutMode changes      →   Stacked ↔ Side-by-side
Click fullscreen         →     isPanelFullscreen=true  →   Chat hides
Click close (✕)          →     openPanel = null        →   Panel closes
Toggle Google Sync       →     googleSyncEnabled       →   Syncs with Google
```

---

## Common Patterns

### Settings Dropdown

```typescript
const [showSettings, setShowSettings] = useState(false)

<div className="relative">
  <button onClick={() => setShowSettings(!showSettings)}>
    <Settings size={16} />
  </button>

  {showSettings && (
    <div className="absolute top-full right-0 mt-1 z-[9999] bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-xl min-w-[160px]">
      <div className="py-1">
        {/* Toggle item */}
        <button className="w-full flex items-center justify-between px-3 py-2 text-xs">
          <span>Setting Name</span>
          <div className={`w-7 h-3.5 rounded-full transition-colors ${
            enabled ? 'bg-accent' : 'bg-gray-300'
          }`}>
            <div className={`w-3 h-3 rounded-full bg-white shadow transform transition-transform ${
              enabled ? 'translate-x-3.5' : 'translate-x-0.5'
            }`} />
          </div>
        </button>
      </div>
    </div>
  )}
</div>
```

### Tab Component

```typescript
<div className="flex items-center gap-1">
  {tabs.map(tab => (
    <button
      key={tab.id}
      onClick={() => setActiveTab(tab.id)}
      className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
        activeTab === tab.id
          ? 'bg-accent text-white'
          : 'text-light-text-secondary/60 dark:text-dark-text-secondary/60 hover:bg-accent/10'
      }`}
    >
      {tab.label}
    </button>
  ))}
</div>
```

### Panel Switcher (Mobile)

```typescript
<div className="flex items-center border border-border-primary rounded-lg overflow-hidden">
  <button
    onClick={() => setMobilePanel('view1')}
    className={`px-2.5 py-1 text-xs font-medium transition-colors ${
      mobilePanel === 'view1' ? 'bg-accent text-white' : 'bg-light-surface'
    }`}
  >
    <Grid size={14} />
  </button>
  <button
    onClick={() => setMobilePanel('view2')}
    className={`px-2.5 py-1 text-xs font-medium transition-colors ${
      mobilePanel === 'view2' ? 'bg-accent text-white' : 'bg-light-surface'
    }`}
  >
    <List size={14} />
  </button>
</div>
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Panel not opening | Check `openPanel` state is being set |
| Mobile controls not showing | Ensure `showXxxControls` prop is passed to TopBar |
| Dropdown behind panel | Increase z-index to `z-[9999]` |
| Resize laggy | Disable transitions with `isResizing ? 'none' : '...'` |
| Layout toggle not working | Check `onLayoutChange` callback is connected |
| Fullscreen broken | Ensure `isPanelFullscreen` controls both opacity AND display |
