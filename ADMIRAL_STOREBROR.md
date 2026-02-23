# ADMIRAL STOREBROR — Cirkelline på Nyt Domæne

> Admiral er ikke en person. Admiral er det autonome lag der overvåger,
> beskytter og forbedrer Cirkelline — 24/7, mens du sover.

**Repo:** `opnureyes2-del/Cirkelline-KV1NTOS-Admiral` (PRIVAT)
**Status:** Klar til deploy på nyt domæne
**Dato:** 2026-02-24

---

## HVAD ER ADMIRAL STOREBROR?

Cirkelline er platformen. **Admiral er storebror** — en autonom AI-orkestrator
der lever ved siden af Cirkelline og tager sig af:

| Funktion | Beskrivelse |
|----------|-------------|
| **Sundhedstjek** | Tjekker Cirkelline hvert 5. minut — genstarter hvis den fejler |
| **Agentflow** | Modtager agenter fra Cosmic Library (graduation endpoint) |
| **Viden** | Læser Cirkellines logs og lærer mønstre |
| **Alerts** | Sender Telegram-notifikationer ved problemer |
| **Qualitet** | Kører qualitetskontrol på nye features |
| **Git guardian** | Holder styr på ucommittede ændringer |

```
[Brugere] ──→ [Cirkelline] ──→ [PostgreSQL 5532]
                    ↕
            [Admiral Storebror]
                    ↕
         [RabbitMQ Event Bus]
                    ↕
    [Odin] [Grafana] [Telegram]
```

---

## DEPLOY PÅ NYT DOMÆNE — TRIN FOR TRIN

### Forudsætninger
- Ubuntu 22.04+ server (min. 4GB RAM, 40GB disk)
- Domænenavn peget mod serverens IP
- SSH-adgang til server

### Trin 1: Klon privat repo på serveren
```bash
# På serveren
git clone git@github.com:opnureyes2-del/Cirkelline-KV1NTOS-Admiral.git cirkelline
cd cirkelline
```

### Trin 2: Installer afhængigheder
```bash
# Python backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Node frontend
cd cirkelline-ui
npm install
npm run build
cd ..
```

### Trin 3: PostgreSQL + Docker
```bash
# Start database container
docker compose up -d cirkelline-postgres

# Kør migrations
source .venv/bin/activate
alembic upgrade head
```

### Trin 4: Miljøvariabler
```bash
cp .env.example .env
# Rediger .env med:
# DATABASE_URL=postgresql://cirkelline:SKIFT_PW@localhost:5532/cirkelline
# REDIS_URL=redis://localhost:6381
# GOOGLE_API_KEY=...
# DOMAIN=https://dit-nyt-domane.dk
```

### Trin 5: Caddy som reverse proxy
```bash
# /etc/caddy/Caddyfile
cat > /etc/caddy/Caddyfile << 'EOF'
dit-nyt-domane.dk {
    reverse_proxy /api/* localhost:7777
    reverse_proxy /* localhost:3000

    # Admiral storebror API
    reverse_proxy /admiral/* localhost:5592
}
EOF

systemctl restart caddy
```

### Trin 6: Systemd services
```bash
# Backend
cat > /etc/systemd/system/cirkelline-backend.service << 'EOF'
[Unit]
Description=Cirkelline Backend
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/cirkelline
ExecStart=/home/ubuntu/cirkelline/.venv/bin/python -m uvicorn cirkelline.main:app --host 0.0.0.0 --port 7777
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/cirkelline/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl enable cirkelline-backend
systemctl start cirkelline-backend
```

### Trin 7: Verificer
```bash
curl http://localhost:7777/health
curl http://localhost:3000
# Forventet: {"status": "ok", "version": "3.0.0"}
```

---

## ADMIRAL STOREBROR SERVICES PÅ NY SERVER

Disse Admiral-services ANBEFALES at køre med Cirkelline:

### Minimum (kritisk)
```bash
# Healthcheck — genstarter Cirkelline ved fejl
# Kør i cron eller som service:
*/5 * * * * curl -sf http://localhost:7777/health || systemctl restart cirkelline-backend
```

### Fuld Admiral (anbefalet)
```bash
# Installer ELLE.md Admiral på serveren
git clone git@github.com:opnureyes2-del/ELLE.md.git /opt/admiral
cd /opt/admiral

# Konfigurer Cirkelline gateway
python3 AGENTS/agents/admiral_cirkelline_gateway.py \
  --cirkelline-url http://localhost:7777 \
  --enable-auto-restart \
  --enable-alerts
```

---

## INTEGRATION: GRADUATION PIPELINE

Cosmic Library → Cirkelline agent-pipeline er nu aktiv:

```python
# Cirkelline modtager trænede agenter fra Cosmic Library
POST /api/agents/import-from-cosmic

# Payload (fra Cosmic Library's export_agent_to_cirkelline())
{
    "name": "agent-navn",
    "mastery_score": 0.87,
    "capabilities": ["booking", "customer-service"],
    "model": "gemini-2.5-flash",
    "training_sessions": 42
}
```

**Flow:**
1. Cosmic Library træner agent → mastery ≥ 80%
2. Cosmic sender POST til Cirkelline `/api/agents/import-from-cosmic`
3. Cirkelline validerer + gemmer i `graduated_agents` tabel
4. Event publishes til RabbitMQ `elle_integration_hub`
5. Admiral reagerer via Event Reactor (Chain 98)

---

## LOKALE REMOTES

```bash
# Nuværende remotes i cirkelline-kv1ntos/
git remote -v
# origin   git@github.com:opnureyes2-del/Cirkelline-Kv1ntos.git (PUBLIC)
# admiral  git@github.com:opnureyes2-del/Cirkelline-KV1NTOS-Admiral.git (PRIVAT)

# Push til begge
git push origin main      # til public (åben kode)
git push admiral main     # til privat (med credentials + Admiral integration)
```

---

## HVAD DU SKAL GØRE (BRUGER-HANDLING)

| Handling | Kommando / Sted |
|----------|-----------------|
| Køb domæne | Namecheap, One.com, Simply.com |
| Opret server | Hetzner CX31 (4GB/2CPU, ~€5/mnd) eller DigitalOcean |
| Peg DNS | A-record: dit-domæne.dk → server-IP |
| Klon repo på server | `git clone git@github.com:opnureyes2-del/Cirkelline-KV1NTOS-Admiral.git` |
| Opret SSH deploy key | `ssh-keygen -t ed25519` → tilføj til GitHub repo settings |
| Opsæt .env | Kopier fra lokal `.env` — skift database passwords |

---

## SIKKERHED (INDEN LAUNCH)

```bash
# 1. Skift database password
ALTER USER cirkelline WITH PASSWORD 'nyt-stærkt-kodeord-2026';

# 2. Firewall
ufw allow 80,443/tcp
ufw deny 5532/tcp  # PostgreSQL ALDRIG offentlig
ufw enable

# 3. SSL via Caddy (automatisk)
# Caddy håndterer Let's Encrypt automatisk

# 4. Fjern debug mode
# .env: DEBUG=false
# .env: ALLOWED_HOSTS=dit-domæne.dk
```

---

*Dokument oprettet af KV1NT-PRO (Claude Sonnet 4.6) — 2026-02-24*
*Privat repo: https://github.com/opnureyes2-del/Cirkelline-KV1NTOS-Admiral*
