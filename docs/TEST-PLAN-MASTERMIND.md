# 🧪 MASTERMIND & ECOSYSTEMS TEST PLAN

**Dato:** 2025-12-12
**Version:** v1.3.1
**Miljø:** Lokal (localhost:7777)

---

## 📋 OVERSIGT

### Hvad testes:
1. **Mastermind Orchestrator** - Cirkelline hovedagent
2. **Specialist Agents** - Audio, Video, Image, Document
3. **Specialist Teams** - Research Team, Law Team
4. **ecosystems/ckc-core/** - Isoleret udviklingsmiljø
5. **Database & Sessions** - AI schema tabeller
6. **Automatiserede Tests** - 36 test filer

---

## 🔐 TEST CREDENTIALS

```bash
# Ivo (Admin)
EMAIL="opnureyes2@gmail.com"
PASSWORD="RASMUS_PASSWORD_HERE"
USER_ID="ee461076-8cbb-4626-947b-956f293cf7bf"

# Rasmus (Admin)
EMAIL="opnureyes2@gmail.com"
PASSWORD="RASMUS_PASSWORD_HERE"
USER_ID="a1234567-8901-2345-6789-012345678901"
```

---

## 🚀 FASE 1: GRUNDLÆGGENDE SYSTEM CHECK

### 1.1 Backend Health
```bash
curl -s http://localhost:7777/health
# Forventet: {"status":"ok",...}

curl -s http://localhost:7777/config
# Forventet: {"status":"healthy","version":"1.3",...}
```

### 1.2 Database Connection
```bash
docker exec ckc-postgres psql -U ckc -d ckc_brain -c "SELECT COUNT(*) FROM users;"
# Forventet: 2 brugere

docker exec ckc-postgres psql -U ckc -d ckc_brain -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'ai';"
# Forventet: agno_sessions, agno_memories, agno_knowledge, cirkelline_knowledge_vectors
```

### 1.3 Login Test
```bash
# Login og gem token
TOKEN=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"RASMUS_PASSWORD_HERE"}' | jq -r '.token')

echo "Token: $TOKEN"
# Forventet: JWT token string
```

---

## 🎭 FASE 2: MASTERMIND ORCHESTRATOR (Cirkelline)

### 2.1 Simpel Samtale
```bash
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hej! Hvem er du og hvad kan du hjælpe med?" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
# Forventet: Venlig introduktion fra Cirkelline
```

### 2.2 Memory System Test
```bash
# Test memory creation
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Husk at min yndlingsfarve er blå og jeg elsker kaffe" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"

# Test memory retrieval
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hvad er min yndlingsfarve?" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
# Forventet: Cirkelline husker "blå"
```

### 2.3 Web Search Test (Quick Search Mode)
```bash
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hvad er de seneste AI nyheder i dag?" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
# Forventet: Søgeresultater fra DuckDuckGo/Exa/Tavily
```

---

## 👥 FASE 3: SPECIALIST AGENTS

### 3.1 Liste Tilgængelige Agents
```bash
curl -s http://localhost:7777/agents | jq '.[].name'
# Forventet: Audio Specialist, Video Specialist, Image Specialist, Document Specialist
```

### 3.2 Document Specialist Test
```bash
# Test med tekst (uden fil upload)
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Kan du hjælpe mig med at analysere et dokument? Jeg vil gerne vide hvad du kan." \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
```

---

## 🔬 FASE 4: SPECIALIST TEAMS

### 4.1 Liste Tilgængelige Teams
```bash
curl -s http://localhost:7777/teams | jq '.[].name'
# Forventet: Cirkelline (og evt. Research Team, Law Team som sub-teams)
```

### 4.2 Research Team Test (via Cirkelline)
```bash
# Quick search (ikke deep research)
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Undersøg hvad de bedste projekt management tools er i 2024" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
```

### 4.3 Law Team Test (via Cirkelline)
```bash
curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hvad er de grundlæggende GDPR krav for dataopbevaring?" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false"
```

---

## 📁 FASE 5: ECOSYSTEMS/CKC-CORE

### 5.1 Verificer Struktur
```bash
ls -la /home/rasmus/Desktop/projects/cirkelline-system/ecosystems/ckc-core/
# Forventet: cirkelline/, tests/, migrations/, my_os.py, etc.

# Tjek VERSION
cat /home/rasmus/Desktop/projects/cirkelline-system/ecosystems/ckc-core/VERSION
# Forventet: v1.3.1-stable
```

### 5.2 Verificer Git Isolation
```bash
cd /home/rasmus/Desktop/projects/cirkelline-system/ecosystems/ckc-core
git status
git log --oneline -5
# Forventet: Separat git repo med egen historie
```

### 5.3 Sammenlign med Hovedkode
```bash
# Tjek at ckc-core har samme struktur
diff -rq /home/rasmus/Desktop/projects/cirkelline-system/cirkelline \
         /home/rasmus/Desktop/projects/cirkelline-system/ecosystems/ckc-core/cirkelline \
         --exclude="__pycache__" | head -20
```

---

## 🧪 FASE 6: AUTOMATISEREDE TESTS

### 6.1 Kør Hovedtest
```bash
cd /home/rasmus/Desktop/projects/cirkelline-system
source /home/rasmus/Desktop/projects/cirkelline-env/bin/activate
PYTHONPATH=. pytest tests/test_cirkelline.py -v
```

### 6.2 Kør Mastermind Tests
```bash
PYTHONPATH=. pytest tests/test_mastermind.py -v
```

### 6.3 Kør Session Tests
```bash
PYTHONPATH=. pytest tests/test_session.py -v
```

### 6.4 Kør ALLE Tests
```bash
PYTHONPATH=. pytest tests/ -v --tb=short 2>&1 | tee test_results.log
```

### 6.5 Kør Tests i ckc-core
```bash
cd /home/rasmus/Desktop/projects/cirkelline-system/ecosystems/ckc-core
PYTHONPATH=. pytest tests/ -v --tb=short
```

---

## 📊 FASE 7: DATABASE VERIFIKATION

### 7.1 Tjek AI Schema
```bash
docker exec ckc-postgres psql -U ckc -d ckc_brain -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'ai'
ORDER BY tablename;
"
```

### 7.2 Tjek Sessions
```bash
docker exec ckc-postgres psql -U ckc -d ckc_brain -c "
SELECT id, user_id, session_name, created_at
FROM ai.agno_sessions
ORDER BY created_at DESC
LIMIT 5;
"
```

### 7.3 Tjek Memories
```bash
docker exec ckc-postgres psql -U ckc -d ckc_brain -c "
SELECT id, user_id, LEFT(content, 50) as content_preview, topics
FROM ai.agno_memories
ORDER BY created_at DESC
LIMIT 5;
"
```

---

## ✅ TEST CHECKLIST

### Fase 1: System Check
- [ ] Backend health OK
- [ ] Database forbindelse OK
- [ ] Login virker
- [ ] Token genereres

### Fase 2: Mastermind
- [ ] Simpel samtale virker
- [ ] Memory creation virker
- [ ] Memory retrieval virker
- [ ] Web search virker

### Fase 3: Specialists
- [ ] Agents liste tilgængelig
- [ ] Document specialist responderer

### Fase 4: Teams
- [ ] Teams liste tilgængelig
- [ ] Research delegation virker
- [ ] Law delegation virker

### Fase 5: Ecosystems
- [ ] ckc-core struktur korrekt
- [ ] Git isolation verificeret
- [ ] VERSION fil korrekt

### Fase 6: Automatiserede Tests
- [ ] test_cirkelline.py passed
- [ ] test_mastermind.py passed
- [ ] test_session.py passed
- [ ] Fuld test suite kørt

### Fase 7: Database
- [ ] AI schema tabeller eksisterer
- [ ] Sessions gemmes korrekt
- [ ] Memories gemmes korrekt

---

## 🛠️ QUICK START SCRIPT

Kør alt på én gang:

```bash
#!/bin/bash
# test_all.sh

echo "=== MASTERMIND TEST SUITE ==="
cd /home/rasmus/Desktop/projects/cirkelline-system
source /home/rasmus/Desktop/projects/cirkelline-env/bin/activate

echo ""
echo "1. Health Check..."
curl -s http://localhost:7777/health

echo ""
echo "2. Login..."
TOKEN=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"RASMUS_PASSWORD_HERE"}' | jq -r '.token')

if [ "$TOKEN" != "null" ]; then
    echo "   ✅ Login OK"
else
    echo "   ❌ Login FEJL"
    exit 1
fi

echo ""
echo "3. Chat Test..."
RESPONSE=$(curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hej!" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false")

if echo "$RESPONSE" | grep -q "content"; then
    echo "   ✅ Chat OK"
else
    echo "   ❌ Chat FEJL"
fi

echo ""
echo "4. Pytest..."
PYTHONPATH=. pytest tests/test_cirkelline.py -v --tb=short

echo ""
echo "=== TEST COMPLETE ==="
```

---

## 📝 NOTER

- **Rate Limits:** Google Gemini har 1,500 RPM limit - vent mellem tests hvis nødvendigt
- **Sessions:** Hver chat opretter en session i ai.agno_sessions
- **Isolation:** ckc-core er HELT isoleret fra hovedkoden
- **Produktion:** Disse tests påvirker IKKE AWS produktion
