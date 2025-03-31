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

# Custom permissions for secrets + S3
resource "aws_iam_policy" "ecs_task_access" {
  name = "ecs-cruise-finder-task-access"

  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Action : [
          "secretsmanager:GetSecretValue",
          "s3:PutObject"
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
# ECS Cluster
# --------------------------------------
resource "aws_ecs_cluster" "cruise_cluster" {
  name = "cruise-finder-cluster"
}

# --------------------------------------
# ECS Task Definition
# --------------------------------------
resource "aws_ecs_task_definition" "cruise_task" {
  family                   = "cruise-finder-task"
  cpu                      = "512"
  memory                   = "1024"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "cruise-finder",
      image     = "${aws_ecr_repository.cruise_finder.repository_url}:latest",
      essential = true,
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}
