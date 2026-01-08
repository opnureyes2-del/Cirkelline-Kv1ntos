#!/bin/bash

source /home/eenvy/Desktop/cirkelline/deployment_vars.env

echo "=== Creating Secrets in AWS Secrets Manager ==="
echo ""

# Read database password
DB_PASSWORD=$(cat /home/eenvy/Desktop/cirkelline/db_password.txt)

# Secret 1: Database URL
echo "Creating Database URL secret..."
DATABASE_URL="postgresql+psycopg://postgres:${DB_PASSWORD}@${DB_ENDPOINT}:5432/${DB_NAME}"

aws secretsmanager create-secret \
    --name cirkelline-system/database-url \
    --description "PostgreSQL connection string for Cirkelline System" \
    --secret-string "$DATABASE_URL" \
    --region $AWS_REGION 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Secret exists, updating..."
    aws secretsmanager update-secret \
        --secret-id cirkelline-system/database-url \
        --secret-string "$DATABASE_URL" \
        --region $AWS_REGION
fi
echo "✅ Database URL secret ready"

# Secret 2: Google API Key
echo ""
echo "Creating Google API Key secret..."
GOOGLE_API_KEY=$(grep GOOGLE_API_KEY /home/eenvy/Desktop/cirkelline/.env | cut -d '=' -f2)

aws secretsmanager create-secret \
    --name cirkelline-system/google-api-key \
    --description "Google Gemini API key for Cirkelline System" \
    --secret-string "$GOOGLE_API_KEY" \
    --region $AWS_REGION 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Secret exists, updating..."
    aws secretsmanager update-secret \
        --secret-id cirkelline-system/google-api-key \
        --secret-string "$GOOGLE_API_KEY" \
        --region $AWS_REGION
fi
echo "✅ Google API Key secret ready"

# Secret 3: JWT Secret Key
echo ""
echo "Creating JWT Secret Key secret..."
if grep -q JWT_SECRET_KEY /home/eenvy/Desktop/cirkelline/.env; then
    JWT_SECRET_KEY=$(grep JWT_SECRET_KEY /home/eenvy/Desktop/cirkelline/.env | cut -d '=' -f2)
else
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> /home/eenvy/Desktop/cirkelline/.env
fi

aws secretsmanager create-secret \
    --name cirkelline-system/jwt-secret-key \
    --description "JWT secret key for Cirkelline System authentication" \
    --secret-string "$JWT_SECRET_KEY" \
    --region $AWS_REGION 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Secret exists, updating..."
    aws secretsmanager update-secret \
        --secret-id cirkelline-system/jwt-secret-key \
        --secret-string "$JWT_SECRET_KEY" \
        --region $AWS_REGION
fi
echo "✅ JWT Secret Key secret ready"

echo ""
echo "=== All Secrets Created Successfully ==="
