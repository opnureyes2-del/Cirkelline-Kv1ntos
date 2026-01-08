# AWS DEPLOYMENT GUIDE

**Last Updated:** 2025-11-30
**Current Version:** v1.2.33
**Region:** eu-north-1 (Stockholm)

**Latest Deployment (v1.2.33):**
- **Type:** Backend + Frontend (UI improvements, mobile fixes)
- **Changes:** TopBar overhaul, mobile sessions fix, Support Us ribbon, version corrections
- **Infrastructure:** No changes required
- **Database:** No schema changes
- **Environment Variables:** No changes

## 🔴 CRITICAL PRE-DEPLOYMENT CHECKLIST

**BEFORE EVERY DEPLOYMENT, VERIFY:**

### 1. ✅ Verify Dockerfile Location and Contents
```bash
# YOU MUST USE THIS EXACT DOCKERFILE:
/home/eenvy/Desktop/cirkelline/Dockerfile

# VERIFY curl is installed (line 12):
grep -n "curl" ~/Desktop/cirkelline/Dockerfile

# Expected output:
#    12:    curl \
```

**NEVER use any other Dockerfile! This is the ONLY correct one for AWS deployments!**

### 2. ✅ Verify Docker Build Command
```bash
# YOU MUST BUILD FROM PROJECT ROOT:
cd ~/Desktop/cirkelline

# YOU MUST USE THIS EXACT COMMAND:
docker build --platform linux/amd64 \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.XX \
  -f Dockerfile .
#  ^^^^^^^^^^^^^ EXPLICITLY specify Dockerfile!

# DO NOT build from any other directory!
# DO NOT use a different Dockerfile!
# DO NOT omit the -f Dockerfile flag!
```

### 3. ✅ Verify task-definition.json Location
```bash
# YOU MUST USE THIS EXACT FILE:
/home/eenvy/Desktop/cirkelline/aws_deployment/task-definition.json

# VERIFY the image version on line 12:
grep -n "image" ~/Desktop/cirkelline/aws_deployment/task-definition.json

# Expected format:
#    12:      "image": "710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.XX",
```

---

## ⚠️ CRITICAL DEPLOYMENT REQUIREMENTS

### Docker Image Requirements
**MUST HAVE** `curl` installed in the Docker image for ECS health checks to work!

**Location:** `/home/eenvy/Desktop/cirkelline/Dockerfile`

```dockerfile
# Line 12 - REQUIRED system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \  # ← CRITICAL: Required for ECS health checks!
    && rm -rf /var/lib/apt/lists/*
```

