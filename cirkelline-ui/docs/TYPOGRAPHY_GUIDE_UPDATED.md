# Cirkelline Typography Guide - UPDATED

Complete typography reference for all text elements in the Cirkelline application with recent changes.

## Recent Changes

- **Chat Input:** Changed from Ubuntu to Alan Sans
- **Section Headers:** Changed from Ubuntu to Alan Sans
- **Links:** Changed from Ubuntu to Ubuntu Mono
- **Tooltips:** Changed from Ubuntu to Ubuntu Mono  
- **Tags/Badges:** Changed from Ubuntu to Ubuntu Mono
- **User Messages:** Changed from Ubuntu 16px to Alan Sans 14px
- **AI Messages:** Changed from Ubuntu to Alan Sans

## Font Families

### Primary Fonts
```css
Body/Default: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif
Headings:     'Alan Sans', 'Ubuntu', system-ui, sans-serif
Code/Mono:    'Ubuntu Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace
```

---

## Form Elements

### Chat Input
- **Font Family:** Alan Sans
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 400
- **Class:** `text-base font-heading`

---

## Sidebar & Navigation

### Section Headers (Sessions, Projects, etc.)
- **Font Family:** Alan Sans
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 700 (bold)
- **Class:** `text-sm font-bold font-heading`

---

## Interactive Elements

### Links
- **Font Family:** Ubuntu Mono
- **Size:** 14px (text-sm)
- **Font Weight:** 500
- **Color:** #DD4814 (accent)
- **Decoration:** Underline on hover
- **Class:** `text-sm font-mono text-accent hover:underline`

### Markdown Links
- **Font Family:** Ubuntu Mono
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Text Decoration:** underline
- **Class:** `text-xs underline font-mono`

---

## Specialized Elements

### Tooltips
- **Font Family:** Ubuntu Mono
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 500 (medium)
- **Class:** `text-xs font-mono font-medium`

### Tags / Badges
- **Font Family:** Ubuntu Mono
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500 (medium)
- **Class:** `text-sm font-mono font-medium`

---

## Chat Interface

### User Messages
- **Font Family:** Alan Sans
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Color:** white (on accent background)
- **Class:** `text-sm font-heading`

### AI Messages / Assistant
- **Font Family:** Alan Sans
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Line Height:** 1.6
- **Class:** `text-sm font-heading` (rendered through markdown)

---

## Code Examples

### Chat Input
```tsx
<textarea className="text-base font-heading">
  Type your message...
</textarea>
```

### Section Header
```tsx
<h2 className="font-heading text-sm font-bold text-light-text dark:text-dark-text">
  Sessions
</h2>
```

### Link Button
```tsx
<button className="text-sm font-mono text-accent hover:underline">
  Click me
</button>
```

### Tooltip
```tsx
<div className="text-xs font-mono font-medium">
  Tooltip content
</div>
```

### Tag/Badge
```tsx
<span className="text-sm font-mono font-medium">
  Tag content
</span>
```

### User Message
```tsx
<div className="text-sm font-heading text-white">
  User message content
</div>
```

### AI Message (Markdown Paragraph)
```tsx
// Uses Paragraph constants with font-heading
<p className="font-heading text-sm">
  AI response rendered through markdown
</p>
```

---

## Summary of Changes

1. **Chat Input**: Ubuntu → Alan Sans (`font-heading`)
2. **Section Headers**: Ubuntu → Alan Sans (`font-heading`)
3. **Links**: Ubuntu → Ubuntu Mono (`font-mono`)
4. **Tooltips**: Ubuntu → Ubuntu Mono (`font-mono`)
5. **Tags/Badges**: Ubuntu → Ubuntu Mono (`font-mono`)
6. **User Messages**: Ubuntu 16px → Alan Sans 14px (`text-sm font-heading`)
7. **AI Messages**: Ubuntu → Alan Sans (`font-heading` via Paragraph constants)

All accent/primary colors are now **#DD4814** (orange) throughout the application.