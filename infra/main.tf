########################################
# Terraform S3
# Cruise Finder Remote State
#######################################
terraform {
  backend "s3" {
    bucket       = "cruise-finder-tfstate"
    key          = "infra/terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
    encrypt      = true
  }
}

########################################
# Terraform for ECS Fargate (Bare Metal)
# Cruise Finder Container Runtime
########################################

# --------------------------------------
# Provider
# --------------------------------------
provider "aws" {
  region = var.aws_region
}

# --------------------------------------
# ECR Repository
# --------------------------------------
resource "aws_ecr_repository" "cruise_finder" {
  name                 = "cruise-finder"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  lifecycle { prevent_destroy = true }
}

# --------------------------------------
# CloudWatch Log Group
# --------------------------------------
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/cruise-finder"
  retention_in_days = 7
}

# --------------------------------------
# IAM Roles
# --------------------------------------
# Execution Role: ECS pulls image, logs to CW
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Principal : {
          Service : "ecs-tasks.amazonaws.com"
        },
        Action : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Attach custom secrets + S3 policy to execution role too
resource "aws_iam_role_policy_attachment" "ecs_execution_access_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ecs_task_access.arn
}

# Custom permissions for secrets + S3 + CloudFront
resource "aws_iam_policy" "ecs_task_access" {
  name = "ecs-cruise-finder-task-access"

  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Action : [
          "secretsmanager:GetSecretValue",
          "s3:PutObject",
          "cloudfront:CreateInvalidation"
        ],
        Resource : "*"
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "ecsCruiseFinderTaskRole"

  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Principal : {
          Service : "ecs-tasks.amazonaws.com"
        },
        Action : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_custom_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_access.arn
}

# --------------------------------------
# Additional Policy for CloudFront Invalidation
# --------------------------------------
resource "aws_iam_policy" "cloudfront_invalidation" {
  name = "cloudfront-invalidation-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "cloudfront:CreateInvalidation"
        ],
        Resource = "arn:aws:cloudfront::491696534851:distribution/E22G95LIEIJY6O"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudfront_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.cloudfront_invalidation.arn
}

# --------------------------------------
# ECS Cluster
# --------------------------------------
resource "aws_ecs_cluster" "cruise_cluster" {
  name = "cruise-finder-cluster"
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
  tags = {
    Name = "cruise-finder-cluster"
  }
}

# --------------------------------------
# ECS Container Insights
# --------------------------------------
resource "aws_cloudwatch_log_group" "ecs_insights_logs" {
  name              = "/aws/ecs/containerinsights/cruise-finder-cluster/performance"
  retention_in_days = 7
}

# --------------------------------------
# ECR Lifecycle Policy
# --------------------------------------
resource "aws_ecr_lifecycle_policy" "cruise_cleanup" {
  repository = aws_ecr_repository.cruise_finder.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 3 images only"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

########################################
# ECS Task Definition (Hardcoded ARN)
########################################

# Removed aws_ecs_task_definition.cruise_finder_task

########################################
# CloudWatch Scheduled Event
########################################
# resource "aws_cloudwatch_event_rule" "daily_cruise_finder" {
#   name                = "run-cruise-finder-daily"
#   description         = "Runs cruise-finder ECS task every day at 5:00 AM UTC"
#   schedule_expression = "cron(0 11 * * ? *)"  # 5:00 AM MT daily
#   state               = "ENABLED"
# }

########################################
# IAM Role to allow EventBridge to run ECS task
########################################
resource "aws_iam_role" "eventbridge_invoke_ecs" {
  name = "eventbridgeECSInvokeRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_invoke_ecs_policy" {
  name = "InvokeECSTaskPolicy"
  role = aws_iam_role.eventbridge_invoke_ecs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "iam:PassRole"
        ]
        Resource = "*"
      }
    ]
  })
}

########################################
# Event Target that runs ECS task
########################################
# resource "aws_cloudwatch_event_target" "run_task" {
#   rule      = aws_cloudwatch_event_rule.daily_cruise_finder.name
#   role_arn  = aws_iam_role.eventbridge_invoke_ecs.arn
#   target_id = "CruiseFinderTask"
#   arn       = aws_ecs_cluster.cruise_cluster.arn

