# Cirkelline System Port Oversigt

**Version:** 1.0.0
**Sidst Opdateret:** 2025-12-09
**Status:** Officiel Reference

---

## Oversigt

Denne fil er den **autoritative kilde** for alle port-tildelinger i Cirkelline-økosystemet.

---

## Port Tildelinger

### Produktion vs. Development

| Komponent | Development Port | Produktion | Beskrivelse |
|-----------|-----------------|------------|-------------|
| **Cirkelline Main** | 7777 | api.cirkelline.com | Hoved-orchestrator |
| **CKC Backend** | 7778 | ckc-backend.cirkelline.com | CKC admin backend |
| **CKC Gateway (SSO)** | 7779 | ckc.cirkelline.com | SSO Gateway |
| **Cosmic Library** | 7780 | cosmic.cirkelline.com | Document management |
| **Command Center** | 7781 | command.cirkelline.com | Agent orchestration |
| **lib-admin** | 8001 | admin.cirkelline.com | Admin dashboard backend |
| **CLA Sync API** | 8080 | sync.cirkelline.com | Local agent sync |

### Database Ports

| Database | Port | Beskrivelse |
|----------|------|-------------|
| PostgreSQL (Cirkelline) | 5532 | Hoved database |
| PostgreSQL (CKC) | 5533 | CKC admin database |
| Redis | 6379 | Cache og sessions |

### Frontend Ports (Development)

| Frontend | Port | Beskrivelse |
|----------|------|-------------|
| Cirkelline UI | 3000 | Next.js frontend |
| CKC Dashboard | 3001 | Admin dashboard |
| Cosmic Library UI | 3002 | Document UI |
| CLA (Tauri) | 1420 | Desktop app dev server |

---

## Service Arkitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                      CIRKELLINE SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Frontend   │    │  Frontend   │    │  Frontend   │        │
│  │   :3000     │    │   :3001     │    │   :3002     │        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Cirkelline  │    │    CKC      │    │   Cosmic    │        │
│  │   :7777     │◄──►│   :7779     │◄──►│   :7780     │        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│         │                  │                  │                │
│         │           ┌──────┴──────┐           │                │
│         │           │ CKC Backend │           │                │
│         │           │   :7778     │           │                │
│         │           └─────────────┘           │                │
│         │                                     │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              PostgreSQL Database :5532               │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐                           │
│  │ lib-admin   │    │  Command    │                           │
│  │   :8001     │    │   Center    │                           │
│  │             │    │   :7781     │                           │
│  └─────────────┘    └─────────────┘                           │
│                                                                 │
│  ┌─────────────┐                                               │
│  │    CLA      │                                               │
│  │ Sync :8080  │                                               │
│  └─────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Port Ranges

| Range | Anvendelse |
|-------|------------|
| 3000-3999 | Frontend development servers |
| 5500-5599 | Databaser |
| 6300-6399 | Cache (Redis) |
| 7777-7799 | Core backend services |
| 8000-8099 | Auxiliary services |

---

## Konflikt Forebyggelse

### Regler

1. **Aldrig ændre eksisterende ports** uden at opdatere denne fil
2. **Nye services** skal bruge næste ledige port i relevant range
3. **Dokumentation** skal referere til denne fil for port info
4. **Kode** skal bruge environment variables, ikke hardcodede ports

### Environment Variables

```bash
# Cirkelline Main
CIRKELLINE_PORT=7777

# CKC System
CKC_BACKEND_PORT=7778
CKC_GATEWAY_PORT=7779

# Cosmic Library
COSMIC_LIBRARY_PORT=7780

# Command Center
COMMAND_CENTER_PORT=7781

# lib-admin
LIB_ADMIN_PORT=8001

# CLA Sync
CLA_SYNC_PORT=8080

# Databases
POSTGRES_PORT=5532
REDIS_PORT=6379
```

---

## Verifikation

```bash
# Tjek hvilke ports der er i brug
netstat -tlnp | grep -E '(7777|7778|7779|7780|7781|8001|5532)'

# Eller med ss
ss -tlnp | grep -E '(7777|7778|7779|7780|7781|8001|5532)'
```

---

## Relateret Dokumentation

- [CKC Architecture](../lib-admin-main/docs/ARCHITECTURE.md)
- [Cosmic Library Architecture](../Cosmic-Library-main/docs/ARCHITECTURE.md)
- [CLA Architecture](cla/docs/ARCHITECTURE.md)

---

*Denne fil er del af Cirkelline FASE 2 Dokumentations-Initiative.*
