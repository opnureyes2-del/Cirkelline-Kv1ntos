# Framework Updates v1.3.5

**Date:** 2025-12-16
**Updated By:** Claude Code
**Total Packages Updated:** 20+ (Backend: 4, Frontend: 16+)

---

## Table of Contents

1. [Backend Updates](#backend-updates)
   - [AGNO 2.3.4 → 2.3.13](#1-agno-234--2313)
   - [FastAPI 0.118.0 → 0.124.4](#2-fastapi-01180--01244)
   - [Uvicorn 0.37.0 → 0.38.0](#3-uvicorn-0370--0380)
   - [Google-GenAI 1.52.0 → 1.55.0](#4-google-genai-1520--1550)
2. [Frontend Updates](#frontend-updates)
   - [TailwindCSS 3.4.17 → 4.1.18](#5-tailwindcss-3417--4118-major)
   - [TypeScript 5.7.3 → 5.9.3](#6-typescript-573--593)
   - [ESLint 9.19.0 → 9.39.2](#7-eslint-9190--9392)
   - [Other NPM Packages](#8-other-npm-packages)
3. [Summary](#summary)
4. [Testing Results](#testing-results)
5. [Sources](#sources)

---

## Backend Updates

### 1. AGNO 2.3.4 → 2.3.13

**9 versions of updates spanning December 3-15, 2025**

#### Version Changelog

##### v2.3.5 (December 3, 2025)

**New Features:**
- **Hooks as Background Tasks** - Enables non-blocking concurrent execution on AgentOS
- **OpenTelemetry-based native tracing** - Captures agent runs, model calls, and tool executions

**Bug Fixes:**
- RunEvent serialization issues with media-containing inputs
- DynamoDB Memory table missing GSI for created_at field
- Team metrics now correctly include duration and time-to-first-token
- AsyncPostgresDB signature mismatch in user memory deletion
- Duplicate WhatsApp image responses eliminated

---

##### v2.3.6 (December 3, 2025)

**New Features:**
- **Spotify toolkit** - For managing library content

**Improvements:**
- Faster accuracy evaluations via AgentOS with fresh sessions per iteration

**Bug Fixes:**
- Session state persistence in Workflows corrected
- Empty sessions now properly handled in AgentOS API endpoints

---

##### v2.3.7 (December 4, 2025)

**New Features:**
- **Amazon Redshift toolkit** - For database exploration and queries
- **RunRequirement class** - Streamlines human-in-the-loop workflows

**Improvements:**
- Yield run responses from continue_run methods when streaming
- Async databases now compatible with AgentOS evaluations
- Custom retrievers receive run_context access

**Bug Fixes:**
- AsyncPostgresDb automatic table creation bug resolved
- SQLite memory topics retrieval corrected

---

##### v2.3.8 (December 5, 2025)

**New Features:**
- **Model-level retry logic** - For provider rate-limit handling

**Improvements:**
- Context variables now propagate to parallel workflow step threads

**Bug Fixes:**
- Knowledge retriever run_context parameter passing fixed

**Removals:**
- **MemoriTools removed** - Deprecated in favor of `enable_user_memories=True` (which we already use)

---

##### v2.3.9 (December 9, 2025)

**New Features:**
- **AsyncMySQLDb support** - With asyncmy driver compatibility
- **AgentAsJudgeEval** - For LLM-based binary/numeric scoring against criteria
- **Agent/Team Introduction parameter** - For initial assistant messages
- **OpenRouter reasoning message support**

**Improvements:**
- Database schema auto-creation now optional via `create_schema=False`
- Nested step output retrieval in Parallel groups
- **Gemini malformed tool call detection and retry**
- DeepSeek thinking mode with tool support
- `run_id` parameter for explicit run identification
- Pure synchronous knowledge methods implementation

**Bug Fixes:**
- Parallel workflow step content aggregation
- Pre-hook triggering unnecessary retries

---

##### v2.3.10 (December 10, 2025)

**New Features:**
- **Shopify toolkit** - For store analytics and insights

**Improvements:**
- Gemini URL context streaming support

**Bug Fixes:**
- Streaming agent evaluation crashes eliminated
- Session state consistency in generator function tools
- AsyncSqlite automatic table creation when upserting knowledge

---

##### v2.3.11 (December 11, 2025)

**Improvements:**
- Custom knowledge reader display improvements in AgentOS
- Reader/chunking handling enhancements for AgentOS uploads
- Trace upsert functionality refinement across databases
- **OpenAI response_provider_data fields** added to RunOutput and RunCompletedEvent

**Bug Fixes:**
- Culture feature compatibility with AsyncPostgresDb and AsyncSqliteDb

---

##### v2.3.12 (December 12, 2025)

**New Features:**
- **Token count-based compression support** - Across all providers

**Improvements:**
- Content hashing now includes name/description fields ensuring uniqueness across sources

**Bug Fixes:**
- Session storage in HITL flows with proper RunRequirement JSON serialization
- Gemini malformed tool call retry logic with configurable retry limits
- CSV reader corrected

---

##### v2.3.13 (December 15, 2025)

**New Features:**
- **AgentOS Role-Based Access Control (RBAC)** - With JWT-based authorization
- **Per-endpoint authorization** - Based on JWT token scopes
- **Per-agent resource control** - Limiting user access to specific agents/teams/workflows
- **Asymmetric key support** - RS256 default in JWTMiddleware

**Bug Fixes:**
- Reranker assignment for Redis
- Citation search queries corrected

**Breaking Changes:**
- `JWTMiddleware secret_key` deprecated (though still supported)
- Algorithm default changed from HS256 to RS256

#### Impact on Cirkelline

| Feature | Impact | Notes |
|---------|--------|-------|
| Parallel Memory Updates | ✅ Positive | Speed improvement for memory system |
| Gemini malformed tool retry | ✅ Positive | Better error handling |
| Token compression | ✅ Positive | Potential cost savings |
| JWTMiddleware RS256 default | ⚪ None | We use our own JWT implementation |
| MemoriTools removed | ⚪ None | We don't use this feature |
| RBAC features | ⚪ None | We use custom auth |

---

### 2. FastAPI 0.118.0 → 0.124.4

**6+ versions of updates**

#### Changes

| Type | Description |
|------|-------------|
| **Feature** | Improved tracebacks with endpoint metadata |
| **Bug Fix** | Parameter alias handling corrections |
| **Bug Fix** | Tagged union with discriminator support inside `Annotated` with `Body()` |
| **Bug Fix** | String annotation evaluation for `if TYPE_CHECKING` blocks |
| **Bug Fix** | Arbitrary types handling with `arbitrary_types_allowed=True` |
| **Bug Fix** | Class dependency resolution with `__call__` methods |
| **Bug Fix** | `separate_input_output_schemas=False` with computed fields |
| **Bug Fix** | OAuth2 scopes in OpenAPI edge cases |
| **Bug Fix** | Function wrapping with `functools.wraps` and `partial` |
| **Bug Fix** | Python 3.10 stringified annotation evaluation |

#### Impact on Cirkelline

- ✅ All bug fixes with no breaking changes
- ✅ Better error tracebacks for debugging production issues
- ✅ Improved type annotation handling

---

### 3. Uvicorn 0.37.0 → 0.38.0

#### Changes

| Type | Description |
|------|-------------|
| **Feature** | Python 3.14 support added |

#### Impact on Cirkelline

- ✅ Future-proofing for Python 3.14
- ✅ No breaking changes
- ✅ Maintenance update only

---

### 4. Google-GenAI 1.52.0 → 1.55.0

**4 versions of updates**

#### Version Changelog

##### v1.52.0

**Bug Fixes:**
- `TypeError: issubclass() arg 1 must be a class` when using `List[str]`
- New aiohttp Client Session created if loop is closed

---

##### v1.53.0

**New Features:**
- Empty response for `tunings.cancel()`

**Bug Fixes:**
- Citation metadata key conversion from 'citationSources' to 'citations'
- `google.auth.transport.requests` import error in Live API resolved

---

##### v1.54.0

**Bug Fixes:**
- Timeout applied to total request duration in aiohttp
- APIError class made picklable

---

##### v1.55.0

**New Features:**
- **Interactions API** added
- **enableEnhancedCivicAnswers** feature in GenerateContentConfig
- New enum values for finish reasons: `IMAGE_RECITATION` and `IMAGE_OTHER`
- Voice activity detection signal support

**Bug Fixes:**
- Voice config bytes handling improvements

#### Impact on Cirkelline

- ✅ Better timeout handling for API calls
- ✅ Improved error handling with picklable APIError
- ✅ Citation metadata fixes (important for Research Team)
- ✅ No breaking changes

---

## Frontend Updates

### 5. TailwindCSS 3.4.17 → 4.1.18 (MAJOR)

**This is the most significant update - TailwindCSS v4 is a complete rewrite.**

#### Performance Improvements

| Metric | v3 | v4 | Improvement |
|--------|----|----|-------------|
| Full builds | 378ms | 100ms | **3.78x faster** |
| Incremental (new CSS) | 44ms | 5ms | **8.8x faster** |
| Incremental (no new CSS) | 35ms | 192µs | **182x faster** |

#### Major Changes

##### Configuration Migration

**Before (v3) - tailwind.config.js:**
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: '#3490dc',
      },
      fontFamily: {
        display: ['Satoshi', 'sans-serif'],
      },
    },
  },
}
```

**After (v4) - CSS @theme block:**
```css
@import "tailwindcss";

@theme {
  --font-display: "Satoshi", "sans-serif";
  --color-brand: #3490dc;
  --breakpoint-3xl: 1920px;
}
```

##### Import Changes

**Before (v3):**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**After (v4):**
```css
@import "tailwindcss";
```

#### New Features in v4

| Feature | Description |
|---------|-------------|
| **Native cascade layers** | Better style control and specificity management |
| **Registered custom properties** | Using `@property` for type-safe CSS variables |
| **`color-mix()`** | Native opacity adjustments |
| **Logical properties** | Built-in RTL support |
| **Design tokens as CSS variables** | All theme values automatically exposed as `--var` |
| **Dynamic utility values** | `grid-cols-15`, `mt-17` work without config |
| **3D transforms** | `rotate-x-*`, `rotate-y-*`, `perspective-*` |
| **Gradient improvements** | `bg-linear-45`, `bg-conic-*`, `bg-radial-*` |
| **Container queries** | Built-in (no plugin needed) |
| **`@starting-style`** | Enter/exit animations without JavaScript |
| **`not-*` variant** | Negate conditions with `:not()` |
| **P3 color palette** | OKLCH colors for more vivid display |

#### Breaking Changes

| Change | Migration Required |
|--------|-------------------|
| Installation method | Use `@import "tailwindcss"` |
| Configuration format | Move from JS to CSS `@theme` |
| Color format | RGB → OKLCH (slight visual differences) |
| Package structure | New `@tailwindcss/postcss` and `@tailwindcss/vite` |

#### Impact on Cirkelline

- ✅ Build succeeded with no errors
- ✅ All 26 routes compiled successfully
- ✅ Standard Tailwind classes work as expected
- ⚠️ Colors may appear slightly more vivid (OKLCH vs RGB)

---

### 6. TypeScript 5.7.3 → 5.9.3

#### TypeScript 5.8 Features

##### Granular Checks for Return Expressions

TypeScript now checks each branch of conditional expressions in return statements:

```typescript
declare const cache: Map<string, URL>;

function getUrlObject(urlString: string): URL {
    return cache.has(urlString) ?
        cache.get(urlString) :
        urlString;  // ❌ Error! Type 'string' is not assignable to type 'URL'
}
```

##### `require()` of ECMAScript Modules

Node.js 22+ allows `require()` calls to ESM files. TypeScript 5.8 supports this with `--module nodenext`.

##### New Compiler Flags

| Flag | Description |
|------|-------------|
| `--module node18` | Stable reference for Node.js 18 |
| `--erasableSyntaxOnly` | Restricts TypeScript constructs with runtime behavior |
| `--libReplacement` | Disables automatic `@typescript/lib-*` lookup |

##### Import Assertions Deprecation

```typescript
// ❌ Deprecated
import data from "./data.json" assert { type: "json" };

// ✅ Preferred
import data from "./data.json" with { type: "json" };
```

#### TypeScript 5.9 Features

- Performance optimizations
- Declaration file improvements
- Better path normalization (avoids array allocations)

#### Impact on Cirkelline

- ✅ Better type checking (may catch more bugs at compile time)
- ✅ No breaking changes for our codebase
- ✅ Improved build performance

---

### 7. ESLint 9.19.0 → 9.39.2

**ESLint 9 was a major rewrite introducing "flat config" as default.**

#### Major Changes

| Change | Description |
|--------|-------------|
| **Flat Config Default** | `eslint.config.js` replaces `.eslintrc` |
| **Node.js 18+ Required** | Dropped support for Node < 18.18.0 |
| **Removed Rules** | `require-jsdoc`, `valid-jsdoc` removed |
| **--quiet Behavior** | Now prevents warn rules from running entirely |
| **eslint-env Removed** | Comments no longer supported |

#### Flat Config vs eslintrc

**Before (.eslintrc.json):**
```json
{
  "extends": ["next/core-web-vitals"],
  "rules": {
    "no-console": "warn"
  }
}
```

**After (eslint.config.js):**
```javascript
import nextConfig from "eslint-config-next";

export default [
  ...nextConfig,
  {
    rules: {
      "no-console": "warn"
    }
  }
];
```

#### Impact on Cirkelline

- ✅ Using `eslint-config-next` which handles migration
- ✅ Build succeeded with no config changes needed
- ✅ May need migration if customizing rules later

---

### 8. Other NPM Packages

#### Updated Packages

| Package | Old Version | New Version | Type | Description |
|---------|-------------|-------------|------|-------------|
| framer-motion | 12.4.1 | 12.23.26 | Patch | Animation library improvements |
| zustand | 5.0.3 | 5.0.9 | Patch | State management bug fixes |
| nuqs | 2.3.2 | 2.8.5 | Minor | URL state management improvements |
| @radix-ui/react-dialog | 1.1.5 | 1.1.15 | Patch | Accessibility fixes |
| @radix-ui/react-select | 2.1.5 | 2.2.6 | Minor | New features, accessibility |
| @radix-ui/react-label | 2.1.7 | 2.1.8 | Patch | Bug fixes |
| @radix-ui/react-slot | 1.1.1 | 1.2.4 | Minor | Improvements |
| @radix-ui/react-tooltip | 1.1.7 | 1.2.8 | Minor | Improvements |
| prettier | 3.4.2 | 3.7.4 | Minor | Formatting improvements |
| postcss | 8.5.1 | 8.5.6 | Patch | Bug fixes |
| @types/node | 20.17.16 | 25.0.2 | Major | Node.js type definitions |
| @types/react | 19.0.8 | 19.2.7 | Minor | React type improvements |
| @types/react-dom | 19.0.3 | 19.2.3 | Minor | ReactDOM type improvements |
| @types/pg | 8.15.5 | 8.16.0 | Minor | PostgreSQL type improvements |
| @eslint/eslintrc | 3.2.0 | 3.3.3 | Patch | ESLint config improvements |
| eslint-config-next | 15.2.3 | 16.0.10 | Major | Next.js ESLint config |

#### Impact on Cirkelline

- ✅ All UI components work correctly
- ✅ State management (zustand) unchanged
- ✅ Animations (framer-motion) improved
- ✅ Accessibility improvements from Radix updates

---

## Summary

### What Was Updated

| Category | Packages | Risk Level | Status |
|----------|----------|------------|--------|
| Backend Core | agno, fastapi, uvicorn, google-genai | ✅ LOW | Tested OK |
| Frontend Build | TailwindCSS v4, TypeScript 5.9, ESLint 9.x | ⚠️ MEDIUM | Tested OK |
| Frontend UI | Radix, framer-motion, zustand, nuqs | ✅ LOW | Tested OK |
| Type Definitions | @types/node, @types/react, @types/pg | ✅ LOW | Tested OK |

### Key Improvements

1. **Performance**
   - TailwindCSS builds 3.78x faster
   - AGNO parallel memory updates
   - TypeScript build optimizations

2. **Reliability**
   - AGNO Gemini malformed tool retry
   - FastAPI improved error tracebacks
   - Google-GenAI better timeout handling

3. **Features**
   - AGNO token compression support
   - TailwindCSS container queries (built-in)
   - TailwindCSS 3D transforms
   - TypeScript better type checking

### Potential Issues to Watch

| Issue | Description | Mitigation |
|-------|-------------|------------|
| TailwindCSS colors | OKLCH may appear slightly different | Visual QA on production |
| AGNO JWT changes | RS256 default | We use custom JWT, no impact |
| ESLint flat config | May need migration for custom rules | Currently using next config |

---

## Testing Results

### Backend Tests

| Test | Result |
|------|--------|
| Backend startup | ✅ PASS |
| Health endpoint | ✅ PASS |
| Chat functionality | ✅ PASS |
| Research Team (Exa/DuckDuckGo) | ✅ PASS |
| AGNO 2.3.13 compatibility | ✅ PASS |

### Frontend Tests

| Test | Result |
|------|--------|
| pnpm build | ✅ PASS |
| TypeScript compilation | ✅ PASS |
| All 26 routes generated | ✅ PASS |
| TailwindCSS v4 compatibility | ✅ PASS |

---

## Sources

- [AGNO GitHub Releases](https://github.com/agno-agi/agno/releases)
- [FastAPI GitHub Releases](https://github.com/fastapi/fastapi/releases)
- [Uvicorn GitHub Releases](https://github.com/encode/uvicorn/releases)
- [Google GenAI GitHub Releases](https://github.com/googleapis/python-genai/releases)
- [TailwindCSS v4.0 Blog Post](https://tailwindcss.com/blog/tailwindcss-v4)
- [TypeScript 5.8 Release Notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html)
- [ESLint v9 Migration Guide](https://eslint.org/docs/latest/use/migrate-to-9.0.0)
- [ESLint Configuration Migration Guide](https://eslint.org/docs/latest/use/configure/migration-guide)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.3.5 | 2025-12-16 | Framework updates (this document) |
| v1.3.4 | 2025-12-16 | Production error fixes, admin stats timestamp fix |
| v1.3.3 | 2025-12-14 | Memory timestamp fix |
| v1.3.2 | 2025-12-12 | Daily Journal Workflow |
