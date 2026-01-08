#!/bin/bash

source /home/eenvy/Desktop/cirkelline/deployment_vars.env

echo "=== Retrieving Secret ARNs ==="
echo ""

DATABASE_URL_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id cirkelline-system/database-url \
    --region $AWS_REGION \
    --query ARN \
    --output text)

GOOGLE_API_KEY_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id cirkelline-system/google-api-key \
    --region $AWS_REGION \
    --query ARN \
    --output text)

JWT_SECRET_KEY_SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id cirkelline-system/jwt-secret-key \
    --region $AWS_REGION \
    --query ARN \
    --output text)

# Save to deployment vars
cat >> /home/eenvy/Desktop/cirkelline/deployment_vars.env << EOF

# Secret ARNs
export DATABASE_URL_SECRET_ARN="$DATABASE_URL_SECRET_ARN"
export GOOGLE_API_KEY_SECRET_ARN="$GOOGLE_API_KEY_SECRET_ARN"
export JWT_SECRET_KEY_SECRET_ARN="$JWT_SECRET_KEY_SECRET_ARN"
EOF

echo "✅ Secret ARNs saved to deployment_vars.env"
echo ""
echo "Database URL Secret ARN: $DATABASE_URL_SECRET_ARN"
echo "Google API Key Secret ARN: $GOOGLE_API_KEY_SECRET_ARN"
echo "JWT Secret Key Secret ARN: $JWT_SECRET_KEY_SECRET_ARN"
