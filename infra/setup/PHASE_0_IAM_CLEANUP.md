# Phase 0: Terraform IAM Permission Cleanup for cruise_finder

**Date**: November 23, 2025  
**Purpose**: Clean up terraform user permissions by creating consolidated `terraform-lcf-*` policies  
**Status**: Not Started

---

## 🎯 Goal

Replace 10 scattered policies (some with MRB contamination) with 3 clean, consolidated policies:

1. **terraform-lcf-infrastructure** - Core IaC permissions for ECS, ECR, CloudFront, etc.
2. **terraform-lcf-state-management** - S3 state bucket access
3. **terraform-lcf-research** - Read-only permissions for debugging and enhancements

---

## 📋 Current State (10 Policies - MESSY)

| Policy Name | Keep? | Issue |
|-------------|-------|-------|
| terraform-rds | ❌ | For MRB (cruise_finder has no database) |
| terraform-infra-policy | ⚠️ | Has MRB S3 buckets mixed in |
| terraform-lcf-ssm | ✅ | Clean - Keep as-is |
| terraform-task-access | ✅ | Clean - Needed for policy versioning |
| terraform-assume-role-policy | ❌ | Lambda role for MRB |
| terraform-lcf-permissions | ⚠️ | Just IAM list - merge into research |
| terraform-read-current-state | ⚠️ | Huge policy - needs cleanup |
| terraform-s3-policy | ❌ | Only MRB bucket |
| terraform-pass-roll | ⚠️ | Has lambda_exec_role for MRB |
| terraform-lambda-deploy | ❌ | For MRB (cruise_finder has no Lambda) |

---

## 🎯 Target State (5 Policies - CLEAN)

| Policy Name | Purpose | Resources |
|-------------|---------|-----------|
| **terraform-lcf-infrastructure** | Core IaC for cruise_finder | ECS, ECR, CloudWatch, EventBridge, IAM roles, CloudFront, VPC, S3 (mytripdata8675309), SQS |
| **terraform-lcf-state-management** | Terraform state bucket access | S3 (cruise-finder-tfstate) |
| **terraform-lcf-ssm** | Parameter Store access | SSM (cruise-finder params) |
| **terraform-lcf-task-policy-mgmt** | ECS task IAM policy versioning | IAM (ecs-cruise-finder-task-access) |
| **terraform-lcf-research** | Read-only for debugging | IAM, ECS, ECR, Logs, Events, EC2, CloudFront |

---

## 📅 Step 1: Create New Consolidated Policies

