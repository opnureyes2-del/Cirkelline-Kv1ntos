# FASE 2: INTERNATIONALISERING (i18n/l10n) - DETALJERET HANDLINGSPLAN

**Version:** 1.0.0
**Dato:** 2025-12-09
**Status:** IMPLEMENTERING PÅBEGYNDT

---

## EXECUTIVE SUMMARY

Denne handlingsplan beskriver den komplette implementering af internationalisering (i18n) og lokalisering (l10n) for hele Cirkelline-økosystemet. Baseret på omfattende analyse og Deep Research.

### Analysefund
- **~800-1200 hardcodede strenge** identificeret på tværs af 75+ filer
- **4 hovedprojekter** skal internationaliseres:
  - Cirkelline System (Backend + Frontend)
  - CKC (Cirkelline Knowledge Center)
  - Cosmic Library
  - lib-admin (Admin Panel)
  - CLA (Cirkelline Local Agent - Tauri)

### Målsprog
| Kode | Sprog | Prioritet | RTL |
|------|-------|-----------|-----|
| `da` | Dansk | P1 (Standard) | Nej |
| `en` | Engelsk | P1 | Nej |
| `sv` | Svensk | P2 | Nej |
| `de` | Tysk | P2 | Nej |
| `ar` | Arabisk | P3 | **JA** |

---

## DEL 1: VALGTE TEKNOLOGIER

### 1.1 Backend (FastAPI/Python)
```
Framework: fastapi-babel + python-babel
Filformat: GNU Gettext (.po/.mo)
```

### 1.2 Frontend (Next.js/React)
```
Framework: next-intl v3+
Filformat: JSON (da.json, en.json, etc.)
Routing: Middleware-baseret locale detection
```

### 1.3 Desktop (Tauri/Rust)
```
Backend: rust-i18n
Frontend: react-i18next
Filformat: YAML (Rust) + JSON (React)
```

### 1.4 Database
```sql
-- Oversættelsestabel for dynamisk indhold
CREATE TABLE ai.translations (
    id SERIAL PRIMARY KEY,
    content_key TEXT NOT NULL,
    locale VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    context TEXT,
    category VARCHAR(50), -- 'ui', 'error', 'notification', 'email'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(content_key, locale, context)
);

CREATE INDEX idx_translations_locale ON ai.translations(locale);
CREATE INDEX idx_translations_key ON ai.translations(content_key);

-- Bruger-præference for sprog
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS preferred_locale VARCHAR(10) DEFAULT 'da';
```

### 1.5 Oversættelsesplatform
```
Platform: Crowdin Enterprise
Integration: GitHub Actions
Sync: Automatisk pull/push ved commits
```

---

## DEL 2: MAPPESTRUKTUR

### 2.1 Cirkelline System (Backend)
```
cirkelline-system/
├── locales/
│   ├── da/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po
│   │       └── messages.mo
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po
│   │       └── messages.mo
│   ├── sv/
│   │   └── LC_MESSAGES/
│   │       └── ...
│   ├── de/
│   │   └── LC_MESSAGES/
│   │       └── ...
│   └── ar/
│       └── LC_MESSAGES/
│           └── ...
├── babel.cfg
└── cirkelline/
    └── i18n/
        ├── __init__.py
        ├── setup.py
        └── utils.py
```

### 2.2 Cirkelline UI (Frontend)
```
cirkelline-ui/
├── messages/
│   ├── da.json
│   ├── en.json
│   ├── sv.json
│   ├── de.json
│   └── ar.json
├── src/
│   └── i18n/
│       ├── request.ts
│       ├── config.ts
│       └── navigation.ts
└── middleware.ts (locale detection)
```

### 2.3 CKC Backend
```
ckc/backend/
├── locales/
│   ├── da/LC_MESSAGES/
│   ├── en/LC_MESSAGES/
│   └── ...
└── api/
    └── i18n/
        └── __init__.py
```

### 2.4 Cosmic Library
```
Cosmic-Library-main/
├── backend/
│   └── locales/
│       ├── da/LC_MESSAGES/
│       ├── en/LC_MESSAGES/
│       └── ...
└── frontend/
    └── messages/
        ├── da.json
        ├── en.json
        └── ...
```

