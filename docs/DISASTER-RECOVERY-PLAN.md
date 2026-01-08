# CIRKELLINE DISASTER RECOVERY PLAN

**Dato:** 2025-12-14
**Version:** 1.0.0
**Status:** DOKUMENTERET
**Mål:** RTO < 15 min, RPO < 5 min

---

## VEJLEDENDE PRINCIP

> *"Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."*

---

## EXECUTIVE SUMMARY

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    DISASTER RECOVERY TARGETS                               ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  RTO (Recovery Time Objective):     < 15 minutter                         ║
║  RPO (Recovery Point Objective):    < 5 minutter                          ║
║                                                                            ║
║  STRATEGI:                                                                 ║
║  ├── Multi-AZ deployment (eu-north-1a, 1b, 1c)                            ║
║  ├── Database: RDS Multi-AZ + Read Replicas                               ║
║  ├── Cache: Redis cluster med automatic failover                          ║
║  ├── Compute: ECS Auto-scaling (3-100 tasks)                              ║
║  ├── CDN: CloudFront global edge caching                                  ║
║  └── Backup: Automated daily + continuous WAL                             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. INFRASTRUCTURE ARKITEKTUR

### 1.1 Multi-Region Layout

```
                         ┌─────────────────────────────────────┐
                         │           Route 53 DNS              │
                         │   Healthcheck + Failover Routing    │
                         └──────────────────┬──────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              │                             │                             │
              ▼                             ▼                             ▼
    ┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
    │   eu-north-1a     │       │   eu-north-1b     │       │   eu-north-1c     │
    │   (Primary)       │       │   (Secondary)     │       │   (Tertiary)      │
    │                   │       │                   │       │                   │
    │   ├── ECS Tasks   │       │   ├── ECS Tasks   │       │   ├── ECS Tasks   │
    │   ├── RDS Primary │       │   ├── RDS Replica │       │   ├── RDS Replica │
    │   └── Redis Node  │       │   └── Redis Node  │       │   └── Redis Node  │
    └───────────────────┘       └───────────────────┘       └───────────────────┘
```

### 1.2 Komponenter

| Komponent | Konfiguration | Failover |
|-----------|---------------|----------|
| **Compute** | ECS Fargate, 3 AZs | Automatic (ALB health check) |
| **Database** | RDS PostgreSQL Multi-AZ | Automatic (< 60s) |
| **Cache** | ElastiCache Redis Cluster | Automatic (Sentinel) |
| **CDN** | CloudFront 300+ edge | N/A (global) |
| **Storage** | S3 with versioning | Cross-region replication |

---

## 2. FAILURE SCENARIOS

### 2.1 Single Container Failure

```
SCENARIO: En ECS task crasher
IMPACT:   Minimal (andre tasks overtager)
DETECTION: ALB health check (10s interval)
RECOVERY: Automatic (ECS scheduler starter ny task)
RTO:      < 30 sekunder
```

**Handling:**
1. ALB detecterer unhealthy target
2. Traffic routes til healthy targets
3. ECS scheduler starter ny task
4. Ny task registreres i target group

### 2.2 Availability Zone Failure

```
SCENARIO: Hele AZ (f.eks. eu-north-1a) går ned
IMPACT:   ~33% kapacitet mistet midlertidigt
DETECTION: CloudWatch AZ health metrics
RECOVERY: Automatic redistribution
RTO:      < 2 minutter
```

**Handling:**
1. ALB stop routing til AZ
2. ECS tasks i andre AZs håndterer traffic
3. Auto-scaling øger kapacitet i healthy AZs
4. Database failover til replica i anden AZ

### 2.3 Database Primary Failure

```
SCENARIO: RDS Primary instans fejler
IMPACT:   Writes blokeret midlertidigt
DETECTION: RDS automated monitoring
RECOVERY: Automatic Multi-AZ failover
RTO:      < 60 sekunder
```

**Handling:**
1. RDS detecterer primary failure
2. Standby promoveres til primary
3. DNS endpoint opdateres automatisk
4. Applikation reconnect til ny primary

### 2.4 Redis Cluster Node Failure

```
SCENARIO: En Redis shard master fejler
IMPACT:   ~33% cache misses midlertidigt
DETECTION: Redis Sentinel
RECOVERY: Automatic replica promotion
RTO:      < 15 sekunder
```

**Handling:**
1. Sentinel detecterer master failure
2. Replica promoveres til master
3. Cluster rebalancerer automatisk
4. Application reconnect transparent

### 2.5 Complete Region Failure

```
SCENARIO: Hele eu-north-1 region går ned
IMPACT:   Fuld service outage
DETECTION: Route 53 health checks
RECOVERY: Manual failover til backup region
RTO:      < 30 minutter (med DR region)
```

