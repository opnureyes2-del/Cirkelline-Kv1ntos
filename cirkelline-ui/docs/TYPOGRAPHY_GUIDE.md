# Cirkelline Typography Guide

Complete typography reference for all text elements in the Cirkelline application.

## Font Families

### Primary Fonts
```css
Body/Default: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif
Headings:     'Alan Sans', 'Ubuntu', system-ui, sans-serif
Code/Mono:    'Ubuntu Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace
```

### Font Loading
Fonts are loaded via Google Fonts CDN:
- Ubuntu: weights 300, 400, 500, 700
- Ubuntu Mono: weights 400, 700
- Alan Sans: weights 300, 400, 500, 600, 700, 800

---

## Typography Scale

### Body Text

#### Default Body
- **Font Family:** Ubuntu
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 400 (normal)
- **Line Height:** 1.5 (default)
- **Usage:** Default text content, paragraphs, descriptions
- **Class:** No explicit class needed (default)

#### Small Body
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Usage:** Secondary text, helper text, labels
- **Examples:** Form labels, session titles, menu items, button text

#### Extra Small Body
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Usage:** Metadata, timestamps, character counts, tags, tooltips
- **Examples:** "200/200 characters", connection labels, step indicators

---

## Headings

All headings use **Alan Sans** font family with **font-weight: 600** (semibold) by default.

### Heading 1 (H1)
- **Font Family:** Alan Sans
- **Font Size:** 36px (2.25rem) - `text-4xl`
- **Font Weight:** 400-600
- **Line Height:** 1.2
- **Usage:** Main page titles, welcome messages
- **Examples:** "Cirkelline" (top bar), "Welcome to Cirkelline" (blank state)
- **Class:** `text-4xl font-heading`

### Heading 2 (H2)
- **Font Family:** Alan Sans
- **Font Size:** 30px (1.875rem) - `text-3xl`
- **Font Weight:** 500-600
- **Usage:** Major section titles, page headers
- **Examples:** Login/signup page titles "Sign In", "Create Account"
- **Class:** `text-3xl font-heading font-medium`

### Heading 3 (H3)
- **Font Family:** Alan Sans
- **Font Size:** 24px (1.5rem) - `text-2xl`
- **Font Weight:** 600
- **Usage:** Section headers, dialog titles
- **Class:** `text-2xl font-heading font-semibold`

### Heading 4 (H4)
- **Font Family:** Alan Sans
- **Font Size:** 20px (1.25rem) - `text-xl`
- **Font Weight:** 600
- **Usage:** Modal titles, sidebar section titles
- **Examples:** "Profile Settings", "Log in to Cirkelline", "Create an account"
- **Class:** `text-xl font-heading font-semibold`

### Heading 5 (H5)
- **Font Family:** Alan Sans
- **Font Size:** 18px (1.125rem) - `text-lg`
- **Font Weight:** 600
- **Usage:** Subsection titles, card headers
- **Examples:** "Workspace" (right sidebar), "Memory Details"
- **Class:** `text-lg font-heading`

### Heading 6 (H6)
- **Font Family:** Alan Sans
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 600
- **Usage:** Minor section headers
- **Class:** `text-base font-heading`

---

## Interactive Elements

### Buttons

#### Default Button
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500 (medium)
- **Usage:** Primary, secondary, outline buttons
- **Height:** 40px (h-10)
- **Class:** `text-sm font-medium`

#### Small Button
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 500
- **Height:** 32px (h-8)
- **Class:** `text-xs font-medium`

#### Large Button
- **Font Family:** Ubuntu
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 500
- **Height:** 48px (h-12)
- **Class:** `text-base font-medium`

#### Extra Large Button
- **Font Family:** Ubuntu
- **Font Size:** 18px (1.125rem) - `text-lg`
- **Font Weight:** 500
- **Height:** 56px (h-14)
- **Class:** `text-lg font-medium`

### Links
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500
- **Text Decoration:** underline on hover
- **Color:** var(--accent) / #DD4814
- **Class:** `text-sm text-accent hover:underline`

---

## Form Elements

### Input Fields
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Placeholder:** Same size, 60% opacity
- **Class:** `text-sm`

### Text Area
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Line Height:** 1.5
- **Class:** `text-sm`

### Chat Input
- **Font Family:** Ubuntu
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 400
- **Line Height:** 1.5
- **Class:** `text-base font-sans`

### Labels
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500 (medium)
- **Class:** `text-sm font-medium`

### Form Helper Text / Validation
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Class:** `text-xs`

---

## Sidebar & Navigation

### Sidebar Title (Cirkelline)
- **Font Family:** Alan Sans
- **Font Size:** 20px (1.25rem) - `text-xl`
- **Font Weight:** 600
- **Letter Spacing:** 0
- **Class:** `text-xl font-heading`

### Section Headers (Sessions, Projects, etc.)
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 700 (bold)
- **Class:** `text-sm font-bold font-sans`

### Session Item Title
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500 (medium)
- **Font Weight (Selected):** 600 (semibold)
- **Class:** `text-sm font-medium` / `text-sm font-semibold`

### Connection Label
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Text Transform:** none
- **Class:** `text-xs`

### Mode/Entity Selector
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 500 (medium)
- **Text Transform:** uppercase
- **Class:** `text-xs font-medium uppercase`

---

## Chat Interface

### User Message
- **Font Family:** Ubuntu
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 400
- **Color:** white (on accent background)
- **Class:** `text-base font-sans`