### 1.1 Create `terraform-lcf-infrastructure.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECSManagement",
      "Effect": "Allow",
      "Action": [
        "ecs:CreateCluster",
        "ecs:UpdateCluster",
        "ecs:DeleteCluster",
        "ecs:DescribeClusters",
        "ecs:RegisterTaskDefinition",
        "ecs:DeregisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecs:TagResource",
        "ecs:UntagResource",
        "ecs:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRManagement",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages",
        "ecr:ListImages",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken",
        "ecr:GetLifecyclePolicy",
        "ecr:PutLifecyclePolicy",
        "ecr:DeleteLifecyclePolicy",
        "ecr:ListTagsForResource",
        "ecr:TagResource",
        "ecr:UntagResource",
        "ecr:PutImageScanningConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsManagement",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy",
        "logs:TagResource",
        "logs:UntagResource",
        "logs:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EventBridgeManagement",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:ListTargetsByRule",
        "events:ListTagsForResource",
        "events:TagResource",
        "events:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": [
        "arn:aws:iam::491696534851:role/ecsTaskExecutionRole",
        "arn:aws:iam::491696534851:role/ecsCruiseFinderTaskRole",
        "arn:aws:iam::491696534851:role/eventbridgeECSInvokeRole"
      ]
    },
    {
      "Sid": "IAMPolicyManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:SetDefaultPolicyVersion"
      ],
      "Resource": [
        "arn:aws:iam::491696534851:policy/ecs-cruise-finder-task-access",
        "arn:aws:iam::491696534851:policy/cloudfront-invalidation-policy"
      ]
    },
    {
      "Sid": "CloudFrontManagement",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:GetDistributionConfig",
        "cloudfront:ListDistributions",
        "cloudfront:ListTagsForResource",
        "cloudfront:TagResource",
        "cloudfront:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:DescribeRouteTables",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:ReplaceRoute",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribeInternetGateways",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
        "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3DataBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mytripdata8675309",
        "arn:aws:s3:::mytripdata8675309/*"
      ]
    },
    {
      "Sid": "SQSManagement",
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:DeleteQueue",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:ListQueueTags",
        "sqs:TagQueue",
        "sqs:UntagQueue"
      ],
      "Resource": "*"
    }
  ]
}
```

### 1.2 Create `terraform-lcf-state-management.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketPolicy",
        "s3:GetBucketAcl",
        "s3:GetBucketVersioning",
        "s3:GetBucketTagging",
        "s3:PutBucketTagging",
        "s3:GetBucketPublicAccessBlock",
        "s3:PutBucketPublicAccessBlock"
      ],
      "Resource": [
        "arn:aws:s3:::cruise-finder-tfstate",
        "arn:aws:s3:::cruise-finder-tfstate/*"
      ]
    }
  ]
}
```

### 1.3 Rename `terraform-task-access` to `terraform-lcf-task-policy-mgmt`

This policy is already clean - just rename it for consistency:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECSTaskPolicyVersioning",
      "Effect": "Allow",
      "Action": [
        "iam:CreatePolicyVersion",
        "iam:ListPolicyVersions",
        "iam:DeletePolicyVersion"
      ],
      "Resource": "arn:aws:iam::491696534851:policy/ecs-cruise-finder-task-access"
    }
  ]
}
```

### 1.4 Create `terraform-lcf-research.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyResearch",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:GetRolePolicy",
        "iam:ListAttachedUserPolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListPolicies",
        "iam:ListPolicyVersions",
        "iam:ListRolePolicies",
        "iam:ListUserPolicies",
        "ecs:DescribeClusters",
        "ecs:DescribeTaskDefinition",
        "ecs:ListClusters",
        "ecs:ListTaskDefinitions",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages",
        "ecr:ListImages",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "logs:ListTagsForResource",
        "events:DescribeRule",
        "events:ListRules",
        "events:ListTargetsByRule",
        "events:ListTagsForResource",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeRouteTables",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeNetworkInterfaces",
        "cloudfront:GetDistribution",
        "cloudfront:GetDistributionConfig",
        "cloudfront:ListDistributions",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:ListBucket",
        "sqs:ListQueues",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📅 Step 2: Create the New Policies

```powershell
# Navigate to infra directory
cd C:\Users\Mike\Documents\Python\cruise_finder\infra

# Create policy 1: terraform-lcf-infrastructure
aws iam create-policy `
  --policy-name terraform-lcf-infrastructure `
  --policy-document file://terraform-lcf-infrastructure.json `
  --description "Core IaC permissions for cruise_finder ECS Fargate application"

# Create policy 2: terraform-lcf-state-management
aws iam create-policy `
  --policy-name terraform-lcf-state-management `
  --policy-document file://terraform-lcf-state-management.json `
  --description "Terraform state bucket access for cruise_finder"

# Create policy 3: terraform-lcf-task-policy-mgmt (replacement for terraform-task-access)
aws iam create-policy `
  --policy-name terraform-lcf-task-policy-mgmt `
  --policy-document file://terraform-lcf-task-policy-mgmt.json `
  --description "ECS task IAM policy versioning for cruise_finder"

# Create policy 4: terraform-lcf-research
aws iam create-policy `
  --policy-name terraform-lcf-research `
  --policy-document file://terraform-lcf-research.json `
  --description "Read-only permissions for debugging and enhancement work"
```

---

## 📅 Step 3: Attach New Policies to terraform User

```powershell
# Attach new policies
aws iam attach-user-policy `
  --user-name terraform `
  --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-infrastructure