**Handling:**
1. Route 53 detecterer region failure
2. DNS failover til backup region (eu-west-1)
3. DR infrastructure aktiveres
4. Database restore fra seneste backup

---

## 3. BACKUP STRATEGI

### 3.1 Database Backups

```python
# Backup konfiguration
BACKUP_CONFIG = {
    "automated_backups": {
        "retention_days": 35,
        "backup_window": "02:00-03:00",  # UTC
        "copy_tags_to_snapshot": True
    },
    "wal_archiving": {
        "enabled": True,
        "destination": "s3://cirkelline-wal-archive/",
        "retention": "7 days"
    },
    "manual_snapshots": {
        "frequency": "weekly",
        "retention": "90 days",
        "cross_region_copy": True,
        "target_region": "eu-west-1"
    }
}
```

### 3.2 Backup Schedule

| Type | Frekvens | Retention | Lokation |
|------|----------|-----------|----------|
| Automated | Daglig 02:00 UTC | 35 dage | eu-north-1 |
| WAL Archive | Continuous | 7 dage | S3 |
| Weekly Snapshot | Søndag 03:00 UTC | 90 dage | eu-north-1 + eu-west-1 |
| Pre-deployment | Før hver deploy | 7 dage | eu-north-1 |

### 3.3 S3 Backup

```bash
# Static assets backup
aws s3 sync s3://cirkelline-static/ s3://cirkelline-backup-eu-west-1/ \
  --source-region eu-north-1 \
  --region eu-west-1

# Knowledge base vectors backup
pg_dump -h cirkelline-primary.rds.amazonaws.com \
  -U cirkelline -d cirkelline \
  -t ai.cirkelline_knowledge_vectors \
  | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 4. RECOVERY PROCEDURES

### 4.1 Database Recovery

```bash
#!/bin/bash
# database_recovery.sh

# 1. Stop application writes
aws ecs update-service --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --desired-count 0

# 2. Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cirkelline-restored \
  --db-snapshot-identifier rds:cirkelline-primary-2025-12-14-02-00 \
  --db-instance-class db.r6g.2xlarge \
  --availability-zone eu-north-1a

# 3. Wait for restoration
aws rds wait db-instance-available \
  --db-instance-identifier cirkelline-restored

# 4. Promote read replica (if using replica)
aws rds promote-read-replica \
  --db-instance-identifier cirkelline-read-1

# 5. Update connection string in Secrets Manager
aws secretsmanager update-secret \
  --secret-id cirkelline-system/database-url \
  --secret-string "postgresql://cirkelline:xxx@cirkelline-restored.rds.amazonaws.com:5432/cirkelline"

# 6. Restart application
aws ecs update-service --cluster cirkelline-system-cluster \
  --service cirkelline-system-backend-service \
  --desired-count 3
```

### 4.2 Point-in-Time Recovery

```bash
#!/bin/bash
# point_in_time_recovery.sh

TARGET_TIME="2025-12-14T10:30:00Z"

aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier cirkelline-primary \
  --target-db-instance-identifier cirkelline-pitr-restore \
  --restore-time $TARGET_TIME \
  --db-instance-class db.r6g.2xlarge \
  --availability-zone eu-north-1a \
  --multi-az
```

### 4.3 Redis Recovery

```bash
#!/bin/bash
# redis_recovery.sh

# 1. Check cluster status
aws elasticache describe-replication-groups \
  --replication-group-id cirkelline-redis

# 2. Manual failover if needed
aws elasticache modify-replication-group \
  --replication-group-id cirkelline-redis \
  --primary-cluster-id cirkelline-redis-002 \
  --apply-immediately

# 3. Restore from backup if cluster corrupt
aws elasticache create-replication-group \
  --replication-group-id cirkelline-redis-restored \
  --replication-group-description "Restored cluster" \
  --snapshot-name cirkelline-redis-backup-20251214
```

---

## 5. MONITORING & ALERTING

### 5.1 CloudWatch Alarms

```terraform
# terraform/monitoring.tf

resource "aws_cloudwatch_metric_alarm" "database_cpu_high" {
  alarm_name          = "cirkelline-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = "cirkelline-primary"
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_count_low" {
  alarm_name          = "cirkelline-task-count-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = 2
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = "cirkelline-system-cluster"
    ServiceName = "cirkelline-system-backend-service"
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_high" {
  alarm_name          = "cirkelline-5xx-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 100
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.api.arn_suffix
  }
}
```

### 5.2 Alert Channels

| Severity | Channel | Response Time |
|----------|---------|---------------|
| CRITICAL | SMS + Slack + Email | < 5 min |
| HIGH | Slack + Email | < 15 min |
| MEDIUM | Email | < 1 hour |
| LOW | Dashboard only | Next business day |

### 5.3 Health Checks

```python
# health_check_endpoints.py

