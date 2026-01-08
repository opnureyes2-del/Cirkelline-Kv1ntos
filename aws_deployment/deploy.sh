#!/bin/bash
#
# CIRKELLINE DEPLOYMENT SCRIPT
# ============================
# Eksekverbar plan for deployment til cirkelline.com
# Deadline: 13. December 2025
#
# Brug: ./deploy.sh [version]
# Eksempel: ./deploy.sh v1.3.4
#

set -e

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Konfiguration
AWS_ACCOUNT="710504360116"
AWS_REGION="eu-north-1"
ECR_REPO="cirkelline-system-backend"
ECS_CLUSTER="cirkelline-system-cluster"
ECS_SERVICE="cirkelline-system-backend-service"
TASK_FAMILY="cirkelline-system-backend"
PROJECT_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"

# Hent version fra argument eller brug default
VERSION=${1:-"v1.3.4"}

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║           CIRKELLINE DEPLOYMENT SCRIPT - D. 13. DECEMBER                  ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Version:    $VERSION                                                         ║"
echo "║  Target:     api.cirkelline.com                                           ║"
echo "║  Region:     $AWS_REGION                                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funktion til at bekræfte handling
confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# TRIN 1: PRE-DEPLOYMENT VALIDERING
echo -e "${YELLOW}▶️ TRIN 1: PRE-DEPLOYMENT VALIDERING${NC}"
echo "------------------------------------------------------------------------"

echo "1.1: Verificerer AWS credentials..."
AWS_IDENTITY=$(aws sts get-caller-identity --region $AWS_REGION 2>/dev/null || echo "FEJL")
if [[ "$AWS_IDENTITY" == "FEJL" ]]; then
    echo -e "${RED}❌ AWS credentials ikke konfigureret!${NC}"
    echo "   Kør: aws configure"
    exit 1
fi
echo -e "${GREEN}✅ AWS Identity: $(echo $AWS_IDENTITY | jq -r '.Arn')${NC}"

echo ""
echo "1.2: Verificerer ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ ECR Repository: $ECR_REPO eksisterer${NC}"
else
    echo -e "${RED}❌ ECR Repository ikke fundet!${NC}"
    exit 1
fi

echo ""
echo "1.3: Verificerer ECS cluster..."
CLUSTER_STATUS=$(aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null)
if [[ "$CLUSTER_STATUS" == "ACTIVE" ]]; then
    echo -e "${GREEN}✅ ECS Cluster: $ECS_CLUSTER er ACTIVE${NC}"
else
    echo -e "${RED}❌ ECS Cluster ikke active! Status: $CLUSTER_STATUS${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ TRIN 1 KOMPLET - Pre-deployment validering bestået${NC}"
echo ""

# TRIN 2: DOCKER BUILD
if confirm "Fortsæt til TRIN 2: Docker Build?"; then
    echo ""
    echo -e "${YELLOW}▶️ TRIN 2: DOCKER IMAGE BUILD${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT

    echo "2.1: Bygger Docker image..."
    IMAGE_URI="$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$VERSION"

    docker build --platform linux/amd64 -f Dockerfile -t $IMAGE_URI .

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker image bygget: $IMAGE_URI${NC}"
    else
        echo -e "${RED}❌ Docker build fejlede!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✅ TRIN 2 KOMPLET - Docker image bygget${NC}"
else
    echo "Afbrudt af bruger."
    exit 0
fi

# TRIN 3: ECR PUSH
if confirm "Fortsæt til TRIN 3: Push til ECR?"; then
    echo ""
    echo -e "${YELLOW}▶️ TRIN 3: PUSH TIL ECR${NC}"
    echo "------------------------------------------------------------------------"

    echo "3.1: Logger ind til ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

    echo ""
    echo "3.2: Pusher image til ECR..."
    docker push $IMAGE_URI

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image pushet til ECR: $IMAGE_URI${NC}"
    else
        echo -e "${RED}❌ ECR push fejlede!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✅ TRIN 3 KOMPLET - Image i ECR${NC}"
else
    echo "Afbrudt af bruger."
    exit 0
fi

