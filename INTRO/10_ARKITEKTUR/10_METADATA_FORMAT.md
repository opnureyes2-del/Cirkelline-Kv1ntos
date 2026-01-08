# INTRO Metadata Format Template

This template documents frontmatter (YAML metadata) format for INTRO files.

## YAML Frontmatter

Some INTRO files use YAML frontmatter at the top:

```markdown
---
title: Document Title
author: Rasmus
date: 2026-01-01
status: active
tags: [architecture, design, system]
---

# Document Title

Content starts here...
```

## Common Metadata Fields

### Required Fields
```yaml
---
title: Document Title        # Clear, descriptive title
date: YYYY-MM-DD            # Creation or last update date
---
```

### Optional Fields
```yaml
---
author: Rasmus              # Primary author
status: active              # active, draft, archived, deprecated
version: 1.0.0              # Semantic versioning
tags: [tag1, tag2]          # Categorization
project: lib-admin          # Associated project
---
```

## Field Descriptions

| Field | Type | Format | Example |
|-------|------|--------|---------|
| **title** | string | Any text | "System Architecture Overview" |
| **author** | string | Name | "Rasmus", "Kv1nt", "Ivo" |
| **date** | string | YYYY-MM-DD | "2026-01-01" |
| **status** | string | Predefined | "active", "draft", "archived" |
| **version** | string | Semantic | "1.0.0", "2.1.3" |
| **tags** | array | List | ["architecture", "design"] |
| **project** | string | Project name | "lib-admin", "cosmic-library" |

## Status Values

| Status | Meaning | When to Use |
|--------|---------|-------------|
| **active** | Currently maintained | Actively used documents |
| **draft** | Work in progress | Incomplete documents |
| **review** | Needs review | Awaiting KOMMANDØR approval |
| **archived** | No longer active | Historical reference |
| **deprecated** | Superseded | Replaced by newer version |

## Examples

### Minimal Frontmatter
```yaml
---
title: Quick TODO List
date: 2026-01-01
---
```

### Full Frontmatter
```yaml
---
title: Cirkelline System Architecture
author: Rasmus
date: 2026-01-01
status: active
version: 2.0.0
tags: [architecture, system-design, cirkelline]
project: cirkelline-system
description: Complete architecture overview for Cirkelline ecosystem
---
```

### Project-Specific
```yaml
---
title: lib-admin Database Schema
author: Kv1nt
date: 2025-12-15
status: active
version: 1.3.0
project: lib-admin
tags: [database, schema, postgresql]
related:
  - 10_ARKITEKTUR/10_DATABASE.md
  - 20_PROJEKTER/25_LIB_ADMIN.md
---
```

## When to Use Frontmatter

**Use frontmatter when:**
- Document needs metadata for automation
- Multiple authors collaborate
- Document has version tracking
- Categorization/search is important
- Integration with tools (e.g., Obsidian, Jekyll)

**Skip frontmatter when:**
- Simple TODO lists
- Quick notes
- Internal documentation
- File is self-explanatory from filename

## Automation Support

INTRO automation tools recognize these fields:
- **TEMPLATE_SYNC_AGENT** - Extracts title, author, date
- **Verification scripts** - Validates status, version
- **Search tools** - Indexes tags, project
- **Git hooks** - Updates date on commit

## Quality Score

**Pattern Quality:** 75/100
- **Usage:** 180+ files with frontmatter (35% of INTRO files)
- **Consistency:** Format stable for 30+ days
- **Field Count:** Average 3.5 fields per frontmatter
- **Most Used Field:** `title` (100%), `date` (95%), `author` (70%)

## Statistics

- **Files with frontmatter:** 182/520 (35%)
- **Most common fields:** title (182), date (173), author (128)
- **Average fields per file:** 3.5
- **Projects using frontmatter:** 6/9

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:55 | Template created from DNA extraction | Kv1nt |
| 2025-12-28 | 17:00 | Frontmatter pattern identified | TEMPLATE_SYNC_AGENT |
