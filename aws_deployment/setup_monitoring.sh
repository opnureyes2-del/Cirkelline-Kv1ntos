#!/bin/bash
#
# CIRKELLINE MONITORING SETUP SCRIPT
# ==================================
# Opretter CloudWatch alarms og dashboard
#
# Brug: ./setup_monitoring.sh [--alarms|--dashboard|--all]
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
SNS_TOPIC_NAME="cirkelline-alerts"
DASHBOARD_NAME="Cirkelline-System"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║           CIRKELLINE MONITORING SETUP                                     ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Region:     $AWS_REGION                                                ║"
echo "║  Account:    $AWS_ACCOUNT                                             ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse argument
ACTION=${1:-"--all"}

# Funktion: Opret SNS Topic
setup_sns_topic() {
    echo -e "${YELLOW}▶️ SETUP SNS TOPIC${NC}"
    echo "------------------------------------------------------------------------"

    # Check if topic exists
    TOPIC_ARN=$(aws sns list-topics --region $AWS_REGION --query "Topics[?contains(TopicArn, '$SNS_TOPIC_NAME')].TopicArn" --output text 2>/dev/null)

    if [ -z "$TOPIC_ARN" ]; then
        echo "Creating SNS topic..."
        TOPIC_ARN=$(aws sns create-topic --name $SNS_TOPIC_NAME --region $AWS_REGION --query 'TopicArn' --output text)
        echo -e "${GREEN}✅ SNS topic created: $TOPIC_ARN${NC}"
    else
        echo -e "${GREEN}✅ SNS topic exists: $TOPIC_ARN${NC}"
    fi

    # Check subscriptions
    SUB_COUNT=$(aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN --region $AWS_REGION --query 'Subscriptions | length(@)' --output text 2>/dev/null || echo "0")

    if [ "$SUB_COUNT" == "0" ]; then
        echo -e "${YELLOW}⚠️  No email subscriptions configured${NC}"
        echo "   To add email alerts, run:"
        echo "   aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint your@email.com --region $AWS_REGION"
    else
        echo -e "${GREEN}✅ $SUB_COUNT subscription(s) configured${NC}"
    fi

    echo ""
    export SNS_TOPIC_ARN=$TOPIC_ARN
}

# Funktion: Opret CloudWatch Alarms
setup_alarms() {
    echo -e "${YELLOW}▶️ SETUP CLOUDWATCH ALARMS${NC}"
    echo "------------------------------------------------------------------------"

    # ECS CPU Alarm
    echo "Creating ECS CPU alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-ecs-cpu-high" \
        --alarm-description "ECS CPU utilization > 80%" \
        --metric-name CPUUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --evaluation-periods 2 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --dimensions Name=ClusterName,Value=cirkelline-system-cluster Name=ServiceName,Value=cirkelline-system-backend-service \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-ecs-cpu-high${NC}" || echo -e "${RED}❌ cirkelline-ecs-cpu-high${NC}"

    # ECS Memory Alarm
    echo "Creating ECS Memory alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-ecs-memory-high" \
        --alarm-description "ECS Memory utilization > 80%" \
        --metric-name MemoryUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --evaluation-periods 2 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --dimensions Name=ClusterName,Value=cirkelline-system-cluster Name=ServiceName,Value=cirkelline-system-backend-service \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-ecs-memory-high${NC}" || echo -e "${RED}❌ cirkelline-ecs-memory-high${NC}"

    # ALB 5XX Alarm
    echo "Creating ALB 5XX alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-alb-5xx-errors" \
        --alarm-description "ALB 5XX errors > 10 in 5 minutes" \
        --metric-name HTTPCode_Target_5XX_Count \
        --namespace AWS/ApplicationELB \
        --statistic Sum \
        --period 300 \
        --evaluation-periods 1 \
        --threshold 10 \
        --comparison-operator GreaterThanThreshold \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-alb-5xx-errors${NC}" || echo -e "${RED}❌ cirkelline-alb-5xx-errors (may need LoadBalancer dimension)${NC}"

    # ALB Latency Alarm
    echo "Creating ALB Latency alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-alb-latency-high" \
        --alarm-description "ALB response time > 2 seconds" \
        --metric-name TargetResponseTime \
        --namespace AWS/ApplicationELB \
        --statistic Average \
        --period 300 \
        --evaluation-periods 2 \
        --threshold 2 \
        --comparison-operator GreaterThanThreshold \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-alb-latency-high${NC}" || echo -e "${RED}❌ cirkelline-alb-latency-high (may need LoadBalancer dimension)${NC}"

    # RDS CPU Alarm
    echo "Creating RDS CPU alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-rds-cpu-high" \
        --alarm-description "RDS CPU > 80%" \
        --metric-name CPUUtilization \
        --namespace AWS/RDS \
        --statistic Average \
        --period 300 \
        --evaluation-periods 2 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --dimensions Name=DBInstanceIdentifier,Value=cirkelline-system-db \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-rds-cpu-high${NC}" || echo -e "${RED}❌ cirkelline-rds-cpu-high${NC}"

    # RDS Storage Alarm
    echo "Creating RDS Storage alarm..."
    aws cloudwatch put-metric-alarm \
        --alarm-name "cirkelline-rds-storage-low" \
        --alarm-description "RDS free storage < 5GB" \
        --metric-name FreeStorageSpace \
        --namespace AWS/RDS \
        --statistic Average \
        --period 300 \
        --evaluation-periods 1 \
        --threshold 5368709120 \
        --comparison-operator LessThanThreshold \
        --dimensions Name=DBInstanceIdentifier,Value=cirkelline-system-db \
        --alarm-actions $SNS_TOPIC_ARN \
        --treat-missing-data notBreaching \
        --region $AWS_REGION 2>/dev/null && echo -e "${GREEN}✅ cirkelline-rds-storage-low${NC}" || echo -e "${RED}❌ cirkelline-rds-storage-low${NC}"

    echo ""
    echo -e "${GREEN}✅ Alarms setup complete${NC}"
    echo ""
}