### 2.5 CLA (Tauri Desktop)
```
cla/
├── src-tauri/
│   └── locales/
│       ├── da.yml
│       ├── en.yml
│       └── ...
└── src/
    └── locales/
        ├── da.json
        ├── en.json
        └── ...
```

---

## DEL 3: IMPLEMENTERINGS TRIN

### FASE 2.1: Foundation Setup (I GANG)

#### Trin 2.1.1: Database Migration
```sql
-- Kør på alle databaser
CREATE TABLE IF NOT EXISTS ai.translations (
    id SERIAL PRIMARY KEY,
    content_key TEXT NOT NULL,
    locale VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    context TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(content_key, locale, context)
);

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS preferred_locale VARCHAR(10) DEFAULT 'da';
```

#### Trin 2.1.2: Backend i18n Setup (FastAPI)
```python
# cirkelline/i18n/__init__.py
from babel import Locale
from babel.support import Translations
from fastapi import Request
from functools import lru_cache

SUPPORTED_LOCALES = ['da', 'en', 'sv', 'de', 'ar']
DEFAULT_LOCALE = 'da'
RTL_LOCALES = ['ar']

@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def get_translations(locale: str) -> Translations:
    return Translations.load('locales', [locale])

def get_locale(request: Request) -> str:
    # Priority: query > cookie > user profile > Accept-Language > default
    if locale := request.query_params.get('locale'):
        if locale in SUPPORTED_LOCALES:
            return locale

    if locale := request.cookies.get('preferred_locale'):
        if locale in SUPPORTED_LOCALES:
            return locale

    if hasattr(request.state, 'user'):
        if locale := getattr(request.state.user, 'preferred_locale', None):
            if locale in SUPPORTED_LOCALES:
                return locale

    accept_language = request.headers.get('Accept-Language', '')
    for lang in accept_language.split(','):
        locale = lang.split(';')[0].strip()[:2]
        if locale in SUPPORTED_LOCALES:
            return locale

    return DEFAULT_LOCALE

def _(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    """Translate a string."""
    translations = get_translations(locale)
    return translations.gettext(key).format(**kwargs) if kwargs else translations.gettext(key)
```

#### Trin 2.1.3: Frontend i18n Setup (next-intl)
```typescript
// src/i18n/config.ts
export const locales = ['da', 'en', 'sv', 'de', 'ar'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'da';
export const rtlLocales: Locale[] = ['ar'];

// src/i18n/request.ts
import { getRequestConfig } from 'next-intl/server';
import { cookies, headers } from 'next/headers';

export default getRequestConfig(async () => {
  const cookieStore = cookies();
  const headerStore = headers();

  // Priority: cookie > Accept-Language > default
  let locale = cookieStore.get('NEXT_LOCALE')?.value;

  if (!locale) {
    const acceptLanguage = headerStore.get('Accept-Language') || '';
    locale = acceptLanguage.split(',')[0].split('-')[0];
  }

  if (!locales.includes(locale as Locale)) {
    locale = defaultLocale;
  }

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default
  };
});
```

#### Trin 2.1.4: Middleware for Next.js
```typescript
// middleware.ts
import createMiddleware from 'next-intl/middleware';
import { locales, defaultLocale } from './src/i18n/config';

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'as-needed'
});

export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)']
};
```

### FASE 2.2: String Extraction

#### Trin 2.2.1: Backend String Extraction
```bash
# Extract strings from Python files
pybabel extract -F babel.cfg -o locales/messages.pot .

# Initialize locale catalogs
pybabel init -i locales/messages.pot -d locales -l da
pybabel init -i locales/messages.pot -d locales -l en
pybabel init -i locales/messages.pot -d locales -l sv
pybabel init -i locales/messages.pot -d locales -l de
pybabel init -i locales/messages.pot -d locales -l ar
```