### AI Message / Assistant
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm` (in markdown)
- **Font Weight:** 400
- **Line Height:** 1.6
- **Class:** Rendered through markdown with prose classes

### Typing Indicator Text
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Class:** `text-sm`

### Tool Name Badge
- **Font Family:** Ubuntu Mono
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Text Transform:** uppercase
- **Class:** `text-xs font-dmmono uppercase`

### File Preview Name
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Class:** `text-xs`

---

## Modals & Dialogs

### Modal Title
- **Font Family:** Alan Sans
- **Font Size:** 20px (1.25rem) - `text-xl`
- **Font Weight:** 600 (semibold)
- **Class:** `text-xl font-heading font-semibold`

### Modal Description
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Class:** `text-sm font-sans`

### Dialog Content
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Class:** `text-sm font-sans`

---

## Specialized Text

### Code Blocks / Inline Code
- **Font Family:** Ubuntu Mono
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Background:** Light gray / Dark surface
- **Class:** `text-sm font-mono`

### Tooltips
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 500 (medium)
- **Class:** `text-xs font-medium`

### Memory Content
- **Font Family:** Ubuntu
- **Font Size:** 16px (1rem) - `text-base`
- **Font Weight:** 400
- **Line Height:** 1.6 (relaxed)
- **Class:** `text-base leading-relaxed`

### Memory Metadata
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Class:** `text-sm`

### Tags / Badges
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 500 (medium)
- **Class:** `text-sm font-medium`

### Error Messages
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Color:** var(--error) / #EF4444
- **Class:** `text-sm text-error`

### Success Messages
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Color:** var(--success) / #10B981
- **Class:** `text-sm text-success`

---

## Markdown Rendered Content

### Markdown Headings
- **H1:** 20px (text-xl) - Alan Sans, semibold
- **H2:** 18px (text-lg) - Alan Sans, medium
- **H3:** 16px (text-base) - Alan Sans, medium
- **H4-H6:** Progressively smaller

### Markdown Paragraph
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 400
- **Line Height:** 1.6

### Markdown Links
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Text Decoration:** underline
- **Class:** `text-xs underline`

### Markdown Table Headers
- **Font Family:** Ubuntu
- **Font Size:** 14px (0.875rem) - `text-sm`
- **Font Weight:** 600
- **Class:** `text-sm font-semibold`

### Markdown Table Body
- **Font Family:** Ubuntu
- **Font Size:** 12px (0.75rem) - `text-xs`
- **Font Weight:** 400
- **Class:** `text-xs`

### Markdown Strong/Bold
- **Font Weight:** 600 (semibold)
- **Class:** `font-semibold`

### Markdown Emphasis/Italic
- **Font Style:** italic
- **Font Weight:** 600 (semibold)
- **Class:** `font-semibold italic`

---

## Font Weights Reference

- **300:** Light
- **400:** Normal/Regular (default)
- **500:** Medium
- **600:** Semibold
- **700:** Bold
- **800:** Extra Bold (Alan Sans only)

---

## Text Colors

### Light Theme
- **Primary Text:** #212124 (--text-primary)
- **Secondary Text:** #6B6B6B (--text-secondary)
- **Tertiary Text:** #9B9B9B (--text-tertiary)
- **Placeholder:** #B0B0B0 (--text-placeholder)

### Dark Theme
- **Primary Text:** #E0E0E0 (--text-primary)
- **Secondary Text:** #A0A0A0 (--text-secondary)
- **Tertiary Text:** #808080 (--text-tertiary)
- **Placeholder:** #606060 (--text-placeholder)

### Accent
- **Accent:** #DD4814 (--accent)

---

## Best Practices

1. **Use font-heading for all headings:** Apply `font-heading` class to h1-h6 elements
2. **Use font-sans for body text:** This is the default, but can be explicitly set
3. **Use font-mono for code:** Apply to code blocks and inline code
4. **Maintain text hierarchy:** Larger sizes for more important content
5. **Use font-medium for interactive elements:** Buttons, links, labels
6. **Keep line-height appropriate:** 1.5 for body, 1.2 for headings
7. **Use semantic HTML:** Use proper heading levels (h1-h6) for structure

---

## Tailwind Classes Quick Reference

```
Font Sizes:
text-xs    = 12px (0.75rem)
text-sm    = 14px (0.875rem)
text-base  = 16px (1rem)
text-lg    = 18px (1.125rem)
text-xl    = 20px (1.25rem)
text-2xl   = 24px (1.5rem)
text-3xl   = 30px (1.875rem)
text-4xl   = 36px (2.25rem)

Font Families:
font-sans     = Ubuntu
font-heading  = Alan Sans
font-mono     = Ubuntu Mono

Font Weights:
font-light     = 300
font-normal    = 400
font-medium    = 500
font-semibold  = 600
font-bold      = 700

Text Colors:
text-light-text              = Light theme primary
text-dark-text               = Dark theme primary
text-light-text-secondary    = Light theme secondary
text-dark-text-secondary     = Dark theme secondary
text-accent                  = Accent color (#DD4814)
```

---

## Examples by Component

### Top Bar
```tsx
<h1 className="font-heading text-xl text-light-text dark:text-dark-text">
  Cirkelline
</h1>
```

### Button
```tsx
<button className="px-4 py-2 text-sm font-medium">
  Click me
</button>
```

### Form Label
```tsx
<label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
  Email
</label>
```

### Chat Message
```tsx
<div className="text-base font-sans">
  User message content
</div>
```

### Section Header
```tsx
<h2 className="font-sans text-sm font-bold text-light-text dark:text-dark-text">
  Sessions
</h2>
```

### Helper Text
```tsx
<p className="text-xs text-light-text/50 dark:text-dark-text/50">
  200/200 characters
</p>