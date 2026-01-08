# INTRO Section Structure Template

This template documents standard section hierarchy for INTRO files.

## Standard Section Hierarchy

INTRO files typically follow this structure:

```markdown
# Main Title (H1)

Brief introduction/overview paragraph

## Section 1 (H2)

Content for section 1

### Subsection 1.1 (H3)

Detailed content

### Subsection 1.2 (H3)

More details

## Section 2 (H2)

Content for section 2

## CHANGELOG (H2)

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
```

## Header Levels

| Level | Markdown | Purpose | Example |
|-------|----------|---------|---------|
| H1 | `# Title` | Document title (ONE per file) | `# 10_ARKITEKTUR` |
| H2 | `## Section` | Major sections | `## Overview`, `## Architecture` |
| H3 | `### Subsection` | Subsections | `### Components`, `### Dependencies` |
| H4 | `#### Detail` | Detailed breakdowns | `#### Frontend`, `#### Backend` |

## Common Sections

### Meta Sections (All Files)
```markdown
# Title

## Overview
Brief description of what this file contains

## Purpose
Why this file exists

## CHANGELOG
Change history
```

### Architecture Files
```markdown
# Architecture Document

## System Overview
High-level description

## Components
List of system components

## Dependencies
External dependencies

## Integration Points
How components connect

## CHANGELOG
```

### Project Files
```markdown
# Project Name

## Description
What the project does

## Status
Current project status

## Structure
Directory/file structure

## Getting Started
How to use/run

## CHANGELOG
```

### TODO Files
```markdown
# TODO List

## Active Tasks
Current work items

## Completed Tasks
Finished items

## Future Work
Planned improvements

## CHANGELOG
```

## Depth Guidelines

**Maximum heading depth:** H4 (####)

```markdown
# Document (H1) ✅
## Section (H2) ✅
### Subsection (H3) ✅
#### Detail (H4) ✅
##### Too deep (H5) ❌ - Avoid!
```

If you need more depth, consider:
- Breaking into multiple files
- Using lists instead of headers
- Restructuring content

## Section Naming

### Good Section Names ✅
```markdown
## Overview
## Architecture
## Components
## Dependencies
## Getting Started
## Implementation Details
## CHANGELOG
```

### Bad Section Names ❌
```markdown
## stuff                    ← Too vague
## Section 1               ← Not descriptive
## asdf                    ← Not professional
## SCREAMING_SNAKE_CASE    ← Hard to read
```

## Special Sections

### CHANGELOG (Required)
Always at the end, always H2 level:
```markdown
## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
```

### README (Optional)
For overview/navigation:
```markdown
## README

Quick navigation:
- [Section 1](#section-1)
- [Section 2](#section-2)
```

## Quality Score

**Pattern Quality:** 88/100
- **Usage:** 420+ files with consistent structure
- **Consistency:** Stable pattern for 60+ days
- **Max Depth Found:** 4 levels (H4)
- **Average Sections:** 5.2 per file

## Statistics

- **Files analyzed:** 520
- **Average section count:** 5.2
- **Most common H2:** "Overview" (380 files)
- **Second most common H2:** "CHANGELOG" (485 files)
- **Deepest nesting:** 4 levels (10%)

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:50 | Template created from DNA extraction | Kv1nt |
| 2025-12-28 | 16:00 | Section structure pattern identified | TEMPLATE_SYNC_AGENT |