#   ecs_target {
#     launch_type         = "FARGATE"
#     platform_version    = "LATEST"
#     task_definition_arn = "arn:aws:ecs:us-west-2:491696534851:task-definition/cruise-finder-task:73"  # <-- PINNED manually

#     network_configuration {
#       subnets          = [var.subnet_id]
#       assign_public_ip = true
#       security_groups  = [var.security_group_id]
#     }
#   }
#     dead_letter_config {
#       arn = aws_sqs_queue.eventbridge_dlq.arn
#     }
# }

########################################
# Log group to capture EventBridge -> ECS target failures
########################################
resource "aws_cloudwatch_log_group" "eventbridge_cruise_finder" {
  name              = "/aws/events/run-cruise-finder-daily"
  retention_in_days = 7
}

########################################
# DLQ for EventBridge failures
########################################
resource "aws_sqs_queue" "eventbridge_dlq" {
  name                      = "eventbridge-cruise-finder-dlq"
  message_retention_seconds = 1209600 # 14 days
}

########################################
# Internet Gateway for ECS public access
########################################
resource "aws_internet_gateway" "cruise_finder" {
  vpc_id = var.vpc_id

  tags = {
    Name = "cruise-finder-igw"
  }
}

########################################
# Route table entry for 0.0.0.0/0 to IGW
########################################
resource "aws_route" "public_internet_access" {
  route_table_id         = var.route_table_id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.cruise_finder.id
}


######################################################
# CLOUDFRONT
######################################################
resource "aws_cloudfront_distribution" "cruise_finder" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = ""
  default_root_object = ""
  http_version        = "http2and3"
  price_class         = "PriceClass_All"

  origin {
    domain_name = "zf5sdrd108.execute-api.us-west-2.amazonaws.com"
    origin_id   = "zf5sdrd108.execute-api.us-west-2.amazonaws.com"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "https-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_read_timeout      = 30
      origin_keepalive_timeout = 5
    }
  }

  origin {
    domain_name              = "mytripdata8675309.s3.us-west-2.amazonaws.com"
    origin_id                = "mytripdata8675309.s3.us-west-2.amazonaws.com"
    origin_access_control_id = "ENOVD7IIZ96BA"

    s3_origin_config {
      origin_access_identity = ""
    }
  }

  default_cache_behavior {
    target_origin_id       = "mytripdata8675309.s3.us-west-2.amazonaws.com"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id   = "bf5ae425-e28a-4bad-beb8-609c621b28a8"
    response_headers_policy_id = "eaab4381-ed33-4a86-88ca-d9558dc6cd63"
  }

  ordered_cache_behavior {
    path_pattern           = "/prod/admin-api/*"
    target_origin_id       = "zf5sdrd108.execute-api.us-west-2.amazonaws.com"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id   = "bf5ae425-e28a-4bad-beb8-609c621b28a8"
    response_headers_policy_id = "eaab4381-ed33-4a86-88ca-d9558dc6cd63"
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1"
    ssl_support_method             = "vip"
  }

  wait_for_deployment = true

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      origin,
      viewer_certificate[0].ssl_support_method,
    ]
  }
}

####################################################
# SPACELIFT.IO - IAM Role
####################################################
resource "aws_iam_role" "spacelift_runner" {
  name = "SpaceliftCruiseFinderRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::324880187172:root" # ✅ Spacelift US Account ID
        },
        Action = "sts:AssumeRole",
        Condition = {
          StringLike = {
            "sts:ExternalId" = "mbroadfo@*"
          }
        }
      }
    ]
  })
}

####################################################
# SPACELIFT.IO - IAM Policy
####################################################
resource "aws_iam_role_policy" "spacelift_policy" {
  name = "SpaceliftCruiseFinderPolicy"
  role = aws_iam_role.spacelift_runner.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecs:*",
          "ecr:*",
          "logs:*",
          "events:*",
          "iam:PassRole",
          "s3:*"
        ],
        Resource = "*"
      }
    ]
  })
}