aws iam attach-user-policy `
  --user-name terraform `
  --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-state-management

aws iam attach-user-policy `
  --user-name terraform `
  --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-task-policy-mgmt

aws iam attach-user-policy `
  --user-name terraform `
  --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-research

# Verify all policies attached
aws iam list-attached-user-policies --user-name terraform
```

---

## 📅 Step 4: Test Terraform Operations

```powershell
cd C:\Users\Mike\Documents\Python\cruise_finder\infra

# Test plan (read-only)
terraform plan

# If plan succeeds, test apply (only if safe changes)
terraform apply

# Test updating ECS task IAM policy
terraform apply -target=aws_iam_policy.ecs_task_access
```

**Success Criteria**:
- ✅ `terraform plan` completes without permission errors
- ✅ `terraform apply` can update resources
- ✅ Can create new policy versions
- ✅ Can read CloudWatch logs for debugging

---

## 📅 Step 5: Detach Old Policies (Only After Testing)

**⚠️ WARNING**: Only proceed if Step 4 tests pass!

```powershell
# Detach old contaminated policies
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-rds
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-infra-policy
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-task-access
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-assume-role-policy
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-permissions
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-read-current-state
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-s3-policy
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-pass-roll
aws iam detach-user-policy --user-name terraform --policy-arn arn:aws:iam::491696534851:policy/terraform-lambda-deploy

# Keep these clean policies:
# - terraform-lcf-ssm (already clean)
# - terraform-lcf-infrastructure (new)
# - terraform-lcf-state-management (new)
# - terraform-lcf-task-policy-mgmt (new)
# - terraform-lcf-research (new)
```

---

## 📅 Step 6: Retest Everything

```powershell
# Verify only clean policies remain
aws iam list-attached-user-policies --user-name terraform

# Expected output: Only 5 terraform-lcf-* policies

# Retest terraform
cd C:\Users\Mike\Documents\Python\cruise_finder\infra
terraform plan
terraform apply

# Retest Python application (from Phase 0 cleanup)
cd C:\Users\Mike\Documents\Python\cruise_finder
C:/Users/Mike/Documents/Python/cruise_finder/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); from save_trips import s3; print('✅ S3 client works')"
```

---

## 📅 Step 7: Delete Old Policies (Optional - After 1 Week)

**⚠️ CAUTION**: Only delete after confirming everything works for at least 1 week!

```powershell
# Delete old policies (they're no longer attached to any user)
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-rds
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-infra-policy
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-task-access
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-assume-role-policy
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-lcf-permissions
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-read-current-state
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-s3-policy
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-pass-roll
aws iam delete-policy --policy-arn arn:aws:iam::491696534851:policy/terraform-lambda-deploy

# Note: You may need to delete old policy versions first
# Use: aws iam delete-policy-version --policy-arn <ARN> --version-id <vX>
```

---

## ✅ Success Criteria

- [x] 4 new clean `terraform-lcf-*` policies created
- [ ] New policies attached to terraform user
- [ ] Terraform plan/apply works
- [ ] Python application still works
- [ ] Old MRB-contaminated policies detached
- [ ] System stable for 1 week
- [ ] Old policies deleted (optional)

---

## 📊 Before vs After

### Before (10 policies - messy):
- terraform-rds (MRB)
- terraform-infra-policy (mixed LCF + MRB)
- terraform-lcf-ssm ✅
- terraform-task-access (should be terraform-lcf-*)
- terraform-assume-role-policy (MRB Lambda)
- terraform-lcf-permissions (tiny)
- terraform-read-current-state (huge, unfocused)
- terraform-s3-policy (MRB only)
- terraform-pass-roll (mixed)
- terraform-lambda-deploy (MRB)

### After (5 policies - clean):
- terraform-lcf-infrastructure ✅
- terraform-lcf-state-management ✅
- terraform-lcf-ssm ✅
- terraform-lcf-task-policy-mgmt ✅
- terraform-lcf-research ✅

**Result**: Cleaner, more maintainable, zero MRB contamination! 🎉