#### Trin 2.2.2: Frontend JSON Structure
```json
// messages/da.json
{
  "common": {
    "loading": "Indlæser...",
    "error": "Der opstod en fejl",
    "success": "Handling gennemført",
    "cancel": "Annuller",
    "save": "Gem",
    "delete": "Slet",
    "edit": "Rediger"
  },
  "auth": {
    "login": "Log ind",
    "logout": "Log ud",
    "email": "E-mail",
    "password": "Adgangskode",
    "forgotPassword": "Glemt adgangskode?",
    "createAccount": "Opret konto"
  },
  "errors": {
    "unauthorized": "Du har ikke adgang til denne ressource",
    "notFound": "Siden blev ikke fundet",
    "serverError": "Serverfejl. Prøv igen senere.",
    "validation": {
      "required": "{field} er påkrævet",
      "email": "Ugyldig e-mailadresse",
      "minLength": "{field} skal være mindst {min} tegn"
    }
  },
  "navigation": {
    "home": "Hjem",
    "dashboard": "Dashboard",
    "settings": "Indstillinger",
    "profile": "Profil"
  }
}
```

```json
// messages/en.json
{
  "common": {
    "loading": "Loading...",
    "error": "An error occurred",
    "success": "Action completed",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit"
  },
  "auth": {
    "login": "Log in",
    "logout": "Log out",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot password?",
    "createAccount": "Create account"
  },
  "errors": {
    "unauthorized": "You do not have access to this resource",
    "notFound": "Page not found",
    "serverError": "Server error. Please try again later.",
    "validation": {
      "required": "{field} is required",
      "email": "Invalid email address",
      "minLength": "{field} must be at least {min} characters"
    }
  },
  "navigation": {
    "home": "Home",
    "dashboard": "Dashboard",
    "settings": "Settings",
    "profile": "Profile"
  }
}
```

### FASE 2.3: API Integration

#### HTTPException med i18n
```python
# cirkelline/i18n/exceptions.py
from fastapi import HTTPException, Request
from .utils import _, get_locale

def i18n_http_exception(
    request: Request,
    status_code: int,
    message_key: str,
    **kwargs
) -> HTTPException:
    locale = get_locale(request)
    translated_message = _(message_key, locale, **kwargs)
    return HTTPException(status_code=status_code, detail=translated_message)

# Brug:
# raise i18n_http_exception(request, 401, "errors.unauthorized")
```

#### API Response Headers
```python
# Middleware for locale headers
@app.middleware("http")
async def add_locale_header(request: Request, call_next):
    response = await call_next(request)
    locale = get_locale(request)
    response.headers["Content-Language"] = locale
    response.headers["X-Locale"] = locale
    return response
```

### FASE 2.4: RTL Support

#### CSS Logical Properties
```css
/* global.css */
[dir="rtl"] {
  /* Use logical properties */
  text-align: start; /* instead of left */
}

.card {
  margin-inline-start: 1rem; /* instead of margin-left */
  padding-inline-end: 1rem;  /* instead of padding-right */
}

/* RTL-specific overrides */
[dir="rtl"] .icon-arrow {
  transform: scaleX(-1);
}
```

#### React Component
```tsx
// components/LocaleProvider.tsx
'use client';
import { useLocale } from 'next-intl';
import { rtlLocales } from '@/i18n/config';

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useLocale();
  const dir = rtlLocales.includes(locale) ? 'rtl' : 'ltr';

  return (
    <html lang={locale} dir={dir}>
      {children}
    </html>
  );
}
```

### FASE 2.5: Date/Time/Currency Formatting

#### Intl API Usage
```typescript
// utils/formatters.ts
import { useLocale } from 'next-intl';

export function useFormatters() {
  const locale = useLocale();

  const formatDate = (date: Date, options?: Intl.DateTimeFormatOptions) => {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'medium',
      ...options
    }).format(date);
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat(locale, {
      timeStyle: 'short'
    }).format(date);
  };

  const formatCurrency = (amount: number, currency = 'DKK') => {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat(locale).format(num);
  };

  return { formatDate, formatTime, formatCurrency, formatNumber };
}
```

---

## DEL 4: CI/CD INTEGRATION

### GitHub Actions Workflow
```yaml
# .github/workflows/i18n-sync.yml
name: i18n Sync

on:
  push:
    paths:
      - 'locales/**'
      - 'messages/**'
  pull_request:
    paths:
      - 'locales/**'
      - 'messages/**'

jobs:
  crowdin-upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Upload to Crowdin
        uses: crowdin/github-action@v1
        with:
          upload_sources: true
          upload_translations: false
          crowdin_branch_name: ${{ github.ref_name }}
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}

  crowdin-download:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Download from Crowdin
        uses: crowdin/github-action@v1
        with:
          download_translations: true
          push_translations: true
          commit_message: 'chore(i18n): sync translations from Crowdin'
        env:
          CROWDIN_PROJECT_ID: ${{ secrets.CROWDIN_PROJECT_ID }}
          CROWDIN_PERSONAL_TOKEN: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
```