HEALTH_CHECKS = {
    "api": {
        "url": "https://api.cirkelline.com/health",
        "interval": "10s",
        "timeout": "5s",
        "healthy_threshold": 2,
        "unhealthy_threshold": 3
    },
    "database": {
        "query": "SELECT 1",
        "interval": "30s",
        "timeout": "10s"
    },
    "redis": {
        "command": "PING",
        "interval": "10s",
        "timeout": "3s"
    }
}
```

---

## 6. DR TESTING

### 6.1 Test Schedule

| Test Type | Frekvens | Varighed | Ansvarlig |
|-----------|----------|----------|-----------|
| Failover drill | Månedlig | 2 timer | DevOps |
| Backup restore | Ugentlig | 1 time | DBA |
| Full DR exercise | Kvartalsvis | 4 timer | Team |
| Chaos engineering | Ugentlig | 30 min | DevOps |

### 6.2 Failover Drill Script

```bash
#!/bin/bash
# failover_drill.sh

echo "=== STARTING FAILOVER DRILL ==="
START_TIME=$(date +%s)

# 1. Simulate primary database failure
echo "[1/5] Simulating database failover..."
aws rds reboot-db-instance \
  --db-instance-identifier cirkelline-primary \
  --force-failover

# 2. Monitor recovery
echo "[2/5] Monitoring recovery..."
aws rds wait db-instance-available \
  --db-instance-identifier cirkelline-primary

# 3. Verify application health
echo "[3/5] Verifying application health..."
for i in {1..10}; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.cirkelline.com/health)
  if [ "$HTTP_CODE" == "200" ]; then
    echo "Health check passed"
    break
  fi
  sleep 5
done

# 4. Check data integrity
echo "[4/5] Checking data integrity..."
# Run integrity checks...

# 5. Calculate recovery time
END_TIME=$(date +%s)
RECOVERY_TIME=$((END_TIME - START_TIME))
echo "[5/5] Recovery completed in ${RECOVERY_TIME} seconds"

echo "=== FAILOVER DRILL COMPLETE ==="
```

---

## 7. RUNBOOK: INCIDENT RESPONSE

### 7.1 Incident Classification

| Level | Definition | Example | Response |
|-------|------------|---------|----------|
| P1 | Complete outage | All users affected | Immediate (24/7) |
| P2 | Major degradation | >50% users affected | < 15 min |
| P3 | Minor degradation | <50% users affected | < 1 hour |
| P4 | Non-urgent | Monitoring alert | Next business day |

### 7.2 Incident Response Steps

```
╔════════════════════════════════════════════════════════════════════════════╗
║                         INCIDENT RESPONSE PROCEDURE                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  [1] DETECT                                                                ║
║      ├── CloudWatch alarm trigger                                          ║
║      ├── User reports                                                      ║
║      └── Monitoring dashboard                                              ║
║                                                                            ║
║  [2] ASSESS                                                                ║
║      ├── Determine scope (P1-P4)                                          ║
║      ├── Identify affected components                                      ║
║      └── Notify stakeholders                                               ║
║                                                                            ║
║  [3] CONTAIN                                                               ║
║      ├── Isolate affected systems                                          ║
║      ├── Enable maintenance mode if needed                                 ║
║      └── Redirect traffic if possible                                      ║
║                                                                            ║
║  [4] RECOVER                                                               ║
║      ├── Execute recovery runbook                                          ║
║      ├── Verify system health                                              ║
║      └── Restore normal operations                                         ║
║                                                                            ║
║  [5] POST-MORTEM                                                           ║
║      ├── Document timeline                                                 ║
║      ├── Identify root cause                                               ║
║      └── Define prevention measures                                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. KONTAKTER

### 8.1 Escalation Path

| Role | Contact | Availability |
|------|---------|--------------|
| On-call DevOps | PagerDuty rotation | 24/7 |
| Backend Lead | Slack @backend-lead | Business hours |
| Super Admin | Rasmus | 24/7 (P1 only) |
| AWS Support | Enterprise support | 24/7 |

### 8.2 External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| AWS Support | Case portal | Infrastructure issues |
| Anthropic | support@anthropic.com | AI model issues |
| Google Cloud | Support console | Gemini API issues |

---

## 9. DOKUMENTATION LINKS

- [AWS RDS Disaster Recovery](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/disaster-recovery.html)
- [ECS Service Auto Recovery](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html)
- [ElastiCache Failover](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/AutoFailover.html)
- [CloudFront Origin Failover](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html)

---

*DISASTER-RECOVERY-PLAN v1.0.0*
*Cirkelline System*
*Opdateret: 2025-12-14*
