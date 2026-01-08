# BLUE-GREEN DEPLOYMENT GUIDE

**Oprettet:** 2025-12-17
**Agent:** Kommandor #4
**Version:** v1.3.5
**Status:** DOKUMENTERET

---

## OVERSIGT

Blue-Green deployment giver zero-downtime releases via traffic shifting mellem to identiske miljøer.

---

## NUVÆRENDE STATUS

| Komponent | Status | Note |
|-----------|--------|------|
| ECS Cluster | ✅ | cirkelline-system-cluster |
| ECS Service | ✅ | cirkelline-system-backend-service |
| ALB | ✅ | cirkelline-system-alb |
| Target Group (Blue) | ✅ | Eksisterende |
| Target Group (Green) | ❌ | Skal oprettes |
| CodeDeploy | ❌ | Skal konfigureres |

---

## ARKITEKTUR

### Nuværende (Rolling Update)
```
User → ALB → Target Group → ECS Tasks (rolling)
```

### Blue-Green (Målet)
```
User → ALB
        ├── Target Group BLUE  (100% traffic) → ECS Tasks BLUE
        └── Target Group GREEN (0% traffic)   → ECS Tasks GREEN

Ved deployment:
1. Deploy til GREEN
2. Test GREEN (canary 10%)
3. Shift traffic 50/50
4. Shift traffic 100% GREEN
5. GREEN bliver ny BLUE
```

---

## IMPLEMENTERINGSPLAN

### Fase 1: AWS Ressourcer (Manuel/Terraform)

```bash
# 1. Opret Green Target Group
aws elbv2 create-target-group \
  --name cirkelline-backend-green \
  --protocol HTTP \
  --port 7777 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health \
  --region eu-north-1

# 2. Konfigurer ALB Listener Rules
# - Production listener (port 443) → Blue Target Group
# - Test listener (port 8443) → Green Target Group (for testing)

# 3. Opret CodeDeploy Application
aws deploy create-application \
  --application-name cirkelline-system \
  --compute-platform ECS \
  --region eu-north-1

# 4. Opret CodeDeploy Deployment Group
aws deploy create-deployment-group \
  --application-name cirkelline-system \
  --deployment-group-name production \
  --deployment-config-name CodeDeployDefault.ECSLinear10PercentEvery1Minutes \
  --service-role-arn arn:aws:iam::710504360116:role/CodeDeployServiceRole \
  --ecs-services cluster=cirkelline-system-cluster,service=cirkelline-system-backend-service \
  --load-balancer-info targetGroupPairInfoList=[{targetGroups=[{name=cirkelline-backend-blue},{name=cirkelline-backend-green}],prodTrafficRoute={listenerArns=[arn:aws:elasticloadbalancing:eu-north-1:710504360116:listener/app/xxx]}}] \
  --blue-green-deployment-configuration terminateBlueInstancesOnDeploymentSuccess={action=TERMINATE,terminationWaitTimeInMinutes=5},deploymentReadyOption={actionOnTimeout=CONTINUE_DEPLOYMENT,waitTimeInMinutes=0} \
  --region eu-north-1
```

### Fase 2: AppSpec File

```yaml
# appspec.yml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: <TASK_DEFINITION>
        LoadBalancerInfo:
          ContainerName: "cirkelline-backend"
          ContainerPort: 7777
        PlatformVersion: "LATEST"

Hooks:
  - BeforeInstall: "scripts/before_install.sh"
  - AfterInstall: "scripts/after_install.sh"
  - AfterAllowTestTraffic: "scripts/test_traffic.sh"
  - BeforeAllowTraffic: "scripts/before_traffic.sh"
  - AfterAllowTraffic: "scripts/after_traffic.sh"
```

### Fase 3: Deployment Script

Se `deploy_blue_green.sh` for komplet implementation.

---

## ROLLBACK STRATEGI

### Automatisk Rollback
CodeDeploy ruller automatisk tilbage hvis:
- Health check fejler
- CloudWatch Alarm trigger
- Manual stop af deployment

### Manuel Rollback
```bash
aws deploy stop-deployment \
  --deployment-id <deployment-id> \
  --auto-rollback-enabled \
  --region eu-north-1
```

---

## MONITORING

### CloudWatch Alarms (Skal Oprettes)

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| HighErrorRate | 5XXError | > 5% | Rollback |
| HighLatency | TargetResponseTime | > 2s | Alert |
| UnhealthyHosts | UnHealthyHostCount | > 0 | Alert |
| CPUHigh | CPUUtilization | > 80% | Scale |

### Dashboard Metrics
- Request count (blue vs green)
- Error rate per target group
- Latency P50/P95/P99
- Task count per deployment

---

## COST IMPACT

| Resource | Current | With Blue-Green |
|----------|---------|-----------------|
| ECS Tasks | 2-10 | 4-20 (during deploy) |
| Target Groups | 1 | 2 |
| CodeDeploy | $0 | $0 (free tier) |
| ALB | $0.0225/hr | Same |

**Estimated Additional Cost:** ~$10-20/month during deployments

---

## PREREQUISITES CHECKLIST

- [ ] IAM Role for CodeDeploy
- [ ] Second Target Group (Green)
- [ ] ALB Test Listener (port 8443)
- [ ] CodeDeploy Application
- [ ] CodeDeploy Deployment Group
- [ ] appspec.yml i repository
- [ ] CloudWatch Alarms for rollback

---

## NÆSTE STEPS

1. **P2.1:** Opret IAM Role for CodeDeploy
2. **P2.2:** Opret Green Target Group via AWS Console/Terraform
3. **P2.3:** Konfigurer CodeDeploy Application
4. **P2.4:** Test med canary deployment (10%)
5. **P2.5:** Dokumenter og træn team

---

*Opdateret: 2025-12-17*
*Agent: Kommandør #4*
*Status: DOKUMENTERET - KLAR TIL IMPLEMENTATION*