# TRIN 4: OPDATER TASK DEFINITION
if confirm "Fortsæt til TRIN 4: Opdater Task Definition?"; then
    echo ""
    echo -e "${YELLOW}▶️ TRIN 4: OPDATER TASK DEFINITION${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT/aws_deployment

    echo "4.1: Opdaterer task-definition.json med version $VERSION..."

    # Backup original
    cp task-definition.json task-definition.json.backup

    # Opdater image version (portable sed)
    sed -i.bak "s|$ECR_REPO:v[0-9.]*|$ECR_REPO:$VERSION|g" task-definition.json
    rm -f task-definition.json.bak

    echo "4.2: Registrerer ny task definition..."
    TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json file://task-definition.json \
        --region $AWS_REGION \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

    REVISION=$(echo $TASK_DEF_ARN | grep -oP ':\d+$' | tr -d ':')

    echo -e "${GREEN}✅ Ny Task Definition registreret: $TASK_FAMILY:$REVISION${NC}"

    echo ""
    echo -e "${GREEN}✅ TRIN 4 KOMPLET - Task Definition opdateret${NC}"
else
    echo "Afbrudt af bruger."
    exit 0
fi

# TRIN 5: DEPLOY TIL ECS
if confirm "Fortsæt til TRIN 5: Deploy til ECS Fargate?"; then
    echo ""
    echo -e "${YELLOW}▶️ TRIN 5: DEPLOY TIL ECS FARGATE${NC}"
    echo "------------------------------------------------------------------------"

    echo "5.1: Opdaterer ECS service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --task-definition $TASK_FAMILY:$REVISION \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null

    echo -e "${GREEN}✅ Deployment initieret${NC}"

    echo ""
    echo "5.2: Venter på deployment (dette kan tage 3-5 minutter)..."

    # Monitorér deployment
    for i in {1..30}; do
        DEPLOYMENT=$(aws ecs describe-services \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE \
            --region $AWS_REGION \
            --query 'services[0].deployments[?status==`PRIMARY`].[runningCount,desiredCount]' \
            --output text)

        RUNNING=$(echo $DEPLOYMENT | awk '{print $1}')
        DESIRED=$(echo $DEPLOYMENT | awk '{print $2}')

        echo -e "   [$(date +%H:%M:%S)] Running: $RUNNING / Desired: $DESIRED"

        if [[ "$RUNNING" == "$DESIRED" ]] && [[ "$RUNNING" != "0" ]]; then
            echo -e "${GREEN}✅ Deployment komplet!${NC}"
            break
        fi

        sleep 10
    done

    echo ""
    echo -e "${GREEN}✅ TRIN 5 KOMPLET - Deployed til ECS${NC}"
else
    echo "Afbrudt af bruger."
    exit 0
fi

# TRIN 6: POST-DEPLOYMENT VERIFIKATION
echo ""
echo -e "${YELLOW}▶️ TRIN 6: POST-DEPLOYMENT VERIFIKATION${NC}"
echo "------------------------------------------------------------------------"

echo "6.1: Verificerer produktion health..."
sleep 5  # Kort pause for load balancer

for i in {1..5}; do
    HEALTH=$(curl -s https://api.cirkelline.com/health 2>/dev/null || echo "PENDING")
    if [[ "$HEALTH" == *"healthy"* ]]; then
        echo -e "${GREEN}✅ api.cirkelline.com/health: HEALTHY${NC}"
        break
    else
        echo "   Venter på health check... ($i/5)"
        sleep 10
    fi
done

echo ""
echo "6.2: Verificerer config endpoint..."
CONFIG=$(curl -s https://api.cirkelline.com/config 2>/dev/null || echo "PENDING")
echo "   Config: $(echo $CONFIG | head -c 100)..."

echo ""
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT KOMPLET - $VERSION                           ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Frontend:   https://cirkelline.com                                       ║"
echo "║  Backend:    https://api.cirkelline.com                                   ║"
echo "║  Health:     https://api.cirkelline.com/health                            ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  Logs:     aws logs tail /ecs/cirkelline-system-backend --since 5m --region $AWS_REGION"
echo "  Status:   aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION"
echo "  Rollback: ./deploy.sh v1.3.3  # (previous version)"
echo ""
