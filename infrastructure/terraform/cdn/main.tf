# =============================================================================
# CIRKELLINE CDN INFRASTRUCTURE
# =============================================================================
# CloudFront distribution for static assets and API caching
# Supports 1M+ users with edge caching
#
# Princip: "Man behøver ikke se for at vide - vi bygger så alt er gennemsigtigt."
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "cirkelline"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "cirkelline.com"
}

variable "api_domain" {
  description = "API domain name"
  type        = string
  default     = "api.cirkelline.com"
}

variable "alb_dns_name" {
  description = "ALB DNS name for API origin"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}

# =============================================================================
# S3 BUCKET FOR STATIC ASSETS
# =============================================================================

resource "aws_s3_bucket" "static_assets" {
  bucket = "cirkelline-static-${var.environment}"
}

resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# =============================================================================
# CLOUDFRONT ORIGIN ACCESS IDENTITY
# =============================================================================

resource "aws_cloudfront_origin_access_identity" "static" {
  comment = "OAI for Cirkelline static assets"
}

# S3 bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "CloudFrontAccess"
        Effect    = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.static.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_assets.arn}/*"
      }
    ]
  })
}

# =============================================================================
# CLOUDFRONT CACHE POLICIES
# =============================================================================

# Cache policy for static assets (long TTL)
resource "aws_cloudfront_cache_policy" "static_assets" {
  name        = "cirkelline-static-cache-${var.environment}"
  comment     = "Cache policy for static assets"
  default_ttl = 86400    # 1 day
  max_ttl     = 31536000 # 1 year
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

# Cache policy for API (short TTL or no cache)
resource "aws_cloudfront_cache_policy" "api" {
  name        = "cirkelline-api-cache-${var.environment}"
  comment     = "Cache policy for API responses"
  default_ttl = 0
  max_ttl     = 60
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "all"
    }
    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Authorization", "Accept", "Content-Type"]
      }
    }
    query_strings_config {
      query_string_behavior = "all"
    }
  }
}

# =============================================================================
# CLOUDFRONT ORIGIN REQUEST POLICY
# =============================================================================

resource "aws_cloudfront_origin_request_policy" "api" {
  name    = "cirkelline-api-origin-${var.environment}"
  comment = "Origin request policy for API"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "whitelist"
    headers {
      items = [
        "Authorization",
        "Accept",
        "Content-Type",
        "Origin",
        "Referer",
        "User-Agent",
        "X-Forwarded-For",
      ]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

# =============================================================================
# CLOUDFRONT DISTRIBUTION
# =============================================================================

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Cirkelline CDN - ${var.environment}"
  default_root_object = "index.html"
  price_class         = "PriceClass_100" # US, Canada, Europe

  aliases = [
    var.domain_name,
    "www.${var.domain_name}",
  ]

  # ---------------------------------------------------------------------------
  # ORIGIN: S3 Static Assets
  # ---------------------------------------------------------------------------
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-static"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static.cloudfront_access_identity_path
    }
  }

  # ---------------------------------------------------------------------------
  # ORIGIN: API (ALB)
  # ---------------------------------------------------------------------------
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "ALB-api"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ---------------------------------------------------------------------------
  # BEHAVIOR: Static Assets (/static/*)
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static"

    cache_policy_id = aws_cloudfront_cache_policy.static_assets.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # BEHAVIOR: Assets (/_next/static/*)
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/_next/static/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static"

    cache_policy_id = aws_cloudfront_cache_policy.static_assets.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # BEHAVIOR: API (/api/*)
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-api"

    cache_policy_id          = aws_cloudfront_cache_policy.api.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # BEHAVIOR: Teams endpoint (/teams/*)
  # ---------------------------------------------------------------------------
  ordered_cache_behavior {
    path_pattern     = "/teams/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-api"

    cache_policy_id          = aws_cloudfront_cache_policy.api.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # DEFAULT BEHAVIOR: Frontend (Next.js)
  # ---------------------------------------------------------------------------
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static"

    cache_policy_id = aws_cloudfront_cache_policy.static_assets.id

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  # ---------------------------------------------------------------------------
  # RESTRICTIONS
  # ---------------------------------------------------------------------------
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # ---------------------------------------------------------------------------
  # SSL CERTIFICATE
  # ---------------------------------------------------------------------------
  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # ---------------------------------------------------------------------------
  # CUSTOM ERROR RESPONSES (SPA support)
  # ---------------------------------------------------------------------------
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = {
    Name = "cirkelline-cdn-${var.environment}"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for static assets"
  value       = aws_s3_bucket.static_assets.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.static_assets.arn
}
