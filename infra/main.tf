########################################
# Terraform S3
# Cruise Finder Remote State
#######################################
terraform {
  backend "s3" {
    bucket         = "cruise-finder-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "us-west-2"
    use_lockfile   = true
    encrypt        = true
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
  lifecycle {prevent_destroy = true}
}

# --------------------------------------
# CloudWatch Log Group
# --------------------------------------
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/cruise-finder"
  retention_in_days = 1
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
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# --------------------------------------
# ECS Task Definition (Fargate)
# --------------------------------------
resource "aws_ecs_task_definition" "cruise_finder_task" {
  family                   = "cruise-finder-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "cruise-finder",
      image     = "${aws_ecr_repository.cruise_finder.repository_url}:latest",
      essential = true,
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = "/ecs/cruise-finder",
          awslogs-region        = "us-west-2",
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  lifecycle {
    create_before_destroy = true
  }
}

# --------------------------------------
# CloudWatch Scheduled Event
# --------------------------------------
resource "aws_cloudwatch_event_rule" "daily_cruise_finder" {
  name                = "run-cruise-finder-daily"
  description         = "Runs cruise-finder ECS task every day at 5:00 AM UTC"
  schedule_expression = "cron(0 11 * * ? *)"  # 5:00 AM MT daily
  state               = "ENABLED"
}

# --------------------------------------
# IAM Role to allow EventBridge to run ECS task
# --------------------------------------
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

# --------------------------------------
# Event Target that runs ECS task
# --------------------------------------
resource "aws_cloudwatch_event_target" "run_task" {
  rule      = aws_cloudwatch_event_rule.daily_cruise_finder.name
  role_arn  = aws_iam_role.eventbridge_invoke_ecs.arn
  target_id = "CruiseFinderTask"
  arn       = aws_ecs_cluster.cruise_cluster.arn

  ecs_target {
    launch_type         = "FARGATE"
    platform_version    = "LATEST"
    task_definition_arn = aws_ecs_task_definition.cruise_finder_task.arn
    network_configuration {
      subnets         = [var.subnet_id]
      assign_public_ip = true
      security_groups = [var.security_group_id]
    }
  }
}

# --------------------------------------
# Lambda Execution Role
# --------------------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --------------------------------------
# Lambda Role ECR Read Access
# --------------------------------------
resource "aws_iam_role_policy_attachment" "lambda_ecr_read" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# --------------------------------------
# Lambda ECR Auth Token Access
# --------------------------------------
resource "aws_iam_role_policy" "lambda_ecr_auth" {
  name = "lambda-ecr-auth"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Resource = "*"
      }
    ]
  })
}

# --------------------------------------
# Define the Lambda Function
# --------------------------------------
resource "aws_lambda_function" "list_users" {
  function_name = "list-users"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "491696534851.dkr.ecr.us-west-2.amazonaws.com/list-users:latest"
  timeout       = 30
}

# --------------------------------------
# API Gateway HTTP API
# --------------------------------------
resource "aws_apigatewayv2_api" "lambda_api" {
  name          = "lambda-api"
  protocol_type = "HTTP"
}

# --------------------------------------
# API Gateway Integration
# --------------------------------------
resource "aws_apigatewayv2_integration" "list_users" {
  api_id                 = aws_apigatewayv2_api.lambda_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.list_users.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# --------------------------------------
# API Gateway Route
# --------------------------------------
resource "aws_apigatewayv2_route" "list_users" {
  api_id    = aws_apigatewayv2_api.lambda_api.id
  route_key = "GET /list-users"
  target    = "integrations/${aws_apigatewayv2_integration.list_users.id}"
}

# --------------------------------------
# Lambda Permission
# --------------------------------------
resource "aws_lambda_permission" "apigw_list_users" {
  statement_id  = "AllowAPIGatewayInvokeListUsers"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.list_users.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda_api.execution_arn}/*/*"
}
