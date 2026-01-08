#!/bin/bash
#
# CIRKELLINE BLUE-GREEN DEPLOYMENT SCRIPT
# =======================================
# Zero-downtime deployment med CodeDeploy
#
# Brug: ./deploy_blue_green.sh [version] [--canary|--linear|--all-at-once]
# Eksempel: ./deploy_blue_green.sh v1.3.5 --canary
#
# FORUDSÆTNINGER:
# - CodeDeploy application konfigureret
# - Green target group oprettet
# - IAM Role for CodeDeploy
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
CODEDEPLOY_APP="cirkelline-system"
CODEDEPLOY_GROUP="production"
PROJECT_ROOT="/home/rasmus/Desktop/projekts/projects/cirkelline-system"

# Parse arguments
VERSION=${1:-"v1.3.5"}
DEPLOYMENT_TYPE=${2:-"--linear"}

# Map deployment type to CodeDeploy config
case $DEPLOYMENT_TYPE in
    --canary)
        DEPLOYMENT_CONFIG="CodeDeployDefault.ECSCanary10Percent5Minutes"
        DEPLOY_DESC="Canary: 10% -> 5 min -> 100%"
        ;;
    --linear)
        DEPLOYMENT_CONFIG="CodeDeployDefault.ECSLinear10PercentEvery1Minutes"
        DEPLOY_DESC="Linear: 10% every minute"
        ;;
    --all-at-once)
        DEPLOYMENT_CONFIG="CodeDeployDefault.ECSAllAtOnce"
        DEPLOY_DESC="All at once (use with caution)"
        ;;
    *)
        DEPLOYMENT_CONFIG="CodeDeployDefault.ECSLinear10PercentEvery1Minutes"
        DEPLOY_DESC="Linear: 10% every minute"
        ;;
esac

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║           CIRKELLINE BLUE-GREEN DEPLOYMENT                                ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Version:    $VERSION                                                         ║"
echo "║  Strategy:   $DEPLOY_DESC"
echo "║  Region:     $AWS_REGION                                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}▶️ CHECKING PREREQUISITES${NC}"
    echo "------------------------------------------------------------------------"

    # Check CodeDeploy application
    echo "Checking CodeDeploy application..."
    CODEDEPLOY_STATUS=$(aws deploy get-application \
        --application-name $CODEDEPLOY_APP \
        --region $AWS_REGION 2>/dev/null || echo "NOT_FOUND")

    if [[ "$CODEDEPLOY_STATUS" == "NOT_FOUND" ]]; then
        echo -e "${RED}❌ CodeDeploy application not configured!${NC}"
        echo "   Run AWS setup first. See BLUE-GREEN-DEPLOYMENT-GUIDE.md"
        exit 1
    fi
    echo -e "${GREEN}✅ CodeDeploy application exists${NC}"

    # Check deployment group
    echo "Checking deployment group..."
    DEPLOYMENT_GROUP=$(aws deploy get-deployment-group \
        --application-name $CODEDEPLOY_APP \
        --deployment-group-name $CODEDEPLOY_GROUP \
        --region $AWS_REGION 2>/dev/null || echo "NOT_FOUND")

    if [[ "$DEPLOYMENT_GROUP" == "NOT_FOUND" ]]; then
        echo -e "${RED}❌ Deployment group not configured!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Deployment group exists${NC}"

    echo ""
}

# Build and push Docker image
build_and_push() {
    echo -e "${YELLOW}▶️ BUILD AND PUSH DOCKER IMAGE${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT
    IMAGE_URI="$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$VERSION"

    echo "Building Docker image..."
    docker build --platform linux/amd64 -f Dockerfile -t $IMAGE_URI .

    echo "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

    echo "Pushing to ECR..."
    docker push $IMAGE_URI

    echo -e "${GREEN}✅ Image pushed: $IMAGE_URI${NC}"
    echo ""
}

# Register new task definition
register_task_definition() {
    echo -e "${YELLOW}▶️ REGISTER TASK DEFINITION${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT/aws_deployment

    # Update image version
    cp task-definition.json task-definition.json.backup
    sed -i.bak "s|$ECR_REPO:v[0-9.]*|$ECR_REPO:$VERSION|g" task-definition.json
    rm -f task-definition.json.bak

    TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json file://task-definition.json \
        --region $AWS_REGION \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

    echo -e "${GREEN}✅ Task definition: $TASK_DEF_ARN${NC}"
    echo ""

    export TASK_DEF_ARN
}

