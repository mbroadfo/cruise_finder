# Changelog

All notable changes to the cruise_finder project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2025-11-23

### Removed

- Deleted `src/aws_secrets.py` - unused Secrets Manager module
- Removed all Secrets Manager code from Python files (imports, function calls)
- Removed AWS Secrets Manager permissions from ECS task IAM policy

### Changed

- Simplified S3 client initialization to use IAM role credentials directly (no explicit credential loading)
- Updated `infra/main.tf` - scoped IAM policy resources to specific ARNs (no wildcards)
- Consolidated terraform IAM user from 10 MRB-contaminated policies to 5 clean terraform-lcf-* policies

### Added

- Created Phase 0 IAM cleanup documentation in `infra/setup/` directory:
  - QUICKSTART.md - 5-minute setup guide
  - README.md - Complete step-by-step instructions
  - PHASE_0_IAM_CLEANUP.md - Technical background
  - 4 JSON policy files (terraform-lcf-infrastructure, terraform-lcf-state-management, terraform-lcf-task-policy-mgmt, terraform-lcf-research)
- Added MIGRATION_GUIDE.md - Documents why secrets migration not needed and Phase 0 IAM cleanup
- Added copilot-instructions.md - Python/Terraform-specific development guidelines

### Infrastructure

- Terraform IAM policy now uses specific resource ARNs:
  - S3: `arn:aws:s3:::mytripdata8675309/*`
  - CloudFront: `arn:aws:cloudfront::491696534851:distribution/E22G95LIEIJY6O`
- Removed Secrets Manager permissions from `aws_iam_policy.ecs_task_access`
- Formatted all Terraform files with `terraform fmt`

### Security

- Enhanced security by preventing terraform user from modifying its own IAM permissions
- Removed unused Secrets Manager dependency ($0.40/month savings)
- Implemented IAM role-based authentication throughout (AWS best practice)
- Eliminated MRB (Mom's Recipe Box) contamination from cruise_finder IAM policies
