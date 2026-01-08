# Cirkelline Terminologi Glossar

**Version:** 1.0.0
**Sidst Opdateret:** 2025-12-09
**Status:** Officiel Standard

---

## Formål

Dette glossar definerer **officiel terminologi** for alle Cirkelline projekter.
Al dokumentation og kode skal følge disse standarder.

---

## Platform Navne

| Officiel Term | Beskrivelse | Undgå |
|---------------|-------------|-------|
| **Cirkelline** | Hoved AI-orchestrator system | cirkelline-system (kun til repo) |
| **CKC** | Admin/SSO platform (Cirkelline Knowledge Center) | lib-admin (kun internt/teknisk) |
| **Cosmic Library** | Document management platform | CosmicLibrary, cosmic-library |
| **CLA** | Desktop app (Cirkelline Local Agent) | cla, local-agent |
| **Command Center** | Agent orchestration platform | Commando Center |
| **Consulting** | Consulting booking platform | Cirkelline Consulting |

---

## Tekniske Termer

### Agent System

| Officiel Term | Beskrivelse | Undgå |
|---------------|-------------|-------|
| **Agent** | AI specialist enhed | Bot, Assistant |
| **Team** | Gruppe af samarbejdende agents | Crew, Squad |
| **Orchestrator** | Koordinerende agent | Manager, Controller |
| **DNA** | Agent personlighedskonfiguration | Config, Personality |
| **Tool** | Agent capability/funktion | Function, Skill |

### Training System

| Officiel Term | Beskrivelse | Undgå |
|---------------|-------------|-------|
| **Training Room** | Virtuelt træningsrum | Learning Room, Lærerum |
| **Training Session** | En træningssession | Session, Run |
| **Training Cycle** | Komplet træningsforløb | Round, Iteration |
| **Proficiency** | Agent kompetenceniveau | Skill level, Score |

### Authentication

| Officiel Term | Beskrivelse | Undgå |
|---------------|-------------|-------|
| **SSO** | Single Sign-On via CKC | Login, Auth |
| **Gateway** | CKC authentication service | Auth server |
| **Token** | JWT access token | Session, Key |
| **Platform Access** | Adgang til specifik platform | Permission |

### Data & Storage

| Officiel Term | Beskrivelse | Undgå |
|---------------|-------------|-------|
| **Knowledge Base** | Brugerens dokument-samling | Document store, Library |
| **Collection** | Gruppering af dokumenter | Folder, Category |
| **Embedding** | Vector repræsentation | Vector, Encoding |
| **Chunk** | Dokument-segment | Part, Piece |

---

## Bruger Tiers

| Tier | Beskrivelse | Features |
|------|-------------|----------|
| **Free** | Gratis niveau | Basis funktioner |
| **Creator** | Betalt niveau | Udvidet funktionalitet |
| **VIP** | Premium niveau | Alle funktioner |
| **Admin** | Administrator | System administration |
| **Super Admin** | Hoved administrator | Fuld kontrol |

---

## Status Termer

| Officiel Term | Betydning | Undgå |
|---------------|-----------|-------|
| **Active** | I drift / aktiv | Running, Live |
| **Inactive** | Ikke aktiv | Disabled, Off |
| **Pending** | Afventer | Waiting, Queued |
| **Completed** | Færdig | Done, Finished |
| **Failed** | Fejlet | Error, Broken |
| **Archived** | Arkiveret | Deleted, Removed |

---

## Sprog Konventioner

### Dokumentation

| Kontekst | Sprog | Eksempel |
|----------|-------|----------|
| **Teknisk docs** | Engelsk | API Reference, Architecture |
| **Brugerguides** | Dansk | Brugerguide, FAQ |
| **Kode kommentarer** | Engelsk | `// Validate user input` |
| **Git commits** | Engelsk | `feat: add user export` |
| **Variable navne** | Engelsk | `user_id`, `training_room` |

### Forkortelser

| Forkortelse | Fuld Form | Anvendelse |
|-------------|-----------|------------|
| **API** | Application Programming Interface | Teknisk |
| **JWT** | JSON Web Token | Teknisk |
| **SSO** | Single Sign-On | Alle |
| **UI** | User Interface | Alle |
| **DB** | Database | Teknisk |
| **ENV** | Environment | Teknisk |

---

## Dato og Tid

| Format | Anvendelse | Eksempel |
|--------|------------|----------|
| **YYYY-MM-DD** | Dokumentation | 2025-12-09 |
| **ISO 8601** | API/Database | 2025-12-09T14:30:00Z |
| **DD. MMM YYYY** | Dansk UI | 9. dec 2025 |

---

## Version Nummerering

Vi følger [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

Eksempel: 1.2.3
- MAJOR: Breaking changes
- MINOR: Nye features (backwards compatible)
- PATCH: Bug fixes
```

---

## Eksempler på Korrekt Brug

### Korrekt

```markdown
"CKC håndterer SSO authentication for Cosmic Library"
"Training Room session startede kl. 14:30"
"Agent DNA definerer personlighed og capabilities"
```

### Forkert

```markdown
"lib-admin håndterer login for CosmicLibrary"  ❌
"Learning Room sessionen startede kl. 14:30"   ❌
"Agent config definerer personality og skills"  ❌
```

---

## Opdatering af Dette Glossar

1. Nye termer skal godkendes af Super Admin
2. Ændringer skal dokumenteres i CHANGELOG
3. Al eksisterende dokumentation skal opdateres ved ændringer

---

## Relateret Dokumentation

- [Port Oversigt](PORT-OVERSIGT.md)
- [Contribution Guide](../lib-admin-main/CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

*Denne fil er del af Cirkelline FASE 2 Dokumentations-Initiative.*
