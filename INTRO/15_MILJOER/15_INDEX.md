# 15_MILJOER - Environments & Configuration

**Purpose:** Environment configurations, deployment settings, infrastructure
**Template for:** All environment and configuration documentation

---

## WHAT GOES HERE

### Documents
- **15_MILJOER.md** - Environment overview
- **15A_REELLE_MILJOER.md** - Real environments (dev, staging, prod)
- **15B_TEMPLATES.md** - Configuration templates
- **15C_PORT_MAPPING.md** - Port allocations
- **15D_UDVIKLINGS_STATUS.md** - Development environment status

### Environment Files (Examples)
- **.env.example** - Environment variable template
- **.env.dev** - Development configuration
- **.env.staging** - Staging configuration
- **.env.prod** - Production configuration (secure!)

### Subdirectories
- **configs/** - Configuration files (nginx, docker-compose, etc.)
- **scripts/** - Environment setup scripts

---

## TEMPLATE EXAMPLE

### Port Mapping Template
```markdown
| Service | Dev Port | Staging Port | Prod Port |
|---------|----------|--------------|-----------|
| Frontend | 3000 | 3100 | 443 |
| Backend | 7777 | 7778 | 8080 |
| Database | 5432 | 5433 | 5432 |
```

### Environment Variables Template
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# API Keys
STRIPE_SECRET_KEY=sk_test_...
GOOGLE_API_KEY=...

# App Config
NODE_ENV=development
PORT=3000
```

---

## SECURITY NOTES

- **NEVER** commit real .env files with secrets
- Always use .env.example as template
- Document which variables are required
- Use secrets management for production

---

## RELATED SECTIONS

- **10_ARKITEKTUR:** System design that defines environments
- **70_GUIDES:** Setup guides for environments

---

## CHANGELOG

| Dato | Tid | Handling | Af |
|------|-----|----------|-----|
| 2026-01-01 | 03:30 | Template sektion oprettet | Kv1nt |