**Why:** ECS task definition health check runs INSIDE the Docker container and checks `curl -f http://localhost:7777/config` (localhost from the container's perspective). If curl is not installed, all deployments will fail with "failed container health checks" errors.

**IMPORTANT:** `localhost:7777` in health checks is CORRECT - it's the INTERNAL check inside the container, NOT a public URL!

**Historical Note:** v1.1.21 deployment failed because the wrong Dockerfile was used (one without curl). Always verify you're using `/home/eenvy/Desktop/cirkelline/Dockerfile`!

### Health Check Configuration
- **ECS internal health check:** `curl -f http://localhost:7777/config || exit 1` (runs INSIDE container - line 70 in task-definition.json)
- **Dockerfile health check:** Python requests `http://localhost:7777/config` (line 29 in Dockerfile - for local Docker testing)
- **Production external URL:** `https://api.cirkelline.com` (for testing from outside AWS)

**NOTE:** localhost:7777 is ONLY for internal container health checks, NOT for external access!

---

## Current AWS Infrastructure

### Account Details
- **AWS Account ID:** 710504360116
- **Region:** eu-north-1
- **IAM User:** eenvy

### Production URLs
- **Backend ALB:** `cirkelline-system-backend-alb-1810847627.eu-north-1.elb.amazonaws.com`
- **Health Check:** `http://<alb-dns>/config`
- **Frontend:** Deployed on Vercel

---

## AWS Resources

### ECS (Elastic Container Service)
```
Cluster: cirkelline-system-cluster
Service: cirkelline-system-backend-service
Task Definition: cirkelline-system-backend (current: revision 73)
Launch Type: FARGATE
Platform: LINUX/X86_64
CPU: 2048 (2 vCPU)
Memory: 4096 MB (4 GB)
Desired Count: 2 tasks
Auto-scaling: 2-10 tasks (CPU 70%, Memory 80%)
```

### ECR (Container Registry)
```
Repository: cirkelline-system-backend
URI: 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend
Current Image: v1.2.33
Image Size: ~230MB compressed (~685MB uncompressed)
Note: v1.1.22+ includes curl for health checks (still required for v1.2.33)
```

### RDS (PostgreSQL Database)
```
Instance ID: cirkelline-system-db
Endpoint: cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432
Engine: PostgreSQL 16.10
Instance Class: db.t3.medium
Storage: 20 GB GP2
Database Name: cirkelline_system
Multi-AZ: Yes
Backup Retention: 7 days
```

### Application Load Balancer
```
Name: cirkelline-system-backend-alb
DNS: cirkelline-system-backend-alb-1810847627.eu-north-1.elb.amazonaws.com
Target Group: cirkelline-system-backend-tg
Health Check Path: /config
Health Check Interval: 30s
Health Check Timeout: 5s
Healthy Threshold: 2
Unhealthy Threshold: 3
```

### Secrets Manager
```
Secret 1: cirkelline-system/database-url
  Value: postgresql://postgres:<password>@<endpoint>:5432/cirkelline_system

Secret 2: cirkelline-system/google-api-key
  Value: AIzaSyD07oYF6adWs_HTkSaCYoNPd6nM4T5J57M (Tier 1 - Production Only, Updated 2025-10-31)

Secret 3: cirkelline-system/jwt-secret-key
  Value: <64-char-hex>

Secret 4: cirkelline-system/exa-api-key
  Value: <exa-key>

Secret 5: cirkelline-system/tavily-api-key
  Value: <tavily-key>
```

### Security Groups
```
ECS Tasks: sg-07a6eb96ed423cc27
  Inbound: Port 7777 from ALB
  Outbound: All traffic

ALB: sg-0ce0039efebbcc493
  Inbound: HTTP (80), HTTPS (443) from 0.0.0.0/0
  Outbound: Port 7777 to ECS tasks
```

### VPC Endpoints (CRITICAL for Private Subnets)
```
1. com.amazonaws.eu-north-1.secretsmanager
   Purpose: Access Secrets Manager

2. com.amazonaws.eu-north-1.ecr.api
   Purpose: Pull Docker images

3. com.amazonaws.eu-north-1.ecr.dkr
   Purpose: Docker registry operations

4. com.amazonaws.eu-north-1.s3 (Gateway)
   Purpose: ECR image layers storage
```

---

## Deployment Procedures

### Quick Deploy (Code Changes Only)

**🔴 MANDATORY: Run the Pre-Deployment Checklist above FIRST!**

```bash
# 0. RUN PRE-DEPLOYMENT CHECKLIST (see section above)
# - Verify Dockerfile location and curl is installed
# - Verify build command uses correct Dockerfile
# - Verify task-definition.json location

# 1. Build new image (increment version number)
cd ~/Desktop/cirkelline

# CRITICAL: Use -f Dockerfile to explicitly specify which Dockerfile!
docker build --platform linux/amd64 \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.23 \
  -f Dockerfile .

# 2. Login to ECR
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  710504360116.dkr.ecr.eu-north-1.amazonaws.com

# 3. Push to ECR
docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.23

# Note: If push times out due to network issues, just retry:
# docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.1.23

# 4. Update task-definition.json image version
cd ~/Desktop/cirkelline/aws_deployment
# Edit line 12: "image": "...backend:v1.1.23"

# 5. Register new task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region eu-north-1 \
  --query 'taskDefinition.{family:family,revision:revision,status:status}'

# 6. Update service (use the revision number from step 5)
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:27 \
  --region eu-north-1 \
  --force-new-deployment

# 7. Monitor deployment (wait 2-3 minutes for health checks)
aws ecs describe-services \
  --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service \
  --region eu-north-1 \
  --query 'services[0].deployments[*].{status:status,taskDefinition:taskDefinition,runningCount:runningCount,desiredCount:desiredCount,failedTasks:failedTasks}'

# 8. Check logs for any errors
aws logs tail /ecs/cirkelline-system-backend --since 5m --region eu-north-1

# 9. Verify production is working
curl https://api.cirkelline.com/config
```

**Common Issues:**
- **"failed container health checks"** → curl not installed in Docker image
- **Docker push timeouts** → Network issue, just retry the push command
- **Tasks stuck at 0 running** → Check logs for startup errors

### Database Schema Changes
```bash
# ⚠️ BE CAREFUL - These affect production data!

# 1. Connect to RDS
PGPASSWORD=<password> psql \
  -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
  -p 5432 \
  -U postgres \
  -d cirkelline_system

# 2. Run migration (example)
ALTER TABLE users ADD COLUMN new_field VARCHAR(255);

# 3. Verify
\d users

# 4. Deploy new backend version that uses new_field
```

### Update Secrets
```bash
# Update secret value
aws secretsmanager update-secret \
  --secret-id cirkelline-system/google-api-key \
  --secret-string "new-api-key" \
  --region eu-north-1

# Force ECS to reload secrets (restart tasks)
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --force-new-deployment \
  --region eu-north-1
```

---

## Monitoring & Logs

### View Logs
```bash
# Real-time logs
aws logs tail /ecs/cirkelline-system-backend --follow --region eu-north-1

# Last 5 minutes
aws logs tail /ecs/cirkelline-system-backend --since 5m --region eu-north-1

# Filter for errors
aws logs tail /ecs/cirkelline-system-backend --since 10m --region eu-north-1 | grep ERROR
```

### Check Service Status
```bash
# Service status
aws ecs describe-services \
  --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service \
  --region eu-north-1

# Running tasks
aws ecs list-tasks \
  --cluster cirkelline-system-cluster \
  --service-name cirkelline-system-backend-service \
  --region eu-north-1

# Task details
aws ecs describe-tasks \
  --cluster cirkelline-system-cluster \
  --tasks <task-arn> \
  --region eu-north-1
```

### Health Checks
```bash
# ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-north-1:710504360116:targetgroup/cirkelline-system-backend-tg/c13812ff2159945f \
  --region eu-north-1

# Test endpoint
curl http://cirkelline-system-backend-alb-1810847627.eu-north-1.elb.amazonaws.com/config
```

---

## Rollback Procedure

```bash
# 1. Find previous task definition revision
aws ecs describe-task-definition \
  --task-definition cirkelline-system-backend \
  --region eu-north-1 \
  --query 'taskDefinition.revision'

# Current is revision 23, rollback to 22

# 2. Update service to use previous revision
aws ecs update-service \
  --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --task-definition cirkelline-system-backend:22 \
  --region eu-north-1

# 3. Monitor rollback
aws ecs describe-services \
  --cluster cirkelline-system-cluster \
  --services cirkelline-system-backend-service \
  --region eu-north-1 \
  --query 'services[0].deployments'
```

---

## Cost Breakdown (Monthly Estimate)

| Service | Details | Cost |
|---------|---------|------|
| ECS Fargate | 2 tasks × 2 vCPU × 4GB × 730 hrs | ~$60 |
| RDS (db.t3.medium) | Single instance | ~$50 |
| Application Load Balancer | 1 ALB + data transfer | ~$20 |
| Data Transfer | Internet egress | ~$15 |
| CloudWatch Logs | 7-day retention | ~$5 |
| Secrets Manager | 5 secrets | ~$3 |
| **Total** | | **~$150-185** |

---

## Troubleshooting AWS Issues

See [02-TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md) for detailed solutions:
- ECS tasks can't access Secrets Manager
- ECS tasks can't pull Docker images
- Tasks failing health checks
- Database connection issues

---

## Quick Reference

```bash
# AWS CLI commands
export AWS_DEFAULT_REGION=eu-north-1

# Service status
aws ecs describe-services --cluster cirkelline-system-cluster --services cirkelline-system-backend-service

# Logs
aws logs tail /ecs/cirkelline-system-backend --follow

# Force deployment
aws ecs update-service --cluster cirkelline-system-cluster --service cirkelline-system-backend-service --force-new-deployment

# Database connection
PGPASSWORD=<pass> psql -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com -p 5432 -U postgres -d cirkelline_system
```