# Create appspec for CodeDeploy
create_appspec() {
    echo -e "${YELLOW}▶️ CREATE APPSPEC${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT/aws_deployment

    cat > appspec.json << EOF
{
    "version": 0.0,
    "Resources": [
        {
            "TargetService": {
                "Type": "AWS::ECS::Service",
                "Properties": {
                    "TaskDefinition": "$TASK_DEF_ARN",
                    "LoadBalancerInfo": {
                        "ContainerName": "cirkelline-backend",
                        "ContainerPort": 7777
                    },
                    "PlatformVersion": "LATEST"
                }
            }
        }
    ]
}
EOF

    echo -e "${GREEN}✅ AppSpec created${NC}"
    echo ""
}

# Deploy with CodeDeploy
deploy_blue_green() {
    echo -e "${YELLOW}▶️ DEPLOY WITH CODEDEPLOY${NC}"
    echo "------------------------------------------------------------------------"

    cd $PROJECT_ROOT/aws_deployment

    # Create deployment
    DEPLOYMENT_ID=$(aws deploy create-deployment \
        --application-name $CODEDEPLOY_APP \
        --deployment-group-name $CODEDEPLOY_GROUP \
        --deployment-config-name $DEPLOYMENT_CONFIG \
        --description "Blue-Green deployment $VERSION" \
        --revision revisionType=AppSpecContent,appSpecContent={content="$(cat appspec.json | jq -c .)"} \
        --region $AWS_REGION \
        --query 'deploymentId' \
        --output text)

    echo -e "${GREEN}Deployment started: $DEPLOYMENT_ID${NC}"
    echo ""

    # Monitor deployment
    echo "Monitoring deployment progress..."
    while true; do
        STATUS=$(aws deploy get-deployment \
            --deployment-id $DEPLOYMENT_ID \
            --region $AWS_REGION \
            --query 'deploymentInfo.status' \
            --output text)

        OVERVIEW=$(aws deploy get-deployment \
            --deployment-id $DEPLOYMENT_ID \
            --region $AWS_REGION \
            --query 'deploymentInfo.deploymentOverview' \
            --output json 2>/dev/null || echo "{}")

        PENDING=$(echo $OVERVIEW | jq -r '.Pending // 0')
        IN_PROGRESS=$(echo $OVERVIEW | jq -r '.InProgress // 0')
        SUCCEEDED=$(echo $OVERVIEW | jq -r '.Succeeded // 0')
        FAILED=$(echo $OVERVIEW | jq -r '.Failed // 0')

        echo -e "   [$(date +%H:%M:%S)] Status: $STATUS | Pending: $PENDING | InProgress: $IN_PROGRESS | Success: $SUCCEEDED | Failed: $FAILED"

        case $STATUS in
            "Succeeded")
                echo -e "${GREEN}✅ Deployment SUCCEEDED!${NC}"
                break
                ;;
            "Failed"|"Stopped")
                echo -e "${RED}❌ Deployment FAILED!${NC}"
                echo "Check logs: aws deploy get-deployment --deployment-id $DEPLOYMENT_ID --region $AWS_REGION"
                exit 1
                ;;
            *)
                sleep 15
                ;;
        esac
    done

    echo ""
}

# Post-deployment verification
verify_deployment() {
    echo -e "${YELLOW}▶️ POST-DEPLOYMENT VERIFICATION${NC}"
    echo "------------------------------------------------------------------------"

    echo "Waiting for load balancer to stabilize..."
    sleep 10

    # Health check
    for i in {1..5}; do
        HEALTH=$(curl -s https://api.cirkelline.com/health 2>/dev/null || echo "PENDING")
        if [[ "$HEALTH" == *"healthy"* ]]; then
            echo -e "${GREEN}✅ Health check: PASSED${NC}"
            break
        else
            echo "   Retry health check... ($i/5)"
            sleep 5
        fi
    done

    # Version check
    CONFIG=$(curl -s https://api.cirkelline.com/config 2>/dev/null | jq -r '.version // "unknown"')
    echo "   Deployed version: $CONFIG"

    echo ""
}

# Main execution
main() {
    echo ""
    echo "Starting Blue-Green Deployment..."
    echo ""

    # Prerequisites (will fail if CodeDeploy not configured)
    check_prerequisites

    # Confirm
    read -p "$(echo -e ${YELLOW}Continue with deployment? [y/N]: ${NC})" response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi

    build_and_push
    register_task_definition
    create_appspec
    deploy_blue_green
    verify_deployment

    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║           BLUE-GREEN DEPLOYMENT COMPLETE                                  ║"
    echo "╠═══════════════════════════════════════════════════════════════════════════╣"
    echo "║  Version:    $VERSION                                                         ║"
    echo "║  Strategy:   $DEPLOY_DESC"
    echo "║  Status:     SUCCESS                                                      ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Run
main "$@"
