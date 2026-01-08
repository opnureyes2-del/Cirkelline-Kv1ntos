# =============================================================================
# CIRKELLINE AUTO-SCALING INFRASTRUCTURE
# =============================================================================
# ECS Service Auto-Scaling for production workloads
# Supports 1M+ users with automatic scaling
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

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "cirkelline-system-cluster"
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
  default     = "cirkelline-system-backend-service"
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for request count metric"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix"
  type        = string
}

# Scaling limits
variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 3
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 100
}

# =============================================================================
# AUTO-SCALING TARGET
# =============================================================================

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${var.ecs_service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# =============================================================================
# SCALING POLICIES
# =============================================================================

# ---------------------------------------------------------------------------
# CPU-Based Scaling
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_policy" "cpu_scaling" {
  name               = "cirkelline-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 60   # 1 minute
  }
}

# ---------------------------------------------------------------------------
# Memory-Based Scaling
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_policy" "memory_scaling" {
  name               = "cirkelline-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# ---------------------------------------------------------------------------
# Request Count Scaling (ALB)
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_policy" "request_scaling" {
  name               = "cirkelline-request-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${var.alb_arn_suffix}/${var.target_group_arn_suffix}"
    }
    target_value       = 1000.0  # 1000 requests per target
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# =============================================================================
# SCHEDULED SCALING
# =============================================================================

# ---------------------------------------------------------------------------
# Morning Scale-Up (08:00 CET)
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "morning_scale_up" {
  name               = "cirkelline-morning-scale-up"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 7 * * ? *)"  # 07:00 UTC = 08:00 CET

  scalable_target_action {
    min_capacity = 5
    max_capacity = var.max_capacity
  }
}

# ---------------------------------------------------------------------------
# Evening Peak (18:00 CET)
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "evening_peak" {
  name               = "cirkelline-evening-peak"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 17 * * ? *)"  # 17:00 UTC = 18:00 CET

  scalable_target_action {
    min_capacity = 10
    max_capacity = var.max_capacity
  }
}

# ---------------------------------------------------------------------------
# Night Scale-Down (23:00 CET)
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "night_scale_down" {
  name               = "cirkelline-night-scale-down"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 22 * * ? *)"  # 22:00 UTC = 23:00 CET

  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
}

# ---------------------------------------------------------------------------
# Weekend Scale-Down
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "weekend_scale_down" {
  name               = "cirkelline-weekend-scale-down"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 22 ? * FRI *)"  # Friday 22:00 UTC

  scalable_target_action {
    min_capacity = 2
    max_capacity = 20
  }
}

# ---------------------------------------------------------------------------
# Monday Scale-Up
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "monday_scale_up" {
  name               = "cirkelline-monday-scale-up"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 6 ? * MON *)"  # Monday 06:00 UTC

  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
}

# =============================================================================
# CLOUDWATCH ALARMS
# =============================================================================

# ---------------------------------------------------------------------------
# High CPU Alarm
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "cirkelline-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "CPU utilization above 85%"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = []  # Add SNS topic ARN for notifications
  ok_actions    = []
}

# ---------------------------------------------------------------------------
# High Memory Alarm
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "cirkelline-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 90
  alarm_description   = "Memory utilization above 90%"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = []
  ok_actions    = []
}

# ---------------------------------------------------------------------------
# Low Task Count Alarm
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "low_task_count" {
  alarm_name          = "cirkelline-low-task-count"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = var.min_capacity
  alarm_description   = "Running tasks below minimum"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  alarm_actions = []
  ok_actions    = []
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "autoscaling_target_id" {
  description = "Auto-scaling target ID"
  value       = aws_appautoscaling_target.ecs_target.id
}

output "cpu_scaling_policy_arn" {
  description = "CPU scaling policy ARN"
  value       = aws_appautoscaling_policy.cpu_scaling.arn
}

output "memory_scaling_policy_arn" {
  description = "Memory scaling policy ARN"
  value       = aws_appautoscaling_policy.memory_scaling.arn
}

output "request_scaling_policy_arn" {
  description = "Request count scaling policy ARN"
  value       = aws_appautoscaling_policy.request_scaling.arn
}

output "scaling_capacity" {
  description = "Scaling capacity range"
  value = {
    min = var.min_capacity
    max = var.max_capacity
  }
}
