# ENVIRONMENT VARIABLES REFERENCE

**Last Updated:** 2025-11-27
**Current Version:** v1.2.32

---

## Table of Contents
- [Overview](#overview)
- [Backend Variables](#backend-variables)
- [Frontend Variables](#frontend-variables)
- [Localhost vs AWS](#localhost-vs-aws)
- [How to Update](#how-to-update)
- [Security Considerations](#security-considerations)
- [Quick Reference](#quick-reference)

---

## Overview

### Environment Files

```
Backend (Python):
├── .env                        # Local development
└── AWS Secrets Manager         # Production

Frontend (Next.js):
├── .env.local                  # Local development
└── Vercel Environment          # Production
```

### Variable Categories

| Category | Variables | Purpose |
|----------|-----------|---------|
| AI Services | GOOGLE_API_KEY, OPENAI_API_KEY, EXA_API_KEY, TAVILY_API_KEY | AI model access |
| Database | DATABASE_URL | PostgreSQL connection |
| Authentication | JWT_SECRET_KEY | Token signing |
| Monitoring | AGNO_MONITOR, AGNO_DEBUG | Logging and debugging |
| Frontend | NEXT_PUBLIC_API_URL | Backend URL |

---

## Backend Variables

### Development (.env)

**Location:** `/home/eenvy/Desktop/cirkelline/.env`

**Complete File:**
```bash
# AI Services
GOOGLE_API_KEY=AIzaSyCjFBlym-lmEl8l-KuLvTWUVt9mWIYWCvE
OPENAI_API_KEY=sk-placeholder-for-knowledge-base
EXA_API_KEY=83082804-12e1-4a16-8151-c3c92eef966f
TAVILY_API_KEY=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

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# JWT Authentication
JWT_SECRET_KEY=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68

# Monitoring & Debugging
AGNO_MONITOR=true
AGNO_DEBUG=true          # Enable DEBUG statements (development mode)
```

**⚠️ IMPORTANT NOTE (Updated 2025-10-31):** We now use SEPARATE Google API keys for development and production:
- **Development:** AIzaSyCjFBlym-lmEl8l-KuLvTWUVt9mWIYWCvE (shown above)
- **Production:** AIzaSyD07oYF6adWs_HTkSaCYoNPd6nM4T5J57M (in AWS Secrets Manager)

### Variable Details

#### GOOGLE_API_KEY

**Purpose:** Google Gemini API access

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (implicitly by AGNO)
- All Agent/Team model initialization
- Embeddings generation

**Where It's Used:**
```python
# Line 37-43: Gemini models
from agno.models.google import Gemini

# Line 82-88: Embedder
from agno.knowledge.embedder.google import GeminiEmbedder

# AGNO automatically reads GOOGLE_API_KEY from environment
```

**Rate Limits:**
- **Free Tier:** 10 RPM, 1,500 RPD
- **Tier 1:** 1,500 RPM, unlimited RPD

**Current Keys (Updated 2025-10-31):**
- **Development:** AIzaSyCjFBlym-lmEl8l-KuLvTWUVt9mWIYWCvE (Tier 1)
- **Production:** AIzaSyD07oYF6adWs_HTkSaCYoNPd6nM4T5J57M (Tier 1)

**Reason for Split:** Due to billing issues with the original Google Console project, we created new projects with separate API keys for development and production environments.

**How to Get:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create new project or select existing
3. Enable Gemini API
4. Create API key
5. Copy key to .env (development) or AWS Secrets Manager (production)

**Troubleshooting:**
```bash
# Check current key (localhost)
echo $GOOGLE_API_KEY
# Should be: AIzaSyCjFBlym-lmEl8l-KuLvTWUVt9mWIYWCvE

# Check production key (AWS)
aws secretsmanager get-secret-value \
  --secret-id cirkelline-system/google-api-key \
  --region eu-north-1 \
  --query SecretString --output text
# Should be: AIzaSyD07oYF6adWs_HTkSaCYoNPd6nM4T5J57M
```

---

#### OPENAI_API_KEY

**Purpose:** Placeholder for AGNO Knowledge module

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 143-148)

**Note:** Currently a placeholder. AGNO Knowledge module requires this variable to exist, but it's not actively used because we're using Gemini embeddings.

**Value:** Any string (e.g., "sk-placeholder-for-knowledge-base")

---

#### EXA_API_KEY

**Purpose:** Exa neural search API

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (line 371)
- Web Researcher agent (Research Team)

**Usage:**
```python
web_researcher = Agent(
    tools=[
        DuckDuckGoTools(),
        ExaTools(),  # Uses EXA_API_KEY
        TavilyTools()
    ]
)
```

**How to Get:**
1. Go to https://exa.ai
2. Sign up for account
3. Generate API key
4. Copy to .env

---

#### TAVILY_API_KEY

**Purpose:** Tavily search API

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (line 371)
- Web Researcher agent (Research Team)

**Usage:**
```python
web_researcher = Agent(
    tools=[
        DuckDuckGoTools(),
        ExaTools(),
        TavilyTools()  # Uses TAVILY_API_KEY
    ]
)
```

**How to Get:**
1. Go to https://tavily.com
2. Sign up for account
3. Generate API key
4. Copy to .env

---

#### DATABASE_URL

**Purpose:** PostgreSQL connection string

**Format:**
```
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

**Localhost:**
```bash
postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
```

**AWS RDS:**
```bash
postgresql://postgres:PASSWORD@cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432/cirkelline_system
```

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 74, 83)
- Database connection initialization
- Vector database connection

**Usage:**
```python
# Line 74: Main database
db = PostgresDb(
    db_url=os.getenv("DATABASE_URL")
)

# Line 83: Vector database (same connection)
vector_db = PgVector(
    db_url=os.getenv("DATABASE_URL"),
    table_name="cirkelline_knowledge_vectors"
)
```

**Troubleshooting:**
```bash
# Test connection
psql "postgresql://cirkelline:cirkelline123@localhost:5532/cirkelline" -c "SELECT 1;"

# Check if Docker container is running
docker ps | grep cirkelline-postgres

# Start if stopped
docker start cirkelline-postgres
```

---

#### JWT_SECRET_KEY

**Purpose:** Sign and verify JWT tokens

**Format:** 64-character hexadecimal string

**Generation:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68
```

**Used In:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 743, 968, 1036, 1081, 1256, 1378)
- JWT signing (login/signup)
- JWT verification (middleware)

**Usage:**
```python
# Line 743: Middleware configuration
app.add_middleware(
    JWTMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256"
)

# Line 1256: Token generation
token = pyjwt.encode(
    jwt_payload,
    os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256"
)

# Line 968: Token verification
payload = pyjwt.decode(
    token,
    os.getenv("JWT_SECRET_KEY"),
    algorithms=["HS256"]
)
```

**Security:**
- NEVER commit to git
- NEVER share publicly
- Rotate every 90 days
- Use different keys for localhost/AWS

---

#### AGNO_MONITOR

**Purpose:** Enable AGNO monitoring/metrics

**Values:**
- `true`: Enable monitoring
- `false`: Disable monitoring

**Used In:**
- AGNO framework (internal)
- Enables performance metrics
- Tracks agent execution

**Usage:**
```python
# Line 32-34: Force enable
os.environ["AGNO_MONITOR"] = "true"
```

**Note:** Currently force-enabled in code because environment variable wasn't being read correctly.

---

#### AGNO_DEBUG

**Purpose:** Control debug logging verbosity for development vs production

**Values:**
- `true`: Enable verbose DEBUG statements (development mode)
- `false`: Disable DEBUG statements, clean logs (production mode)

**Used In:**
- `/home/eenvy/Desktop/cirkelline/cirkelline/config.py` (lines 40-47)
- `/home/eenvy/Desktop/cirkelline/my_os.py` (11 DEBUG print statements)
- AGNO framework (internal logging)

**How It Works:**

1. **Global DEBUG_MODE flag** (`cirkelline/config.py`):
```python
# Lines 40-47
# ════════════════════════════════════════════════════════════════
# DEBUG MODE CONFIGURATION
# ════════════════════════════════════════════════════════════════
# Controls whether DEBUG print statements are shown in logs
# Set AGNO_DEBUG=true in .env for development (verbose logging)
# Set AGNO_DEBUG=false in .env for production (clean logs)
DEBUG_MODE = os.getenv('AGNO_DEBUG', 'false').lower() == 'true'
logger.info(f"Debug mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'} (AGNO_DEBUG={os.getenv('AGNO_DEBUG', 'false')})")
```

2. **Conditional DEBUG statements** wrapped with checks:
```python
# Example from cirkelline/config.py (lines 33-35)
if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
    print(f"DEBUG: DATABASE_URL = {os.getenv('DATABASE_URL')}")
    logger.info(f"DEBUG: DATABASE_URL from environment = {os.getenv('DATABASE_URL')}")

# Example from my_os.py (lines 298-307)
if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
    print("=" * 80)
    print("DEBUG: Starting Stage 4 - AgentOS initialization")
    print("=" * 80)
```

3. **logger.info() statements are ALWAYS visible** (not wrapped):
```python
# These always appear in logs regardless of AGNO_DEBUG value
logger.info("Stage 4: Starting AgentOS initialization...")
logger.info("Stage 4.1: All specialist agents verified")
```

**Environment Variable Export Issue:**

**Problem:** Using `load_dotenv()` from python-dotenv does NOT properly load AGNO_DEBUG:

```python
# Testing showed:
from dotenv import load_dotenv, dotenv_values

dotenv_values('.env')  # Returns: {'AGNO_DEBUG': 'true'} ✅
load_dotenv()          # Does NOT set AGNO_DEBUG in os.environ ❌
os.getenv('AGNO_DEBUG')  # Returns: None
```

**Solution:** Export AGNO_DEBUG in `.venv/bin/activate` script BEFORE Python starts:

```bash
# Line 76 in .venv/bin/activate
export AGNO_DEBUG=true
```

This ensures the variable is available in the shell environment before `python my_os.py` executes.

**Why This Works:**
- Virtual environment activation scripts run BEFORE Python interpreter starts
- Shell `export` makes the variable available to all child processes (including Python)
- `os.getenv('AGNO_DEBUG')` can now read the exported value

**Configuration Locations:**

1. **Development (.env file):**
```bash
# /home/eenvy/Desktop/cirkelline/.env
AGNO_DEBUG=true        # Enable debug statements
AGNO_DEBUG_LEVEL=2     # Not currently used
```

2. **Development (venv activation script) - RECOMMENDED:**
```bash
# /home/eenvy/Desktop/cirkelline/.venv/bin/activate (line 76)
export AGNO_DEBUG=true  # This is what actually works
```

3. **Production (AWS ECS Task Definition):**
```json
{
  "environment": [
    {
      "name": "AGNO_DEBUG",
      "value": "false"  # Disable debug statements in production
    }
  ]
}
```

**Development vs Production:**

| Environment | AGNO_DEBUG | Behavior |
|-------------|------------|----------|
| Localhost Development | `true` | Verbose DEBUG statements visible, helpful for troubleshooting |
| AWS Production | `false` | Clean logs, no DEBUG spam, better performance |

**Output Examples:**

**Debug Mode ON (AGNO_DEBUG=true):**
```
INFO:     Debug mode: ENABLED (AGNO_DEBUG=true)
DEBUG: DATABASE_URL = postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
================================================================================
DEBUG: Starting Stage 4 - AgentOS initialization
================================================================================
DEBUG: Stage 4.1 - Verifying agents exist...
  - audio_agent: Agent
  - video_agent: Agent
  - image_agent: Agent
  - document_agent: Agent
```

**Debug Mode OFF (AGNO_DEBUG=false):**
```
INFO:     Debug mode: DISABLED (AGNO_DEBUG=false)
INFO:     Stage 4: Starting AgentOS initialization...
INFO:     Stage 4.1: All specialist agents verified
```

**Testing:**

```bash
# Test with debug mode ON
source .venv/bin/activate  # Exports AGNO_DEBUG=true
python my_os.py
# You should see DEBUG statements

# Test with debug mode OFF
# Edit .venv/bin/activate line 76: export AGNO_DEBUG=false
source .venv/bin/activate
python my_os.py
# You should NOT see DEBUG statements
```

**Recommendation:**
- **Development:** Keep `AGNO_DEBUG=true` for detailed troubleshooting
- **Production:** Always use `AGNO_DEBUG=false` to prevent log spam and improve performance

---

## Frontend Variables

### Development (.env.local)

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/.env.local`

**Complete File:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:7777
```

### Variable Details

#### NEXT_PUBLIC_API_URL

**Purpose:** Backend API URL

**Used In:**
- `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/store.ts` (line 82)
- All API calls via selectedEndpoint

**Usage:**
```typescript
// Line 82: Default endpoint
selectedEndpoint: process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
```

**Values:**
- **Localhost:** `http://localhost:7777`
- **AWS:** `http://cirkelline-system-backend-alb-1810847627.eu-north-1.elb.amazonaws.com`
- **Production Domain:** `https://api.cirkelline.com`

**Note:** Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

---

## Localhost vs AWS

### Backend Differences

| Variable | Localhost | AWS |
|----------|-----------|-----|
| GOOGLE_API_KEY | From .env file | From Secrets Manager |
| DATABASE_URL | localhost:5532 | RDS endpoint |
| JWT_SECRET_KEY | From .env file | From Secrets Manager |
| EXA_API_KEY | From .env file | From Secrets Manager |
| TAVILY_API_KEY | From .env file | From Secrets Manager |
| AGNO_MONITOR | true | true |
| AGNO_DEBUG | false | false |

### Frontend Differences

| Variable | Localhost | AWS (Vercel) |
|----------|-----------|--------------|
| NEXT_PUBLIC_API_URL | http://localhost:7777 | https://api.cirkelline.com |

### AWS Secrets Manager

**Secrets:**
```bash
cirkelline-system/database-url
cirkelline-system/google-api-key
cirkelline-system/jwt-secret-key
cirkelline-system/exa-api-key
cirkelline-system/tavily-api-key
```

**Task Definition:**
```json
{
  "secrets": [
    {
      "name": "DATABASE_URL",
      "valueFrom": "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/database-url-xxx"
    },
    {
      "name": "GOOGLE_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/google-api-key-xxx"
    },
    {
      "name": "JWT_SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/jwt-secret-key-xxx"
    }
  ],
  "environment": [
    {
      "name": "AGNO_MONITOR",
      "value": "true"
    },
    {
      "name": "AGNO_DEBUG",
      "value": "false"
    }
  ]
}
```

---

## How to Update

### Update Localhost

#### Backend

```bash
# Edit .env file
cd ~/Desktop/cirkelline
nano .env

# Update variable
GOOGLE_API_KEY=new_key_here

# Restart backend
source .venv/bin/activate
python my_os.py
```

#### Frontend

```bash
# Edit .env.local
cd ~/Desktop/cirkelline/cirkelline-ui
nano .env.local

# Update variable
NEXT_PUBLIC_API_URL=http://localhost:7777

# Restart frontend (build step picks up new value)
npm run dev
```

### Update AWS

#### Backend (Secrets Manager)

```bash
# Update secret
aws secretsmanager update-secret \
    --secret-id cirkelline-system/google-api-key \
    --secret-string "new_api_key_here" \
    --region eu-north-1

# Force ECS to reload secrets (restart tasks)
aws ecs update-service \
    --cluster cirkelline-system-cluster \
    --service cirkelline-system-backend-service \
    --force-new-deployment \
    --region eu-north-1

# Monitor deployment
aws ecs describe-services \
    --cluster cirkelline-system-cluster \
    --services cirkelline-system-backend-service \
    --region eu-north-1 \
    --query 'services[0].deployments'
```

#### Backend (Environment Variables in Task Definition)

```bash
# Edit task-definition.json
nano task-definition.json

# Update environment section
{
  "environment": [
    {
      "name": "AGNO_MONITOR",
      "value": "true"  # ← Change here
    }
  ]
}

# Register new task definition
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region eu-north-1

# Update service to use new task definition
aws ecs update-service \
    --cluster cirkelline-system-cluster \
    --service cirkelline-system-backend-service \
    --task-definition cirkelline-system-backend \
    --force-new-deployment \
    --region eu-north-1
```

#### Frontend (Vercel)

```bash
# Via Vercel Dashboard:
1. Go to https://vercel.com
2. Select cirkelline-system-ui project
3. Settings → Environment Variables
4. Update NEXT_PUBLIC_API_URL
5. Redeploy

# Via CLI:
vercel env add NEXT_PUBLIC_API_URL production
# Enter new value when prompted

# Trigger redeploy
vercel --prod
```

---

## Security Considerations

### Best Practices

#### 1. Never Commit Secrets

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "*.env" >> .gitignore

# Verify not tracked
git status | grep .env
# Should return nothing
```

#### 2. Use Different Keys Per Environment

```
Localhost:
  JWT_SECRET_KEY=key_for_localhost_only
  DATABASE_URL=localhost:5532

AWS:
  JWT_SECRET_KEY=different_key_for_aws
  DATABASE_URL=rds_endpoint
```

#### 3. Rotate Secrets Regularly

```bash
# Every 90 days:
1. Generate new JWT_SECRET_KEY
2. Update in Secrets Manager
3. Force ECS deployment
4. All users will need to re-login
```

#### 4. Restrict Access

```bash
# IAM Policy for Secrets Manager
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/*"
      ]
    }
  ]
}
```

#### 5. Monitor Access

```bash
# CloudTrail logs all Secrets Manager access
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
    --region eu-north-1
```

### Common Mistakes

#### ❌ WRONG: Hardcoding Secrets

```python
# NEVER DO THIS
GOOGLE_API_KEY = "AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk"
```

#### ✅ CORRECT: Using Environment Variables

```python
# ALWAYS DO THIS
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

#### ❌ WRONG: Committing .env

```bash
git add .env
git commit -m "Add environment config"
# DANGER: Secret now in git history forever!
```

#### ✅ CORRECT: Using .gitignore

```bash
# .gitignore
.env
.env.local
*.env

# .env never committed
```

---

## Quick Reference

### Backend (.env)

```bash
GOOGLE_API_KEY=       # Gemini API (Tier 1)
DATABASE_URL=         # PostgreSQL connection
JWT_SECRET_KEY=       # 64-char hex (rotate every 90 days)
OPENAI_API_KEY=       # Placeholder (not actively used)
EXA_API_KEY=          # Exa search
TAVILY_API_KEY=       # Tavily search
AGNO_MONITOR=true     # Enable monitoring
AGNO_DEBUG=true       # Enable debug logs (development)
                      # Export in .venv/bin/activate for reliability
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=  # Backend URL
```

### AWS Secrets

```bash
cirkelline-system/database-url        # RDS connection
cirkelline-system/google-api-key      # Gemini API
cirkelline-system/jwt-secret-key      # JWT signing
cirkelline-system/exa-api-key         # Exa search
cirkelline-system/tavily-api-key      # Tavily search
```

### Common Commands

```bash
# View localhost environment
cat .env

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# Test database connection
psql "$DATABASE_URL" -c "SELECT 1;"

# Update AWS secret
aws secretsmanager update-secret \
    --secret-id cirkelline-system/google-api-key \
    --secret-string "new_key" \
    --region eu-north-1

# Force ECS deployment
aws ecs update-service \
    --cluster cirkelline-system-cluster \
    --service cirkelline-system-backend-service \
    --force-new-deployment \
    --region eu-north-1
```

---

**See Also:**
- [03-AWS-DEPLOYMENT.md](./03-AWS-DEPLOYMENT.md) - AWS deployment guide
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend reference
- [07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md) - Development guide