# Funktion: Opret CloudWatch Dashboard
setup_dashboard() {
    echo -e "${YELLOW}▶️ SETUP CLOUDWATCH DASHBOARD${NC}"
    echo "------------------------------------------------------------------------"

    # Check if dashboard JSON exists
    DASHBOARD_FILE="$SCRIPT_DIR/cloudwatch-dashboard.json"

    if [ ! -f "$DASHBOARD_FILE" ]; then
        echo -e "${RED}❌ Dashboard file not found: $DASHBOARD_FILE${NC}"
        return 1
    fi

    # Read dashboard body
    DASHBOARD_BODY=$(cat "$DASHBOARD_FILE")

    echo "Creating dashboard: $DASHBOARD_NAME..."
    aws cloudwatch put-dashboard \
        --dashboard-name "$DASHBOARD_NAME" \
        --dashboard-body "$DASHBOARD_BODY" \
        --region $AWS_REGION 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Dashboard created: $DASHBOARD_NAME${NC}"
        echo "   View at: https://$AWS_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=$DASHBOARD_NAME"
    else
        echo -e "${RED}❌ Dashboard creation failed${NC}"
    fi

    echo ""
}

# Funktion: Vis status
show_status() {
    echo -e "${YELLOW}▶️ MONITORING STATUS${NC}"
    echo "------------------------------------------------------------------------"

    # List alarms
    echo "CloudWatch Alarms:"
    aws cloudwatch describe-alarms \
        --alarm-name-prefix "cirkelline" \
        --region $AWS_REGION \
        --query 'MetricAlarms[].{Name:AlarmName,State:StateValue}' \
        --output table 2>/dev/null || echo "  No alarms found"

    echo ""

    # List dashboards
    echo "CloudWatch Dashboards:"
    aws cloudwatch list-dashboards \
        --dashboard-name-prefix "Cirkelline" \
        --region $AWS_REGION \
        --query 'DashboardEntries[].DashboardName' \
        --output table 2>/dev/null || echo "  No dashboards found"

    echo ""
}

# Main
main() {
    case $ACTION in
        --alarms)
            setup_sns_topic
            setup_alarms
            ;;
        --dashboard)
            setup_dashboard
            ;;
        --status)
            show_status
            ;;
        --all)
            setup_sns_topic
            setup_alarms
            setup_dashboard
            show_status
            ;;
        *)
            echo "Usage: $0 [--alarms|--dashboard|--status|--all]"
            exit 1
            ;;
    esac

    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║           MONITORING SETUP COMPLETE                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo ""
    echo -e "${YELLOW}Quick Commands:${NC}"
    echo "  Alarms:     aws cloudwatch describe-alarms --alarm-name-prefix cirkelline --region $AWS_REGION"
    echo "  Dashboard:  https://$AWS_REGION.console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=$DASHBOARD_NAME"
    echo "  Logs:       aws logs tail /ecs/cirkelline-system-backend --since 5m --region $AWS_REGION"
    echo ""
}

main
