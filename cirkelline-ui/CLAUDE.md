# KV1NTOS FRONTEND BRIEFING — Session 90, Terminal 3

> DU ER TILDELT KV1NTOS FRONTEND. Backend kører på port 7777 (ok, 212 endpoints).
> Frontend er IKKE startet endnu. Next.js projekt med 25 sider. Port 3000.

## DIN OPGAVE

Start KV1NTOS frontend og gør det FUNKTIONELT. Dette er KUNDEPLATFORMEN — det Rasmus' kunder ser.

## REGLER (UFRAVIGELIGE)

1. **BRUGER-FØRST**: Hvad kan en KUNDE gøre? Chat, profil, dokumenter, kalender
2. **MOBIL-FØRST**: Rasmus bruger Pixel. Kunder bruger telefoner. Alt SKAL virke på mobil
3. **INGEN MONITORING-DASHBOARDS**: Kunder vil HANDLE, ikke se JSON
4. **CONNECT TIL BACKEND**: Backend er på `http://localhost:7777` — brug RIGTIGE endpoints
5. **Auth kræves**: Backend returnerer 401 uden auth header

## BACKEND ENDPOINTS (localhost:7777) — 212 total

**Kunde-facing:**
- `POST /api/auth/login` — Login
- `POST /api/auth/signup` — Opret konto
- `POST /api/terminal/ask` — CHAT med AI (KERNE-FEATURE)
- `GET /api/terminal/status` — Terminal status
- `GET /api/terminal/features` — Tilgængelige features

**Profil & Bruger:**
- `GET /api/user/profile` — Bruger profil
- `PATCH /api/user/profile` — Opdater profil
- `GET /api/user/preferences` — Præferencer
- `PATCH /api/user/preferences` — Opdater præferencer
- `GET /api/user/memories` — Bruger-minder
- `GET /api/user/statistics` — Statistik
- `GET /api/user/subscription` — Abonnement

**Kalender & Tasks (Google integration):**
- `GET /api/calendar/events` — Kalender events
- `POST /api/calendar/events` — Opret event
- `GET /api/google/emails` — Emails
- `POST /api/google/emails/send` — Send email
- `GET /api/google/tasks/lists` — Task lister
- `GET /api/oauth/google/start` — Start Google OAuth

**CKC & Knowledge:**
- `GET /api/ckc/overview` — CKC oversigt
- `GET /api/ckc/rooms` — Rooms
- `GET /api/ckc/agents` — CKC agenter
- `GET /api/ckc/models` — Tilgængelige modeller
- `POST /api/ckc/models/switch` — Skift model
- `GET /api/knowledge/documents` — Videnbase dokumenter
- `POST /api/knowledge/upload` — Upload viden

**Admin:**
- `GET /api/admin/users` — Brugerliste
- `GET /api/admin/stats` — Admin statistik
- `GET /api/admin/workflows` — Workflows
- `POST /api/admin/workflows/{name}/run` — Kør workflow

**Sessions & Documents:**
- `GET /sessions` — Sessioner
- `POST /sessions` — Ny session
- `GET /api/documents` — Dokumenter
- `GET /api/feedback` — Feedback
- `POST /api/feedback` — Send feedback

## EKSISTERENDE SIDER (25 pages)

```
Kunde-facing:
  src/app/page.tsx            — Landing/dashboard
  src/app/chat/page.tsx       — CHAT MED AI (vigtigst!)
  src/app/login/page.tsx      — Login
  src/app/signup/page.tsx     — Opret konto

Profil:
  src/app/profile/page.tsx         — Profil oversigt
  src/app/profile/activity/        — Aktivitet
  src/app/profile/documents/       — Dokumenter
  src/app/profile/journals/        — Journaler
  src/app/profile/security/        — Sikkerhed
  src/app/profile/integrations/    — Integrationer (Google)
  src/app/profile/preferences/     — Præferencer
  src/app/profile/sessions/        — Sessioner
  src/app/profile/memories/        — Minder

Admin:
  src/app/admin/page.tsx           — Admin dashboard
  src/app/admin/activity/          — Aktivitetslog
  src/app/admin/fleet/             — Fleet management
  src/app/admin/ckc/               — CKC management
  src/app/admin/metrics/           — Metrics
  src/app/admin/users/             — Brugere
  src/app/admin/feedback/          — Feedback
  src/app/admin/workflows/         — Workflows
  src/app/admin/workflows/memory/  — Memory workflows
  src/app/admin/workflows/journals/— Journal workflows
  src/app/admin/subscriptions/     — Abonnementer
```

## PRIORITERET RÆKKEFØLGE

1. **Frontend KØRER ALLEREDE** på port 3000 (systemd service, aktiv siden Mar 24). SKIP start.
2. **Chat** (chat/page.tsx) — KERNE. Skriv besked → få AI-svar via /api/terminal/ask
3. **Login/Signup** — Auth flow mod backend
4. **Dashboard** (page.tsx) — Brugerens overblik: sessioner, minder, dokumenter
5. **Profil** — Præferencer + integrationer (Google OAuth)
6. **Admin** — Workflows + brugerstyring

## KOORDINATION

- Du ejer zone: `kv1ntos` (~/projekts/projects/cirkelline-kv1ntos/)
- Andre terminaler rører IKKE dine filer
- Rapportér fremskridt til: `~/.admiral/terminal-status/terminal3.json`
- Format: `{"terminal": 3, "zone": "kv1ntos", "status": "working", "progress": "2/6 done", "timestamp": "ISO"}`

## START HER

```bash
cd ~/Desktop/projekts/projects/cirkelline-kv1ntos/cirkelline-ui
# Tjek om dependencies er installeret: ls node_modules/.package-lock.json
# Start: pnpm dev -p 3000
# Læs src/app/chat/page.tsx — forstå hvad der mangler
# Fix chat FØRST — det er produktets kerne
```
