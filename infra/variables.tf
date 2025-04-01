variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-west-2"
}

variable "subnet_id" {
  description = "Subnet ID for Fargate task"
  type        = string
}

variable "security_group_id" {
  description = "Security Group ID for Fargate task"
  type        = string
}
