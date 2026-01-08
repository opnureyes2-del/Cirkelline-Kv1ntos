# Crowdin Integration Best Practices - Cirkelline System

**Comprehensive Deep Research Report**
**Date:** 2025-12-09
**Target:** Multi-repo Cirkelline ecosystem (cirkelline-system, lib-admin-main, Cosmic-Library-main)
**Languages:** da, en, sv, de, ar (RTL)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Crowdin Project Setup](#1-crowdin-project-setup)
3. [CI/CD Integration](#2-cicd-integration)
4. [File Formats](#3-file-formats)
5. [Quality Assurance](#4-quality-assurance)
6. [Webhook Integration](#5-webhook-integration)
7. [Best Practices](#6-best-practices)
8. [Implementation Roadmap](#7-implementation-roadmap)

---

## Executive Summary

This document provides production-ready Crowdin integration configuration for the Cirkelline ecosystem, consisting of three interconnected repositories:

- **cirkelline-system**: Main orchestrator (5 languages × 168 lines)
- **lib-admin-main**: Admin library (5 languages × 168 lines)
- **Cosmic-Library-main**: Media library (5 languages × 168 lines)

**Key Features:**
- Automated CI/CD with GitHub Actions
- RTL language support (Arabic)
- Translation Memory optimization
- QA checks for placeholders and missing translations
- Webhook-triggered PR creation
- Multi-repo shared TM

**Total Translation Volume:** 2,520 strings across 3 repos

---

## 1. Crowdin Project Setup

### 1.1 Project Structure for Multi-Repo Setup

Crowdin supports multiple repositories through a shared Translation Memory (TM) approach. Each repository maintains its own `crowdin.yml` configuration while sharing linguistic assets.

**Architecture:**

```
Crowdin Organization: Cirkelline
├── Project: cirkelline-system (Main)
│   ├── Shared TM: cirkelline-shared-tm
│   ├── Shared Glossary: cirkelline-terminology
│   └── Branches: main, develop, feature/*
├── Project: lib-admin-main (Admin)
│   ├── Uses: cirkelline-shared-tm
│   ├── Uses: cirkelline-terminology
│   └── Branches: main, develop
└── Project: Cosmic-Library-main (Media)
    ├── Uses: cirkelline-shared-tm
    ├── Uses: cirkelline-terminology
    └── Branches: main, develop
```

**Benefits:**
- Consistent translations across all products
- Reduced translation costs (reuse TM suggestions)
- Centralized terminology management
- Independent deployment cycles per repo

### 1.2 Language Configuration

**Supported Languages:**

| Code | Language | Direction | Special Considerations |
|------|----------|-----------|------------------------|
| `da` | Danish | LTR | Base Scandinavian language |
| `en` | English | LTR | Source language |
| `sv` | Swedish | LTR | Similar to Danish, TM suggestions enabled |
| `de` | German | LTR | Compound words, length checks +30% |
| `ar` | Arabic | RTL | RTL layout, numerals LTR, no italics |

**Crowdin Language Codes:**

```yaml
languages:
  - da    # Danish
  - en    # English (source)
  - sv    # Swedish
  - de    # German
  - ar    # Arabic
```

**Language Mapping for File Paths:**

```yaml
language_mapping:
  locale:
    da: da
    en: en
    sv: sv
    de: de
    ar: ar
  android_code:
    da: da
    ar: ar-rSA  # Arabic (Saudi Arabia)
  osx_code:
    da: da
    ar: ar-SA
```

### 1.3 RTL Language Handling (Arabic)

**Critical Considerations:**

1. **Text Direction:**
   - Set `dir="rtl"` in HTML root element for Arabic
   - Use CSS logical properties (`margin-inline-start` instead of `margin-left`)
   - Mirror UI elements (buttons, menus, icons)

2. **Bidirectional Content:**
   - English brand names remain LTR within RTL text
   - Numbers and dates remain LTR
   - URLs and email addresses remain LTR
   - Use Unicode Bidirectional Algorithm (BiDi) markers when needed

3. **Typography:**
   - Avoid bold text (readability issues in Arabic)
   - **Never** use italics (not used in Arabic typography)
   - Increase line height by 10-15% for Arabic
   - Use Arabic-optimized fonts (Noto Sans Arabic, Tajawal, IBM Plex Sans Arabic)

4. **UI Mirroring:**
   - Progress bars: right-to-left
   - Sliders: right-to-left
   - Navigation arrows: mirrored (← becomes →)
   - Icons with direction: mirrored

5. **QA Checks for Arabic:**
   - Verify RTL direction attribute
   - Check for proper BiDi handling
   - Test numeric formatting (Arabic vs. Western numerals)
   - Validate proper text alignment

**Crowdin RTL Settings:**

```yaml
# In crowdin.yml
files:
  - source: /locales/en/messages.json
    translation: /locales/%locale%/messages.json
    update_option: update_as_unapproved
    # RTL-specific settings
    escape_quotes: 0
    escape_special_characters: 0
```

---

## 2. CI/CD Integration

### 2.1 GitHub Actions Workflow

**Official Crowdin GitHub Action** provides more flexibility than native integration:
- Full control over security and repo access
- No need to authorize GitHub in third-party services
- Flexible workflow configuration
- Support for `[ci skip]` tags

**Workflow: `/home/rasmus/Desktop/projects/cirkelline-system/.github/workflows/crowdin.yml`**

```yaml
name: Crowdin Sync

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'locales/en/**'
  schedule:
    # Sync translations daily at 03:00 UTC
    - cron: '0 3 * * *'
  workflow_dispatch:
    # Manual trigger

permissions:
  contents: write
  pull-requests: write

jobs:
  sync-crowdin:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Upload sources to Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: true
          upload_translations: false
          download_translations: false
          crowdin_branch_name: ${{ github.ref_name }}
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CROWDIN_BRANCH_NAME: ${{ github.ref_name }}

      - name: Download translations from Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          upload_translations: false
          download_translations: true
          crowdin_branch_name: ${{ github.ref_name }}
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          localization_branch_name: l10n_${{ github.ref_name }}
          create_pull_request: true
          pull_request_title: 'New Crowdin translations'
          pull_request_body: |
            **Automated translation update**

            This PR contains updated translations from Crowdin.

            Please review the changes before merging.

            - [ ] Verify translation quality
            - [ ] Check placeholder consistency
            - [ ] Test RTL languages (Arabic)
            - [ ] Validate JSON structure
          pull_request_labels: |
            i18n
            translations
            automated
          pull_request_reviewers: |
            rasmus
            ivo
          commit_message: 'chore: update translations from Crowdin [ci skip]'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CROWDIN_BRANCH_NAME: ${{ github.ref_name }}
```

### 2.2 Automatic Upload of Source Strings

**Trigger on English Source Changes:**

```yaml
# Upload-only workflow
name: Upload Sources to Crowdin

on:
  push:
    branches: [main]
    paths:
      - 'locales/en/messages.json'

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Upload to Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: true
          upload_translations: false
          download_translations: false
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2.3 Automatic Download of Translations

**Scheduled Translation Download:**

```yaml
name: Download Translations

on:
  schedule:
    # Every day at 03:00 UTC (off-peak)
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download from Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          download_translations: true
          create_pull_request: true
          localization_branch_name: l10n_main
          pull_request_title: 'New translations from Crowdin'
          commit_message: 'chore: update translations [ci skip]'
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2.4 Branching Strategies in Crowdin

**Version Management Approach:**

```
Git Repository               Crowdin Project
────────────────            ─────────────────
main                   ←→   main (production)
develop                ←→   develop (staging)
feature/new-ui         ←→   feature/new-ui (development)
release/v2.0           ←→   release/v2.0 (pre-production)
```

**Branch Configuration:**

1. **Main Branch (Production):**
   - Only approved translations
   - 100% translation coverage required
   - QA checks mandatory
   - Auto-merge from develop when stable

2. **Develop Branch (Staging):**
   - Active translation work
   - Allow draft translations
   - Pre-translation with TM enabled
   - Merge to main after approval

3. **Feature Branches:**
   - Created automatically on push
   - Inherit translations from develop
   - Show within version branch (hide duplicates)
   - Delete after merge

**Crowdin Branch Settings:**

```yaml
# In crowdin.yml
files:
  - source: /locales/en/messages.json
    translation: /locales/%locale%/messages.json
    update_option: update_as_unapproved
    # Branch-specific settings
    preserve_hierarchy: true
    skip_untranslated_strings: false
    skip_untranslated_files: false
    export_only_approved: true  # For main branch
```

**Show Within Version Branch:**

This feature hides duplicate strings between branches, so only the original (usually from main) needs translation. All duplicates automatically receive translations from the original.

```yaml
# Enable in Crowdin project settings
# Settings > Import/Export > Show within a version branch
show_within_version_branch: true
```

---

## 3. File Formats

### 3.1 JSON File Support

**Current Structure:**

```json
{
  "common": {
    "loading": "Loading...",
    "error": "An error occurred"
  },
  "auth": {
    "login": "Log in",
    "logout": "Log out"
  },
  "errors": {
    "validation": {
      "required": "{field} is required",
      "minLength": "{field} must be at least {min} characters"
    }
  }
}
```

**Crowdin JSON Configuration:**

```yaml
files:
  - source: /locales/en/**/*.json
    translation: /locales/%locale%/**/%original_file_name%
    update_option: update_as_unapproved
    # JSON-specific settings
    type: json
    content_segmentation: 1  # Enable content segmentation
    translatable_elements:
      - /*/text()  # Translate all text nodes
    escape_quotes: 0
    escape_special_characters: 0
```

**Nested JSON Support:**

Crowdin automatically handles nested JSON structures. Use dot notation for context:

```
Key: common.loading
Context: common > loading
Translation: "Loading..."
```

### 3.2 Python Gettext (.po/.mo)

**If you add Python backend localization:**

**Directory Structure:**

```
backend/
└── locales/
    ├── da/
    │   └── LC_MESSAGES/
    │       ├── messages.po
    │       └── messages.mo
    ├── en/
    │   └── LC_MESSAGES/
    │       └── messages.pot (template)
    └── ar/
        └── LC_MESSAGES/
            ├── messages.po
            └── messages.mo
```

**Crowdin Configuration for .po Files:**

```yaml
files:
  - source: /backend/locales/en/LC_MESSAGES/messages.pot
    translation: /backend/locales/%locale%/LC_MESSAGES/messages.po
    update_option: update_as_unapproved
    type: gettext
    # Automatically compile to .mo
    export_pattern: /backend/locales/%locale%/LC_MESSAGES/messages.po
```

**Automatic .mo Compilation:**

Install Crowdin app: "Compile Gettext .po files to .mo"

This app automatically converts .po files to .mo format after download from Crowdin, ensuring binary compatibility.

**Alternative: GitHub Action Step:**

```yaml
- name: Compile .po to .mo
  run: |
    sudo apt-get install -y gettext
    find backend/locales -name "*.po" -exec msgfmt {} -o {}.mo \;
```

### 3.3 Placeholders and Interpolation

**Variable Syntax:**

Cirkelline uses ICU-style placeholders:

```json
{
  "errors": {
    "validation": {
      "required": "{field} is required",
      "minLength": "{field} must be at least {min} characters",
      "maxLength": "{field} must be at most {max} characters"
    }
  },
  "time": {
    "ago": "{time} ago",
    "in": "In {time}"
  }
}
```

**ICU MessageFormat Configuration:**

```yaml
files:
  - source: /locales/en/messages.json
    translation: /locales/%locale%/messages.json
    # Enable ICU detection
    icu_tag_detection: 1
    content_segmentation: 1
```

**Crowdin ICU Support:**

Crowdin automatically detects and highlights ICU placeholders:
- `{variable}` - Simple variable
- `{count, plural, one {# item} other {# items}}` - Pluralization
- `{gender, select, male {He} female {She} other {They}}` - Selection

**QA Checks for Placeholders:**

Crowdin validates:
- Placeholder presence in translation
- Correct placeholder syntax
- Placeholder order (can be changed for natural language flow)

**Example with Context:**

```json
{
  "deleteConfirm": "Are you sure you want to delete {documentName}?"
}
```

Crowdin Editor shows:
- **Source:** `Are you sure you want to delete {documentName}?`
- **Placeholder:** `{documentName}` (highlighted, cannot be translated)
- **Context:** "Delete confirmation dialog"

**Advanced ICU Pluralization:**

```json
{
  "itemCount": "{count, plural, =0 {No items} one {# item} other {# items}}"
}
```

**Arabic Plural Rules:**

Arabic has 6 plural forms (vs. English 2):
- `zero`: 0 items
- `one`: 1 item
- `two`: 2 items
- `few`: 3-10 items
- `many`: 11-99 items
- `other`: 100+ items

Crowdin handles this automatically per language.

---

## 4. Quality Assurance

### 4.1 Terminology Management

**Glossary Structure:**

Create shared glossary: `cirkelline-terminology.tbx`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE martif SYSTEM "TBXcoreStructV02.dtd">
<martif type="TBX" xml:lang="en">
  <martifHeader>
    <fileDesc>
      <titleStmt>
        <title>Cirkelline Terminology</title>
      </titleStmt>
      <sourceDesc>
        <p>Cirkelline product terminology</p>
      </sourceDesc>
    </fileDesc>
  </martifHeader>
  <text>
    <body>
      <!-- Example Terms -->
      <termEntry id="agent">
        <langSet xml:lang="en">
          <tig>
            <term>Agent</term>
            <termNote type="partOfSpeech">noun</termNote>
            <descrip type="definition">AI specialist that performs specific tasks</descrip>
          </tig>
        </langSet>
        <langSet xml:lang="da">
          <tig>
            <term>Agent</term>
            <termNote type="partOfSpeech">substantiv</termNote>
          </tig>
        </langSet>
        <langSet xml:lang="ar">
          <tig>
            <term>وكيل</term>
            <termNote type="partOfSpeech">اسم</termNote>
          </tig>
        </langSet>
      </termEntry>

      <termEntry id="orchestrator">
        <langSet xml:lang="en">
          <tig>
            <term>Orchestrator</term>
            <termNote type="partOfSpeech">noun</termNote>
            <termNote type="customerSubset">DO NOT TRANSLATE</termNote>
            <descrip type="definition">Main coordinator that routes tasks to specialists</descrip>
          </tig>
        </langSet>
      </termEntry>

      <termEntry id="session">
        <langSet xml:lang="en">
          <tig>
            <term>Session</term>
            <termNote type="partOfSpeech">noun</termNote>
          </tig>
        </langSet>
        <langSet xml:lang="da">
          <tig>
            <term>Session</term>
          </tig>
        </langSet>
        <langSet xml:lang="de">
          <tig>
            <term>Sitzung</term>
          </tig>
        </langSet>
        <langSet xml:lang="ar">
          <tig>
            <term>جلسة</term>
          </tig>
        </langSet>
      </termEntry>
    </body>
  </text>
</martif>
```

**Glossary Import to Crowdin:**

1. Go to Crowdin project → Resources → Glossaries
2. Click "Create Glossary" → Name: "Cirkelline Terminology"
3. Upload TBX file or CSV:

```csv
Term,Part of Speech,Definition,Danish,Swedish,German,Arabic,Do Not Translate
Agent,noun,AI specialist,Agent,Agent,Agent,وكيل,No
Orchestrator,noun,Main coordinator,,,,,Yes
Session,noun,Chat conversation,Session,Session,Sitzung,جلسة,No
Knowledge Base,noun,Private document storage,Videnbase,Kunskapsbas,Wissensbasis,قاعدة المعرفة,No
Deep Research,noun,Comprehensive search mode,,,,,No
Translation Memory,noun,TM database,,,,,Yes (TM)
```

4. Assign to all projects (cirkelline-system, lib-admin-main, Cosmic-Library-main)

**Glossary Benefits:**

- Terms underlined in Crowdin Editor
- Hover to see definition and approved translation
- Consistency across all projects
- Faster translation (copy approved terms)

### 4.2 Style Guides

**Create Style Guide Document:**

Upload to Crowdin project → Resources → Style Guide

```markdown
# Cirkelline Translation Style Guide

## Tone and Voice
- **Friendly but professional**
- Use conversational language
- Avoid overly technical jargon
- Be concise and clear

## Formatting
- **Buttons:** Title Case (e.g., "Save Changes")
- **Labels:** Sentence case (e.g., "Enter your email")
- **Error messages:** Sentence case, no period at end
- **Success messages:** Sentence case, no period

## Brand Terms (DO NOT TRANSLATE)
- Cirkelline
- Orchestrator
- AgentOS
- Deep Research (feature name)

## Placeholder Variables
- **Keep exactly as is:** `{field}`, `{min}`, `{max}`, `{time}`
- **Can be reordered** for natural language flow
- Example: "{field} er påkrævet" (Danish) vs "{field} is required" (English)

## Arabic-Specific
- **Do NOT use:** Bold text, italics
- **Use:** Western numerals (123) not Arabic numerals (١٢٣)
- **Formality:** Use Modern Standard Arabic (MSA), not dialects
- **Politeness:** Use polite forms (أنت not إنت)

## German-Specific
- **Formality:** Use formal "Sie" not informal "du"
- **Compound words:** Use correct compounds (e.g., "Systemeinstellungen" not "System Einstellungen")
- **Length:** Translations may be 30% longer, ensure UI fits

## Danish/Swedish
- **Similarity:** Leverage TM suggestions between da/sv
- **Formality:** Informal tone acceptable

## Punctuation
- **Questions:** Always end with "?"
- **Exclamations:** Use sparingly, only for success messages
- **Ellipsis:** Use "..." not "…" (three dots, not Unicode)

## Testing Checklist
- [ ] Placeholders present and correct
- [ ] No missing translations
- [ ] Text fits in UI (test German)
- [ ] RTL layout works (test Arabic)
- [ ] Glossary terms used consistently
```

### 4.3 QA Checks Configuration

**Crowdin QA Settings:**

Navigate to: Crowdin Project → Settings → QA Checks

**Enable These Checks:**

```yaml
qa_checks:
  # Critical for placeholders
  - variables_mismatch: true
    # Validates {field}, {min}, {max} placeholders

  # Missing translations
  - empty_translation: true

  # HTML/formatting
  - tags_mismatch: true
    # Validates JSON structure

  # Spacing issues
  - spaces_mismatch: true
    # Multiple spaces, leading/trailing spaces

  # Punctuation
  - punctuation_mismatch: true
    # Check for consistent punctuation

  # Numbers
  - numbers_mismatch: true
    # Ensure numbers match source

  # Length limits
  - max_length: true
    # German: +30%, Arabic: +20%
    configuration:
      - language: de
        max_length_percent: 130
      - language: ar
        max_length_percent: 120

  # Outdated translations
  - outdated_translation: true
    # Flag when source changed

  # Case consistency
  - character_case: true
    # Check for proper capitalization

  # Terminology
  - inconsistent_translation: true
    # Cross-reference with glossary
```

**Custom QA Checks:**

For advanced validation, create custom regex-based checks:

```yaml
custom_qa_checks:
  - name: "ICU Placeholder Format"
    description: "Validates ICU placeholder syntax"
    pattern: '\{[^}]+\}'
    type: "placeholder"
    languages: ["all"]

  - name: "No Bold in Arabic"
    description: "Prevent bold tags in Arabic"
    pattern: '<strong>|<b>|\*\*'
    type: "forbidden"
    languages: ["ar"]

  - name: "Ellipsis Format"
    description: "Use three dots, not Unicode"
    pattern: '…'
    type: "forbidden"
    languages: ["all"]
    suggestion: "Use ... instead"
```

**QA Check Workflow:**

1. Translator completes string
2. Crowdin runs QA checks automatically
3. Issues highlighted in red under translation
4. Translator fixes issues
5. Proofreader approves (if no issues)
6. Export only after all QA checks pass

**Filter Strings by QA Issues:**

In Crowdin Editor:
- Filter → "With any QA issue"
- Filter → "Tags mismatch"
- Filter → "Variables mismatch"
- Filter → "Empty translation"

### 4.4 In-Context Review

**In-Context Localization Setup:**

Enables translators to see and translate strings directly in the live app.

**Installation:**

1. **Add Crowdin In-Context Script:**

```html
<!-- In your app's HTML <head> -->
<script type="text/javascript">
  var _jipt = _jipt || [];
  _jipt.push(['project', 'cirkelline-system']);
  _jipt.push(['domain', 'cirkelline']);
</script>
<script type="text/javascript" src="//cdn.crowdin.com/jipt/jipt.js"></script>
```

2. **Enable In-Context Mode:**

Add query parameter to URL: `?in_context=true`

Example: `https://cirkelline.com?in_context=true`

3. **Translator Workflow:**

- Open app with `?in_context=true`
- Click on any text to translate
- Edit in overlay
- Save directly to Crowdin project
- Preview changes in real-time

**Screenshot Automation:**

```yaml
# GitHub Action to capture screenshots
name: Crowdin Screenshots

on:
  workflow_dispatch:

jobs:
  screenshots:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          npm install -g puppeteer
          npm install

      - name: Capture screenshots
        run: node scripts/capture-screenshots.js

      - name: Upload to Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          upload_translations: false
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          # Custom command to upload screenshots
          command: 'crowdin screenshot upload screenshots/*.png'
```

**Screenshot Capture Script:**

`/home/rasmus/Desktop/projects/cirkelline-system/scripts/capture-screenshots.js`

```javascript
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  const pages = [
    { url: 'http://localhost:3000', name: 'home' },
    { url: 'http://localhost:3000/chat', name: 'chat' },
    { url: 'http://localhost:3000/settings', name: 'settings' },
    { url: 'http://localhost:3000/profile', name: 'profile' },
  ];

  if (!fs.existsSync('screenshots')) {
    fs.mkdirSync('screenshots');
  }

  for (const pageData of pages) {
    await page.goto(pageData.url);
    await page.screenshot({
      path: `screenshots/${pageData.name}.png`,
      fullPage: true
    });
  }

  await browser.close();
})();
```

**Auto-Tagging Strings in Screenshots:**

Crowdin automatically:
1. Detects visible text in screenshots
2. Searches for matching strings in project
3. Tags strings on screenshot
4. Displays in Editor context panel

**Benefits:**

- Translators see UI context
- Prevent text overflow issues
- Understand button vs. label vs. title
- See string relationships (what appears together)

---

## 5. Webhook Integration

### 5.1 Webhook Configuration in Crowdin

**Setup Webhooks:**

1. Navigate to: Crowdin Project → Settings → Integrations → Webhooks
2. Click "Add Webhook"

**Webhook 1: Translation Completed**

```yaml
Name: GitHub Action Trigger - Translation Complete
URL: https://api.github.com/repos/rasmus/cirkelline-system/dispatches
Method: POST
Events:
  - "translation.updated" (string translated)
  - "file.approved" (file 100% approved)
Payload:
  {
    "event_type": "crowdin_translation_updated",
    "client_payload": {
      "project": "cirkelline-system",
      "language": "%language%",
      "file": "%file_name%"
    }
  }
Headers:
  Authorization: token ghp_YOUR_GITHUB_PAT
  Accept: application/vnd.github.v3+json
  Content-Type: application/json
```

**Webhook 2: File 100% Translated**

```yaml
Name: Auto Download on 100%
URL: https://api.github.com/repos/rasmus/cirkelline-system/dispatches
Method: POST
Events:
  - "file.translated" (file 100% translated)
Payload:
  {
    "event_type": "crowdin_file_ready",
    "client_payload": {
      "project": "cirkelline-system",
      "language": "%language%",
      "file": "%file_name%",
      "branch": "%branch%"
    }
  }
```

### 5.2 GitHub Action Triggered by Webhook

**Workflow: `/.github/workflows/crowdin-webhook.yml`**

```yaml
name: Crowdin Webhook Handler

on:
  repository_dispatch:
    types: [crowdin_translation_updated, crowdin_file_ready]

permissions:
  contents: write
  pull-requests: write

jobs:
  download-translations:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Log webhook event
        run: |
          echo "Event: ${{ github.event.action }}"
          echo "Project: ${{ github.event.client_payload.project }}"
          echo "Language: ${{ github.event.client_payload.language }}"
          echo "File: ${{ github.event.client_payload.file }}"

      - name: Download translations from Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          download_translations: true
          crowdin_branch_name: ${{ github.event.client_payload.branch || 'main' }}
          config: crowdin.yml
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          # Don't create PR immediately, accumulate changes
          create_pull_request: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check if translations changed
        id: check_changes
        run: |
          if [[ -n $(git status -s) ]]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
          fi

      - name: Create Pull Request
        if: steps.check_changes.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          branch: l10n_${{ github.event.client_payload.language }}
          title: 'i18n: Update ${{ github.event.client_payload.language }} translations'
          body: |
            ## Translation Update

            **Language:** ${{ github.event.client_payload.language }}
            **File:** ${{ github.event.client_payload.file }}
            **Triggered by:** Crowdin webhook

            ### Changes
            - [ ] Review translation quality
            - [ ] Verify placeholders
            - [ ] Test in UI (especially RTL for Arabic)

            **Auto-generated by Crowdin webhook**
          labels: |
            i18n
            translations
            ${{ github.event.client_payload.language }}
          reviewers: |
            rasmus
          commit-message: 'i18n: update ${{ github.event.client_payload.language }} translations [ci skip]'
```

### 5.3 Automatic PR Creation

**PR Workflow:**

1. **Translator completes file in Crowdin** (or reaches 100%)
2. **Crowdin webhook fires** → GitHub repository_dispatch
3. **GitHub Action triggers:**
   - Downloads latest translations
   - Creates language-specific branch (`l10n_da`, `l10n_ar`)
   - Commits changes with `[ci skip]` tag
   - Creates Pull Request
4. **PR Review:**
   - Auto-assigns reviewers
   - Labels: `i18n`, `translations`, language code
   - Checklist in PR body
5. **Merge:**
   - Manual merge after review
   - Triggers deployment pipeline (without re-uploading to Crowdin due to `[ci skip]`)

**Advanced: Auto-Merge for Trusted Languages**

```yaml
- name: Auto-merge if Danish/Swedish
  if: |
    steps.check_changes.outputs.changed == 'true' &&
    (github.event.client_payload.language == 'da' ||
     github.event.client_payload.language == 'sv')
  run: |
    gh pr merge l10n_${{ github.event.client_payload.language }} \
      --auto --squash --delete-branch
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Webhook Failure Handling:**

Crowdin automatically disables webhooks that fail 100+ times in 24 hours (4xx/5xx responses).

**To prevent:**
- Use valid GitHub PAT with `repo` scope
- Test webhook with "Send Test Request" in Crowdin
- Monitor webhook logs in Crowdin Settings → Webhooks → View Logs

---

## 6. Best Practices

### 6.1 Translation Memory (TM) Optimization

**Shared TM Setup:**

1. **Create Shared TM:**
   - Crowdin → Resources → Translation Memories
   - Name: `cirkelline-shared-tm`
   - Languages: da, en, sv, de, ar

2. **Assign to All Projects:**
   - cirkelline-system → Settings → Translation Memories → Assign `cirkelline-shared-tm`
   - lib-admin-main → Same
   - Cosmic-Library-main → Same

3. **Set TM Priority:**

```yaml
# In each project
TM Priority:
  1. Project-specific TM (Priority: 5)
  2. cirkelline-shared-tm (Priority: 3)
  3. Other shared TMs (Priority: 1)
```

**TM Match Types:**

| Match Type | Description | Usage |
|------------|-------------|-------|
| Perfect Match (101%) | Text + context identical | Auto-apply |
| 100% Match | Text identical, context differs | Suggest |
| Fuzzy Match (75-99%) | Similar text | Pre-fill, review required |
| <75% | Too different | Ignore |

**Auto-Substitution:**

Enable: Project Settings → Translation Memories → Auto-substitution

Automatically replaces:
- HTML tags
- Placeholders (`{field}` → `{nombre}`)
- Numbers
- URLs
- Email addresses

**Pre-Translation Strategy:**

```yaml
Pre-translation Priority:
  1. Perfect Match (101%) → Auto-apply
  2. 100% Match → Auto-apply if from same project
  3. Fuzzy Match (90-99%) → Pre-fill as draft
  4. Machine Translation → Pre-fill if no TM (see 6.2)
```

**Enable in Crowdin:**

Project → Pre-translation → Configure:
- ✅ Apply perfect matches
- ✅ Apply 100% matches
- ✅ Pre-translate via TM (90%+)
- ✅ Auto-substitution enabled
- ⬜ Apply fuzzy matches (manual review recommended)

**TM Cleaner App:**

Install from Crowdin Store: "TM Cleaner"

- Removes duplicate entries
- Keeps unique translations
- Run monthly to optimize performance

**TM Export/Import:**

```bash
# Export TM (for backup or migration)
crowdin tm download \
  --tm-id 12345 \
  --format tmx \
  --source-language-id en \
  --target-language-id da

# Import to another project
crowdin tm upload \
  --tm-id 67890 \
  --file cirkelline-tm-da.tmx
```

### 6.2 Machine Translation Pre-Fill

**Supported MT Engines:**

| Engine | Cost | Quality | Best For |
|--------|------|---------|----------|
| Google Translate | $20/1M chars | Good | General content |
| DeepL Pro | €25/1M chars | Excellent | European languages (da, sv, de) |
| Microsoft Translator | $10/1M chars | Good | Technical content |
| Amazon Translate | $15/1M chars | Good | High volume |

**Recommendation for Cirkelline:**

- **DeepL Pro:** Danish, Swedish, German (high quality)
- **Google Translate:** Arabic (better RTL support)

**Setup DeepL Integration:**

1. Crowdin → Settings → Integrations → Machine Translation
2. Add DeepL Pro API key
3. Configure:

```yaml
MT Configuration:
  Engine: DeepL Pro
  Languages:
    - da (Danish)
    - sv (Swedish)
    - de (German)
  Pre-translate:
    - Apply if no TM match
    - Mark as draft (requires review)
  Auto-translate:
    - Never (always require human review)
```

**Setup Google Translate for Arabic:**

```yaml
MT Configuration:
  Engine: Google Translate
  Languages:
    - ar (Arabic)
  Pre-translate:
    - Apply if no TM match
    - Mark as draft
  Settings:
    - Use Modern Standard Arabic (MSA)
    - Formal tone
```

**Pre-Translation Workflow:**

1. **Developer pushes source (English)**
2. **Crowdin uploads sources**
3. **Pre-translation runs automatically:**
   - Check TM for Perfect Match → Apply
   - Check TM for 100% Match → Apply
   - Check TM for 90%+ Fuzzy → Pre-fill as draft
   - No TM match → MT pre-fill as draft
4. **Translator reviews:**
   - Approves TM suggestions
   - Post-edits MT suggestions
   - Translates remaining strings
5. **Proofreader approves**
6. **Export to GitHub**

**Cost Estimation:**

Total strings: 168 per language × 3 projects = 504 strings
Avg. characters per string: ~40
Total characters: 504 × 40 = 20,160 chars per language

**Danish (DeepL):**
- 20,160 chars × €0.000025 = €0.50 per pre-translation
- With TM reuse (70%): €0.15

**Arabic (Google):**
- 20,160 chars × $0.00002 = $0.40 per pre-translation
- With TM reuse (50%): $0.20

**Annual cost (monthly updates):**
- Danish/Swedish/German: ~€20/year
- Arabic: ~$10/year
- **Total: ~€30/year** (negligible)

**Quality Control:**

- **Never auto-approve MT** (always require human review)
- Enable "Save only approved to TM" (prevent MT pollution)
- Use MT as **suggestion**, not final translation

### 6.3 Context for Translators

**String Context Types:**

1. **File Context:**
   - Automatic from file path: `locales/en/messages.json`
   - Shows translator which feature (auth, chat, documents)

2. **Key Context:**
   - Automatic from JSON key: `errors.validation.required`
   - Shows nested structure

3. **Manual Context:**
   - Add via Crowdin Editor or API
   - Describe UI location, usage

4. **Screenshot Context:**
   - Most effective
   - Shows exact UI placement

**Adding Manual Context:**

**Via Crowdin Editor:**
1. Select string in Editor
2. Click "Context" tab
3. Add description:

```
String: "Delete"
Context: "Button in document list to permanently delete a document.
Shows confirmation dialog before deletion."
```

**Via API (Bulk Context Upload):**

```bash
# context.json
{
  "common.delete": "Button to delete items, shows confirmation dialog",
  "auth.login": "Primary login button on authentication page",
  "errors.validation.required": "Error message shown below form field when left empty",
  "chat.typeMessage": "Placeholder text in chat input field"
}
```

```bash
curl -X POST \
  https://api.crowdin.com/api/v2/projects/{projectId}/strings \
  -H "Authorization: Bearer $CROWDIN_TOKEN" \
  -d @context.json
```

**Max Length Annotations:**

Add max length for UI-constrained strings:

```json
{
  "common.save": {
    "translation": "Save",
    "maxLength": 15,
    "context": "Button label, max 15 chars to fit mobile layout"
  }
}
```

**Screenshot Best Practices:**

1. **Capture all key screens:**
   - Login page
   - Main dashboard
   - Chat interface
   - Settings
   - Profile
   - Error states
   - Success states

2. **Update regularly:**
   - When UI changes
   - When new features added
   - Monthly refresh

3. **Tag strings automatically:**
   - Use In-Context mode
   - Crowdin auto-tags visible strings

4. **Organize by feature:**
   - Folder: `screenshots/auth/`
   - Folder: `screenshots/chat/`
   - Folder: `screenshots/settings/`

### 6.4 Screenshot Integration

**Automated Screenshot Capture:**

```javascript
// scripts/capture-screenshots.js
const puppeteer = require('puppeteer');
const { CrowdinApi } = require('@crowdin/crowdin-api-client');

const crowdin = new CrowdinApi({
  token: process.env.CROWDIN_PERSONAL_TOKEN,
});

const projectId = parseInt(process.env.CROWDIN_PROJECT_ID);

async function captureAndUpload() {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Set viewport to common desktop size
  await page.setViewport({ width: 1920, height: 1080 });

  const screens = [
    {
      url: 'http://localhost:3000/login',
      name: 'auth-login',
      selector: 'form[name="login"]',
      tags: ['auth.login', 'auth.email', 'auth.password', 'common.submit']
    },
    {
      url: 'http://localhost:3000/chat',
      name: 'chat-main',
      selector: '#chat-container',
      tags: ['chat.typeMessage', 'chat.sendMessage', 'chat.newChat']
    },
    {
      url: 'http://localhost:3000/settings',
      name: 'settings-profile',
      selector: '#settings-panel',
      tags: ['user.profile', 'user.language', 'user.theme']
    },
    // RTL version for Arabic
    {
      url: 'http://localhost:3000/chat?lang=ar',
      name: 'chat-main-rtl',
      selector: '#chat-container',
      tags: ['chat.typeMessage', 'chat.sendMessage', 'chat.newChat'],
      rtl: true
    }
  ];

  for (const screen of screens) {
    await page.goto(screen.url, { waitUntil: 'networkidle0' });

    // Wait for specific element
    await page.waitForSelector(screen.selector);

    // Capture screenshot
    const screenshotBuffer = await page.screenshot({
      fullPage: false,
      clip: await page.evaluate((sel) => {
        const element = document.querySelector(sel);
        const { x, y, width, height } = element.getBoundingClientRect();
        return { x, y, width, height };
      }, screen.selector)
    });

    // Upload to Crowdin
    try {
      // 1. Upload screenshot file
      const storage = await crowdin.uploadStorageApi.addStorage(
        screen.name + '.png',
        screenshotBuffer
      );

      // 2. Add screenshot to project
      const screenshot = await crowdin.screenshotsApi.addScreenshot(projectId, {
        storageId: storage.data.id,
        name: screen.name,
        autoTag: true  // Auto-tag visible strings
      });

      console.log(`✓ Uploaded screenshot: ${screen.name}`);

      // 3. Manually tag specific strings (if auto-tag misses some)
      for (const tag of screen.tags) {
        await crowdin.screenshotsApi.addTag(
          projectId,
          screenshot.data.id,
          {
            stringId: await getStringId(tag),  // Helper function
            position: { x: 0, y: 0, width: 100, height: 50 }  // Auto-detect or manual
          }
        );
      }

    } catch (error) {
      console.error(`✗ Failed to upload ${screen.name}:`, error.message);
    }
  }

  await browser.close();
  console.log('Screenshot capture complete!');
}

// Helper: Find string ID by key
async function getStringId(key) {
  const strings = await crowdin.sourceStringsApi.listProjectStrings(projectId, {
    filter: key,
    limit: 1
  });
  return strings.data[0]?.data.id;
}

captureAndUpload();
```

**GitHub Action for Screenshots:**

```yaml
name: Update Crowdin Screenshots

on:
  workflow_dispatch:
  schedule:
    # Monthly on 1st at 02:00 UTC
    - cron: '0 2 1 * *'

jobs:
  screenshots:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          npm install
          npm install -g puppeteer @crowdin/crowdin-api-client

      - name: Start dev server
        run: |
          npm run dev &
          sleep 10  # Wait for server to start

      - name: Capture and upload screenshots
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
        run: node scripts/capture-screenshots.js

      - name: Stop dev server
        run: pkill -f "npm run dev"
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Day 1-2: Crowdin Setup**

- [ ] Create Crowdin account (if not exists)
- [ ] Create 3 projects:
  - `cirkelline-system`
  - `lib-admin-main`
  - `Cosmic-Library-main`
- [ ] Configure languages: da, en, sv, de, ar
- [ ] Create shared TM: `cirkelline-shared-tm`
- [ ] Create glossary: `cirkelline-terminology`

**Day 3-4: Repository Configuration**

- [ ] Add `crowdin.yml` to each repo (see configs below)
- [ ] Create GitHub secrets:
  - `CROWDIN_PROJECT_ID` (for each repo)
  - `CROWDIN_PERSONAL_TOKEN` (shared)
- [ ] Add GitHub Actions workflows:
  - `.github/workflows/crowdin.yml`
  - `.github/workflows/crowdin-webhook.yml`

**Day 5-7: Initial Upload**

- [ ] Run initial source upload:
  ```bash
  crowdin upload sources
  ```
- [ ] Verify files in Crowdin dashboard
- [ ] Test download workflow:
  ```bash
  crowdin download translations
  ```
- [ ] Validate JSON structure

### Phase 2: Quality Setup (Week 2)

**Day 8-9: QA Configuration**

- [ ] Enable QA checks in Crowdin
- [ ] Configure custom QA checks for placeholders
- [ ] Set max length limits (German +30%, Arabic +20%)
- [ ] Test QA checks with sample translations

**Day 10-11: Glossary & TM**

- [ ] Populate glossary with 50+ key terms
- [ ] Export existing translations to TM
- [ ] Assign shared TM to all projects
- [ ] Set TM priorities

**Day 12-14: Screenshots**

- [ ] Create screenshot capture script
- [ ] Capture key screens (login, chat, settings)
- [ ] Upload to Crowdin
- [ ] Auto-tag strings
- [ ] Verify context in Editor

### Phase 3: Automation (Week 3)

**Day 15-16: CI/CD**

- [ ] Test GitHub Action on push
- [ ] Verify source upload automation
- [ ] Test scheduled translation download
- [ ] Validate PR creation

**Day 17-18: Webhooks**

- [ ] Configure Crowdin webhooks
- [ ] Create GitHub PAT for webhook authentication
- [ ] Test webhook trigger
- [ ] Verify automatic PR creation

**Day 19-21: Testing**

- [ ] Full end-to-end test:
  1. Update English source
  2. Push to GitHub
  3. Verify Crowdin upload
  4. Translate in Crowdin
  5. Trigger webhook
  6. Verify PR creation
  7. Merge PR
  8. Validate deployed translations

### Phase 4: Optimization (Week 4)

**Day 22-23: MT Integration**

- [ ] Setup DeepL Pro account
- [ ] Configure DeepL for da, sv, de
- [ ] Configure Google Translate for ar
- [ ] Test pre-translation
- [ ] Review MT quality

**Day 24-25: Style Guide**

- [ ] Create comprehensive style guide
- [ ] Upload to Crowdin
- [ ] Train translators
- [ ] Review first batch of translations

**Day 26-28: Documentation**

- [ ] Document workflow for developers
- [ ] Create translator guide
- [ ] Write troubleshooting guide
- [ ] Training session for team

---

## Crowdin Configuration Files

### `/home/rasmus/Desktop/projects/cirkelline-system/crowdin.yml`

```yaml
# Crowdin configuration for cirkelline-system
# Documentation: https://support.crowdin.com/configuration-file/

project_id: "YOUR_PROJECT_ID"  # Set via environment variable: CROWDIN_PROJECT_ID
api_token: "YOUR_API_TOKEN"    # Set via environment variable: CROWDIN_PERSONAL_TOKEN

preserve_hierarchy: true

files:
  - source: /locales/en/**/*.json
    translation: /locales/%locale%/**/%original_file_name%
    update_option: update_as_unapproved
    type: auto

    # Content segmentation for better TM matching
    content_segmentation: 1

    # Enable ICU message format detection
    icu_tag_detection: 1

    # Escape settings
    escape_quotes: 0
    escape_special_characters: 0

    # Export settings
    skip_untranslated_strings: false
    skip_untranslated_files: false
    export_only_approved: false  # Set to true for production branch

    # Translation strategy
    translate_hidden: true

    # Language-specific overrides
    languages_mapping:
      locale:
        da: da
        en: en
        sv: sv
        de: de
        ar: ar
```

### `/home/rasmus/Desktop/projects/lib-admin-main/crowdin.yml`

```yaml
# Crowdin configuration for lib-admin-main

project_id_env: "CROWDIN_PROJECT_ID"
api_token_env: "CROWDIN_PERSONAL_TOKEN"

preserve_hierarchy: true

files:
  - source: /backend/locales/en/**/*.json
    translation: /backend/locales/%locale%/**/%original_file_name%
    update_option: update_as_unapproved
    type: auto
    content_segmentation: 1
    icu_tag_detection: 1
    escape_quotes: 0
    escape_special_characters: 0
    skip_untranslated_strings: false
    skip_untranslated_files: false
    export_only_approved: false

    languages_mapping:
      locale:
        da: da
        en: en
        sv: sv
        de: de
        ar: ar
```

### `/home/rasmus/Desktop/projects/Cosmic-Library-main/crowdin.yml`

```yaml
# Crowdin configuration for Cosmic-Library-main

project_id_env: "CROWDIN_PROJECT_ID"
api_token_env: "CROWDIN_PERSONAL_TOKEN"

preserve_hierarchy: true

files:
  - source: /backend/locales/en/**/*.json
    translation: /backend/locales/%locale%/**/%original_file_name%
    update_option: update_as_unapproved
    type: auto
    content_segmentation: 1
    icu_tag_detection: 1
    escape_quotes: 0
    escape_special_characters: 0
    skip_untranslated_strings: false
    skip_untranslated_files: false
    export_only_approved: false

    languages_mapping:
      locale:
        da: da
        en: en
        sv: sv
        de: de
        ar: ar
```

---

## GitHub Actions Workflows

### `/home/rasmus/Desktop/projects/cirkelline-system/.github/workflows/crowdin-sync.yml`

```yaml
name: Crowdin Sync

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'locales/en/**/*.json'
  schedule:
    # Daily at 03:00 UTC
    - cron: '0 3 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Crowdin - Upload Sources
        if: github.event_name == 'push'
        uses: crowdin/github-action@v2
        with:
          upload_sources: true
          upload_translations: false
          download_translations: false
          crowdin_branch_name: ${{ github.ref_name }}
          config: crowdin.yml
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Crowdin - Download Translations
        if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          upload_translations: false
          download_translations: true
          crowdin_branch_name: main
          config: crowdin.yml
          localization_branch_name: l10n_main
          create_pull_request: true
          pull_request_title: 'i18n: Update translations from Crowdin'
          pull_request_body: |
            ## Automated Translation Update

            This PR contains the latest translations from Crowdin.

            ### Review Checklist
            - [ ] Verify placeholder consistency
            - [ ] Check RTL layout for Arabic
            - [ ] Validate German text length
            - [ ] Test in UI

            **Auto-generated by Crowdin**
          pull_request_labels: |
            i18n
            translations
            automated
          pull_request_reviewers: |
            rasmus
          commit_message: 'i18n: update translations [ci skip]'
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `/home/rasmus/Desktop/projects/cirkelline-system/.github/workflows/crowdin-webhook.yml`

```yaml
name: Crowdin Webhook Handler

on:
  repository_dispatch:
    types:
      - crowdin_translation_updated
      - crowdin_file_ready

permissions:
  contents: write
  pull-requests: write

jobs:
  handle-webhook:
    runs-on: ubuntu-latest

    steps:
      - name: Log Event
        run: |
          echo "Event Type: ${{ github.event.action }}"
          echo "Project: ${{ github.event.client_payload.project }}"
          echo "Language: ${{ github.event.client_payload.language }}"
          echo "File: ${{ github.event.client_payload.file }}"
          echo "Branch: ${{ github.event.client_payload.branch }}"

      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Download from Crowdin
        uses: crowdin/github-action@v2
        with:
          upload_sources: false
          download_translations: true
          crowdin_branch_name: ${{ github.event.client_payload.branch || 'main' }}
          config: crowdin.yml
          create_pull_request: false
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check Changes
        id: changes
        run: |
          if [[ -n $(git status -s) ]]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
          fi

      - name: Create PR
        if: steps.changes.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          branch: l10n_${{ github.event.client_payload.language }}_${{ github.run_number }}
          title: 'i18n: Update ${{ github.event.client_payload.language }} - ${{ github.event.client_payload.file }}'
          body: |
            ## Translation Update (Webhook Triggered)

            **Language:** ${{ github.event.client_payload.language }}
            **File:** ${{ github.event.client_payload.file }}
            **Branch:** ${{ github.event.client_payload.branch }}

            ### Review
            - [ ] Translation quality verified
            - [ ] Placeholders checked
            - [ ] UI tested

            **Triggered by:** Crowdin webhook at ${{ github.event.client_payload.timestamp }}
          labels: |
            i18n
            ${{ github.event.client_payload.language }}
            webhook-triggered
          reviewers: rasmus
          commit-message: 'i18n: ${{ github.event.client_payload.language }} update [ci skip]'
```

---

## Helper Scripts

### `/home/rasmus/Desktop/projects/cirkelline-system/scripts/crowdin-stats.sh`

```bash
#!/bin/bash
# Get translation progress statistics

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "==================================="
echo "Crowdin Translation Statistics"
echo "==================================="
echo ""

# Check if crowdin CLI is installed
if ! command -v crowdin &> /dev/null; then
    echo -e "${RED}Error: Crowdin CLI not installed${NC}"
    echo "Install: npm install -g @crowdin/cli"
    exit 1
fi

# Get project info
crowdin status --verbose

echo ""
echo "==================================="
echo "Project Summary"
echo "==================================="

# Parse and display per-language stats
crowdin status --json | jq -r '
  .[] |
  "Language: \(.language.name)",
  "  Translated: \(.translationProgress)%",
  "  Approved: \(.approvalProgress)%",
  "  Words: \(.words.total) total, \(.words.translated) translated",
  ""
'

echo ""
echo "==================================="
echo "Next Steps"
echo "==================================="
echo ""

# Check for languages below 80%
crowdin status --json | jq -r '
  .[] |
  select(.translationProgress < 80) |
  "⚠️  \(.language.name): \(.translationProgress)% - Needs attention"
'

# Check for languages 100% translated but not approved
crowdin status --json | jq -r '
  .[] |
  select(.translationProgress == 100 and .approvalProgress < 100) |
  "✓  \(.language.name): Ready for review (\(.approvalProgress)% approved)"
'

echo ""
```

### `/home/rasmus/Desktop/projects/cirkelline-system/scripts/validate-translations.js`

```javascript
#!/usr/bin/env node

/**
 * Validate translation files for:
 * - Valid JSON structure
 * - Placeholder consistency
 * - Missing translations
 * - RTL characters in Arabic
 */

const fs = require('fs');
const path = require('path');

const LOCALES_DIR = path.join(__dirname, '../locales');
const LANGUAGES = ['da', 'en', 'sv', 'de', 'ar'];

let errors = 0;
let warnings = 0;

console.log('Validating translation files...\n');

// Load English (source) for comparison
const enPath = path.join(LOCALES_DIR, 'en/messages.json');
const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));

function getAllKeys(obj, prefix = '') {
  let keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'object' && value !== null) {
      keys = keys.concat(getAllKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

function getPlaceholders(str) {
  const regex = /\{([^}]+)\}/g;
  const matches = [];
  let match;
  while ((match = regex.exec(str)) !== null) {
    matches.push(match[1]);
  }
  return matches;
}

function validateLanguage(lang) {
  console.log(`\n=== Validating ${lang} ===`);

  const filePath = path.join(LOCALES_DIR, `${lang}/messages.json`);

  // Check file exists
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filePath}`);
    errors++;
    return;
  }

  // Check valid JSON
  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    console.error(`❌ Invalid JSON: ${error.message}`);
    errors++;
    return;
  }

  // Get all keys
  const enKeys = getAllKeys(enData);
  const langKeys = getAllKeys(data);

  // Check for missing keys
  const missingKeys = enKeys.filter(k => !langKeys.includes(k));
  if (missingKeys.length > 0) {
    console.warn(`⚠️  Missing ${missingKeys.length} translations:`);
    missingKeys.slice(0, 5).forEach(k => console.warn(`   - ${k}`));
    if (missingKeys.length > 5) {
      console.warn(`   ... and ${missingKeys.length - 5} more`);
    }
    warnings += missingKeys.length;
  }

  // Check for extra keys (not in English)
  const extraKeys = langKeys.filter(k => !enKeys.includes(k));
  if (extraKeys.length > 0) {
    console.warn(`⚠️  Extra keys (not in English):`);
    extraKeys.forEach(k => console.warn(`   - ${k}`));
    warnings += extraKeys.length;
  }

  // Check placeholder consistency
  enKeys.forEach(key => {
    const enValue = key.split('.').reduce((obj, k) => obj?.[k], enData);
    const langValue = key.split('.').reduce((obj, k) => obj?.[k], data);

    if (!langValue) return; // Already reported as missing

    const enPlaceholders = getPlaceholders(enValue);
    const langPlaceholders = getPlaceholders(langValue);

    if (enPlaceholders.length !== langPlaceholders.length) {
      console.error(`❌ Placeholder mismatch in "${key}":`);
      console.error(`   EN:  ${enValue}`);
      console.error(`   ${lang.toUpperCase()}: ${langValue}`);
      errors++;
    } else {
      // Check placeholder names match (order can differ)
      const missing = enPlaceholders.filter(p => !langPlaceholders.includes(p));
      if (missing.length > 0) {
        console.error(`❌ Missing placeholders in "${key}": ${missing.join(', ')}`);
        errors++;
      }
    }
  });

  // Arabic-specific checks
  if (lang === 'ar') {
    console.log('\n--- Arabic-specific checks ---');

    // Check for RTL characters
    const hasRTL = Object.values(data).some(section =>
      Object.values(section).some(str => /[\u0600-\u06FF]/.test(str))
    );

    if (hasRTL) {
      console.log('✓ Contains Arabic characters');
    } else {
      console.warn('⚠️  No Arabic characters detected - possible machine translation?');
      warnings++;
    }

    // Check for bold/italic markers (should not be used)
    langKeys.forEach(key => {
      const value = key.split('.').reduce((obj, k) => obj?.[k], data);
      if (/<b>|<strong>|<i>|<em>|\*\*/.test(value)) {
        console.warn(`⚠️  Bold/italic formatting in Arabic "${key}" (not recommended)`);
        warnings++;
      }
    });
  }

  console.log(`\n${lang}: ${langKeys.length} translations`);
}

// Validate all languages
LANGUAGES.forEach(lang => {
  if (lang === 'en') {
    console.log('\n=== English (source) ===');
    console.log(`✓ ${getAllKeys(enData).length} source strings`);
  } else {
    validateLanguage(lang);
  }
});

// Summary
console.log('\n\n=== Validation Summary ===');
console.log(`Errors: ${errors}`);
console.log(`Warnings: ${warnings}`);

if (errors > 0) {
  console.error('\n❌ Validation failed!');
  process.exit(1);
} else if (warnings > 0) {
  console.warn('\n⚠️  Validation passed with warnings');
  process.exit(0);
} else {
  console.log('\n✓ All translations valid!');
  process.exit(0);
}
```

Make scripts executable:

```bash
chmod +x /home/rasmus/Desktop/projects/cirkelline-system/scripts/crowdin-stats.sh
chmod +x /home/rasmus/Desktop/projects/cirkelline-system/scripts/validate-translations.js
```

---

## Required Secrets

Add these to GitHub repository settings (Settings → Secrets and variables → Actions):

```yaml
CROWDIN_PROJECT_ID: "123456"  # Your Crowdin project ID (numeric)
CROWDIN_PERSONAL_TOKEN: "abc123..."  # Crowdin Personal Access Token

# For webhook authentication
GITHUB_PAT: "ghp_..."  # GitHub Personal Access Token with 'repo' scope
```

---

## Testing Checklist

### Initial Setup Testing

- [ ] Crowdin projects created (3 total)
- [ ] Languages configured (da, en, sv, de, ar)
- [ ] Shared TM created and assigned
- [ ] Glossary created
- [ ] `crowdin.yml` added to all repos
- [ ] GitHub secrets configured

### Upload Testing

- [ ] Manual upload: `crowdin upload sources`
- [ ] Verify files appear in Crowdin
- [ ] Check file structure preserved
- [ ] Test GitHub Action upload on push

### Download Testing

- [ ] Manual download: `crowdin download translations`
- [ ] Verify JSON structure valid
- [ ] Check placeholders intact
- [ ] Test scheduled download action

### QA Testing

- [ ] Translate test string with placeholder
- [ ] Verify QA check catches missing placeholder
- [ ] Test max length warning (German)
- [ ] Validate RTL display (Arabic)

### Webhook Testing

- [ ] Configure webhook in Crowdin
- [ ] Test with "Send Test Request"
- [ ] Verify GitHub Action triggered
- [ ] Check PR created successfully

### End-to-End Testing

- [ ] Update English source file
- [ ] Push to GitHub
- [ ] Verify Crowdin upload
- [ ] Translate in Crowdin (or use MT)
- [ ] Trigger download (manual or webhook)
- [ ] Review PR
- [ ] Merge PR
- [ ] Validate translations in app

---

## Troubleshooting

### Common Issues

**1. Crowdin CLI authentication fails**

```bash
# Verify API token
crowdin whoami

# If fails, re-authenticate
export CROWDIN_PERSONAL_TOKEN="your-token"
```

**2. GitHub Action fails with 401**

- Check `CROWDIN_PERSONAL_TOKEN` secret is set
- Verify token has project access
- Ensure `CROWDIN_PROJECT_ID` is correct (numeric)

**3. PR not created automatically**

- Check workflow permissions: `contents: write`, `pull-requests: write`
- Verify `GITHUB_TOKEN` has sufficient permissions
- Check GitHub Action logs for errors

**4. Placeholders broken in translation**

- Enable QA check: "Variables mismatch"
- Review translations with red highlights
- Fix in Crowdin Editor

**5. Arabic text displays LTR**

- Verify `dir="rtl"` in HTML
- Check CSS logical properties used
- Validate font supports Arabic

**6. Webhook not triggering**

- Check webhook logs in Crowdin (Settings → Webhooks → View Logs)
- Verify GitHub PAT valid and has `repo` scope
- Test with "Send Test Request" button
- Check for 4xx/5xx errors (auto-disabled after 100 failures)

---

## Resources

### Official Documentation

- [Crowdin Configuration File](https://support.crowdin.com/developer/configuration-file/)
- [GitHub Integration](https://support.crowdin.com/github-integration/)
- [GitHub Action](https://github.com/crowdin/github-action)
- [CI/CD Integration](https://crowdin.github.io/crowdin-cli/ci-cd)

### Translation Memory

- [Translation Memory Guide](https://crowdin.com/blog/2021/08/25/translation-memory)
- [TM Settings](https://support.crowdin.com/project-settings/translation-memories/)
- [Pre-Translation](https://support.crowdin.com/pre-translation-via-machine/)

### Quality Assurance

- [QA Checks Guide](https://crowdin.com/blog/qa-checks-article)
- [QA Check Settings](https://support.crowdin.com/project-settings/qa-checks/)
- [Custom QA Checks](https://support.crowdin.com/enterprise/custom-qa-checks/)

### Context & Screenshots

- [Screenshots Guide](https://crowdin.com/blog/2023/09/14/translation-context-screenshots-automation)
- [In-Context Localization](https://support.crowdin.com/in-context-localization/)
- [Screenshots API](https://support.crowdin.com/screenshots/)

### Terminology

- [Glossary Guide](https://crowdin.com/blog/2018/05/18/using-glossary-to-keep-translations-swift-and-consistent)
- [Glossary Settings](https://support.crowdin.com/project-settings/glossaries/)

### Webhooks

- [Webhooks Documentation](https://support.crowdin.com/webhooks/)
- [Webhook Events](https://support.crowdin.com/developer/webhooks/)

### RTL Languages

- [RTL Best Practices](https://www.argosmultilingual.com/blog/planning-for-rtl-languages-how-layout-content-and-qa-fit-together)
- [Hebrew UI Translation](https://www.tomedes.com/translator-hub/hebrew-ui-strings-translation)
- [RTL Website Design](https://www.reffine.com/en/blog/rtl-website-design-and-development-mistakes-best-practices)

### ICU MessageFormat

- [ICU Message Syntax](https://support.crowdin.com/icu-message-syntax/)
- [ICU Guide](https://crowdin.com/blog/2022/04/13/icu-guide)
- [ICU Helper App](https://store.crowdin.com/icu-helper)

### Branching

- [Version Management](https://support.crowdin.com/version-management/)
- [Development & Localization in Parallel](https://crowdin.com/blog/2020/12/08/development-and-localization-running-in-parallel-tips-for-developers)

---

## Next Steps

1. **Review this document** with the team
2. **Choose Crowdin plan** (Team, Business, or Enterprise)
3. **Schedule implementation** (4-week timeline recommended)
4. **Assign roles:**
   - Project manager: Oversees Crowdin projects
   - Developers: Implement CI/CD
   - Translators: da, sv, de, ar (or use professional services)
   - QA: Review translations before merge
5. **Start with Phase 1** (Foundation setup)

**Estimated effort:**
- Setup: 40 hours (1 week full-time)
- Training: 8 hours
- Ongoing: 2-4 hours/week for translation review

**Cost estimate (annual):**
- Crowdin Team plan: ~$500/year
- DeepL Pro: ~€30/year
- Professional translation (optional): ~€0.10/word × 500 words = €50 per language
- **Total: ~$600-800/year**

---

**Document prepared by:** Claude (Anthropic)
**Date:** 2025-12-09
**Version:** 1.0
**For:** Cirkelline System (Rasmus & Ivo)