### Pre-commit Hook for i18n
```yaml
# .pre-commit-config.yaml (tilføj)
  - repo: local
    hooks:
      - id: check-i18n-keys
        name: Check i18n key consistency
        entry: python scripts/check_i18n_keys.py
        language: python
        files: \.(json|po)$
```

---

## DEL 5: TEST STRATEGI

### Unit Tests
```python
# tests/test_i18n.py
import pytest
from cirkelline.i18n import _, get_locale, SUPPORTED_LOCALES

def test_all_locales_have_translations():
    test_keys = ['common.loading', 'errors.unauthorized', 'auth.login']
    for locale in SUPPORTED_LOCALES:
        for key in test_keys:
            translated = _(key, locale)
            assert translated != key, f"Missing translation for {key} in {locale}"

def test_locale_detection_priority():
    # Test query param takes priority
    # Test cookie fallback
    # Test Accept-Language fallback
    # Test default locale
    pass

def test_rtl_locale_detection():
    assert get_dir('ar') == 'rtl'
    assert get_dir('da') == 'ltr'
    assert get_dir('en') == 'ltr'
```

### Integration Tests
```typescript
// __tests__/i18n.test.tsx
import { render, screen } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';

describe('i18n Integration', () => {
  it('renders Danish translations by default', () => {
    render(
      <NextIntlClientProvider locale="da" messages={daMessages}>
        <LoginForm />
      </NextIntlClientProvider>
    );
    expect(screen.getByText('Log ind')).toBeInTheDocument();
  });

  it('renders English translations when locale is en', () => {
    render(
      <NextIntlClientProvider locale="en" messages={enMessages}>
        <LoginForm />
      </NextIntlClientProvider>
    );
    expect(screen.getByText('Log in')).toBeInTheDocument();
  });
});
```

---

## DEL 6: VERIFIKATIONS CHECKLISTE

### Per Projekt
- [ ] i18n framework installeret og konfigureret
- [ ] Locale mappestruktur oprettet
- [ ] Alle hardcodede strenge identificeret
- [ ] Strenge ekstraheret til oversættelsesfiler
- [ ] Basis oversættelser (da/en) komplet
- [ ] RTL support implementeret (ar)
- [ ] Date/time/currency formattering testet
- [ ] Unit tests bestået
- [ ] Integration tests bestået

### Cross-Project
- [ ] Database migration kørt på alle databaser
- [ ] API locale detection konsistent
- [ ] SSO videresender locale præference
- [ ] Crowdin integration konfigureret
- [ ] CI/CD workflow aktiv
- [ ] Pre-commit hooks installeret

---

## DEL 7: ESTIMERET KOMPLEKSITET

| Komponent | Filer | Strenge | Kompleksitet |
|-----------|-------|---------|--------------|
| Cirkelline Backend | 15 | 150 | Medium |
| Cirkelline UI | 30 | 200 | Medium |
| CKC Backend | 20 | 180 | Medium |
| Cosmic Library | 25 | 200 | Medium |
| lib-admin | 31 | 150 | Low |
| CLA (Tauri) | 15 | 120 | High |
| **Total** | **136** | **~1000** | **Medium-High** |

---

## NÆSTE SKRIDT (IMPLEMENTATION)

1. **DEL 2.1.1** - Opret database migration for `ai.translations`
2. **DEL 2.1.2** - Implementer backend i18n modul for Cirkelline System
3. **DEL 2.1.3** - Implementer frontend i18n med next-intl
4. **DEL 2.1.4** - Opret initial locale filer (da.json, en.json)
5. **DEL 2.2** - Påbegynd systematisk string extraction

---

**Dokument Revision:** 1.0.0
**Sidst Opdateret:** 2025-12-09
**Ansvarlig:** Claude Code (FASE 2 Implementation)
