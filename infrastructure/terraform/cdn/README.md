# Cirkelline CDN Infrastructure

CloudFront distribution for edge caching and global content delivery.

## Architecture

```
                    ┌─────────────────────────────┐
                    │        End Users            │
                    │   (Denmark, EU, Global)     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │      CloudFront Edge        │
                    │   (300+ Edge Locations)     │
                    │                             │
                    │   Cache: Static Assets      │
                    │   - JS/CSS bundles          │
                    │   - Images                  │
                    │   - Fonts                   │
                    │   - API responses (selected)│
                    └──────────────┬──────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   S3 Bucket     │     │   ALB Origin    │     │   API Gateway   │
│   (Static)      │     │   (Dynamic)     │     │   (API)         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Features

- **Edge caching** at 300+ global locations
- **Static assets** served from S3 with long TTL (1 year max)
- **API routing** to ALB with short/no cache
- **HTTPS only** with TLS 1.2+
- **Brotli + Gzip** compression
- **SPA support** (404/403 → index.html)

## Cache Behaviors

| Path Pattern | Origin | Cache TTL | Methods |
|--------------|--------|-----------|---------|
| `/static/*` | S3 | 1 day - 1 year | GET, HEAD |
| `/_next/static/*` | S3 | 1 day - 1 year | GET, HEAD |
| `/api/*` | ALB | 0 - 60s | ALL |
| `/teams/*` | ALB | 0 - 60s | ALL |
| `/*` (default) | S3 | 1 day - 1 year | GET, HEAD |

## Prerequisites

1. ACM certificate in **us-east-1** (required for CloudFront)
2. ALB deployed and accessible
3. Route53 hosted zone for domain

## Deployment

```bash
# 1. Copy variables
cp terraform.tfvars.example terraform.tfvars

# 2. Edit terraform.tfvars with your values
vim terraform.tfvars

# 3. Initialize Terraform
terraform init

# 4. Plan
terraform plan

# 5. Apply
terraform apply
```

## Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `aws_region` | AWS region | No (default: eu-north-1) |
| `environment` | Environment name | No (default: production) |
| `domain_name` | Primary domain | No (default: cirkelline.com) |
| `alb_dns_name` | ALB DNS name | **Yes** |
| `acm_certificate_arn` | ACM cert ARN (us-east-1) | **Yes** |

## Outputs

| Output | Description |
|--------|-------------|
| `cloudfront_distribution_id` | Distribution ID for cache invalidation |
| `cloudfront_domain_name` | CloudFront domain (*.cloudfront.net) |
| `s3_bucket_name` | S3 bucket for static assets |

## Cache Invalidation

```bash
# Invalidate all
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"

# Invalidate specific paths
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/static/*" "/_next/*"
```

## Estimated Cost

| Component | Estimated Cost |
|-----------|---------------|
| CloudFront (1M requests) | ~$85/month |
| S3 (10GB storage) | ~$0.25/month |
| Data Transfer (100GB) | ~$8.50/month |
| **Total** | **~$95/month** |

---

*Cirkelline CDN Infrastructure v1.0.0*
