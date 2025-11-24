# cruise_finder: Secrets Manager Cleanup & IAM Consolidation

**Application**: cruise_finder (ECS Fargate - Expedition Data Scraper)  
**Status**: ✅ Code Cleanup COMPLETED - November 23, 2025  
**Phase 0 Status**: 🔄 IAM Cleanup READY - Manual execution required  
**Last Updated**: November 23, 2025

---

## 📋 Summary

### Part 1: Secrets Manager Removal (COMPLETED ✅)

**Discovery**: cruise_finder does NOT need AWS Secrets Manager or Parameter Store.

**Why**:

- Application is a simple ECS Fargate task that scrapes Lindblad Expeditions website

- Uses IAM role-based authentication (best practice) for AWS services

- No sensitive credentials required - only needs:
  - Internet access (to scrape website)
  - S3 PutObject permission (to write results)
  - CloudFront CreateInvalidation permission (to refresh cache)

**Action Taken**:

1. Removed all Secrets Manager code from Python files
2. Deleted `aws_secrets.py` (unused)
3. Updated Terraform IAM policy to remove Secrets Manager permissions
4. Simplified S3 client to use IAM role credentials directly

**Migration Status**: ❌ NOT APPLICABLE - cruise_finder doesn't need secrets migration

---

### Part 2: IAM Cleanup - Phase 0 (READY 🔄)

**Discovery**: terraform IAM user has 10 policies with MRB (Mom's Recipe Box) contamination.

**Problem**:

- Mixed cruise_finder + MRB permissions in same policies

- Unclear naming (e.g., `terraform-task-access` vs `terraform-lcf-*`)

- Too broad permissions (e.g., `terraform-read-current-state`)

- Includes unused permissions (RDS, Lambda - cruise_finder doesn't use these)

**Solution**:

Replace 10 messy policies with 5 clean, focused policies for cruise_finder only.

**📁 Phase 0 Setup Files**: See `infra/setup/` directory

- **QUICKSTART.md** - 5-minute setup guide

- **README.md** - Complete step-by-step instructions

- **PHASE_0_IAM_CLEANUP.md** - Technical background

- **4 JSON policy files** - Ready to copy/paste into AWS Console

**Status**:

- ✅ Policy JSON files created

- ✅ Documentation complete

- 🔄 **ACTION REQUIRED**: Manual execution via AWS Console (see `infra/setup/QUICKSTART.md`)

**Why Manual?**:
Security best practice - terraform user should NOT be able to modify its own IAM permissions. This prevents privilege escalation and requires human approval for IAM changes.

---

## 🚀 Next Steps

1. ✅ **Code cleanup**: DONE - Commit Python changes
2. ✅ **Terraform update**: DONE - Commit IAM policy changes  
3. 🔄 **Phase 0 IAM cleanup**: TODO - Follow `infra/setup/QUICKSTART.md`

4. ⏭️ **Test & Deploy**: After Phase 0 completion

---

## ✅ Prerequisites (Must Complete Phase 1 First)

Before starting cruise_finder migration, verify:

- [ ] Parameter Store parameter exists: `/cruise-finder/prod/aws-credentials`

- [ ] Parameter contains: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

- [ ] Test script passes: `python scripts/test-parameter-store.py`

- [ ] IAM policy prepared: `cruise_finder/infra/iam-policy-parameter-store.json`

**Verify**:

```powershell

aws ssm get-parameter `

  --name "/cruise-finder/prod/aws-credentials" `

  --with-decryption `

  --region us-west-2 `

  --query "Parameter.Value" `

  --output text

```

Expected: JSON with AWS credentials

**If this fails**: Complete Phase 1 first (see `../cruise-apps/REVISED_MIGRATION_PLAN.md`)

---

## 📅 Day 1: Create Parameter Store Utility

### Create `src/parameter_store.py`

```python

import boto3
import json
import os
from botocore.exceptions import ClientError

def get_parameter(name: str, region_name: str = "us-west-2", decrypt: bool = True) -> str:
    """
    Fetch a single parameter from AWS Systems Manager Parameter Store.
    """
    session = boto3.session.Session()
    client = session.client(service_name="ssm", region_name=region_name)
    
    try:
        response = client.get_parameter(Name=name, WithDecryption=decrypt)
        return response['Parameter']['Value']
    except ClientError as e:
        print(f"❌ Error retrieving parameter '{name}': {e}")
        raise

def load_aws_credentials(region_name: str = "us-west-2") -> dict:
    """
    Loads AWS credentials from Parameter Store.
    """
    param_value = get_parameter('/cruise-finder/prod/aws-credentials', region_name, True)
    return json.loads(param_value)

def inject_aws_credentials(region_name: str = "us-west-2") -> None:
    """
    Loads AWS credentials and injects them into environment variables.
    """
    credentials = load_aws_credentials(region_name)
    for key, value in credentials.items():
        if key not in os.environ:
            os.environ[key] = value
    print(f"✅ AWS credentials loaded from Parameter Store")

```

### Test Locally

```powershell

cd c:\Users\Mike\Documents\Python\cruise_finder

# Quick test
python -c "import sys; sys.path.insert(0, 'src'); from parameter_store import inject_aws_credentials; import os; inject_aws_credentials(); print('Test:', 'AWS_ACCESS_KEY_ID' in os.environ)"

```

Expected output:

```text

✅ AWS credentials loaded from Parameter Store
Test: True

```

### Commit Changes - Step 1 - Step 1

```powershell

git add src/parameter_store.py
git commit -m "feat: Add Parameter Store utility for cruise_finder"
git push

```

---

## 📅 Day 2: Add Dual-Mode Support

### Update `src/aws_secrets.py`

Add at the top:

```python

import os

# Dual-mode flag
USE_PARAMETER_STORE = os.getenv("USE_PARAMETER_STORE", "false").lower() == "true"

```

Update `inject_env_from_secrets()` function:

```python

def inject_env_from_secrets(secret_name: str = "cruise-finder-secrets", region_name: str = "us-west-2") -> None:
    """
    Loads AWS credentials and injects into environment variables.
    Supports dual mode: Parameter Store (new) or Secrets Manager (legacy).
    """
    if USE_PARAMETER_STORE:
        print("🔧 Loading credentials from Parameter Store...")
        from parameter_store import inject_aws_credentials
        inject_aws_credentials(region_name)
    else:
        print("🔧 Loading credentials from Secrets Manager (legacy)...")
        secrets = load_secrets(secret_name, region_name)
        # Only inject AWS-related keys
        aws_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
        for key in aws_keys:
            if key in secrets and key not in os.environ:
                os.environ[key] = secrets[key]
        print(f"✅ AWS credentials loaded from Secrets Manager")

```

### Test Both Modes

```powershell

# Test 1: Secrets Manager mode (default)
$env:USE_PARAMETER_STORE="false"
python -c "from src.aws_secrets import inject_env_from_secrets; inject_env_from_secrets()"

# Expected: 
# 🔧 Loading credentials from Secrets Manager (legacy)...
# ✅ AWS credentials loaded from Secrets Manager

# Test 2: Parameter Store mode
$env:USE_PARAMETER_STORE="true"
python -c "from src.aws_secrets import inject_env_from_secrets; inject_env_from_secrets()"

# Expected:
# 🔧 Loading credentials from Parameter Store...
# ✅ AWS credentials loaded from Parameter Store

```

### Commit Changes - Step 2 - Step 2

```powershell

git add src/aws_secrets.py
git commit -m "feat: Add dual-mode support (Secrets Manager OR Parameter Store)"
git push

```

---

## 📅 Day 3: Update IAM and Deploy with Secrets Manager

### Update Terraform IAM Policy

**File**: `infra/main.tf`

Add Parameter Store permissions to the ECS task role policy. Replace the existing Secrets Manager policy with one that includes BOTH Secrets Manager (for fallback) and Parameter Store:

```hcl
# Example - adjust based on your actual Terraform structure
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "ecs-cruise-finder-task-access"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Keep existing Secrets Manager access
      {
        Sid    = "SecretsManagerAccess"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:us-west-2:491696534851:secret:cruise-finder-secrets-*"
        ]
      },
      # ADD Parameter Store access
      {
        Sid    = "ParameterStoreReadCredentials"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:us-west-2:491696534851:parameter/cruise-finder/prod/*"
        ]
      },
      # Existing S3 and CloudFront permissions (keep as-is)
      {
        Sid    = "S3UploadAccess"
        Effect = "Allow"
        Action = ["s3:PutObject"]
        Resource = "arn:aws:s3:::mytripdata8675309/*"
      },
      {
        Sid    = "CloudFrontInvalidation"
        Effect = "Allow"
        Action = ["cloudfront:CreateInvalidation"]
        Resource = "arn:aws:cloudfront::491696534851:distribution/E22G95LIEIJY6O"
      },
      # KMS for both Secrets Manager and Parameter Store
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = [
              "secretsmanager.us-west-2.amazonaws.com",
              "ssm.us-west-2.amazonaws.com"
            ]
          }
        }
      }
    ]
  })
}

```

### Apply Terraform

```powershell

cd c:\Users\Mike\Documents\Python\cruise_finder\infra

terraform plan
# Review: Should show adding Parameter Store permissions, keeping Secrets Manager

terraform apply

```

### Build and Push Docker Image

```powershell

cd c:\Users\Mike\Documents\Python\cruise_finder

# Build
docker build -t cruise-finder:latest .

# Push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 491696534851.dkr.ecr.us-west-2.amazonaws.com
docker tag cruise-finder:latest 491696534851.dkr.ecr.us-west-2.amazonaws.com/cruise-finder:latest
docker push 491696534851.dkr.ecr.us-west-2.amazonaws.com/cruise-finder:latest

```

### Test with Secrets Manager (Baseline)

```powershell

# Run task manually to verify nothing broke
aws ecs run-task `

  --cluster cruise-finder-cluster `

  --task-definition cruise-finder-task:73 `

  --launch-type FARGATE `

  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a975322c55a6bd97],securityGroups=[sg-0e1769b0d4a2b1d4e],assignPublicIp=ENABLED}" `

  --region us-west-2

# Watch logs
aws logs tail /ecs/cruise-finder --follow --region us-west-2

```

**Expected log output**:

```text
🔧 Loading credentials from Secrets Manager (legacy)...
✅ AWS credentials loaded from Secrets Manager
[rest of normal application logs]

```

**Validation checklist**:

- [ ] Task completes with exit code 0 (success)

- [ ] Logs show "Secrets Manager" mode

- [ ] S3 file updated: `s3://mytripdata8675309/trip_list.json`

- [ ] CloudFront invalidation created

- [ ] No errors in logs

**Checkpoint**: Baseline confirmed - nothing broke ✅

### Commit Changes - Step 3 - Step 3

```powershell

git add infra/main.tf
git commit -m "feat: Add Parameter Store IAM permissions (dual-mode)"
git push

```

---

## 📅 Day 4: Switch to Parameter Store

### Create New ECS Task Definition Revision

**Method**: Add environment variable `USE_PARAMETER_STORE=true`

**Option 1: AWS Console** (Recommended)

1. Navigate to: **ECS → Task Definitions → cruise-finder-task**
2. Select current revision (e.g., 73)
3. Click **"Create new revision"**
4. Find **"Environment variables"** section
5. Click **"Add environment variable"**
6. Add:
   - Key: `USE_PARAMETER_STORE`

   - Value: `true`

7. Click **"Create"** (creates new revision, e.g., 74)

#### Option 2: CLI

```powershell

# Export current definition
aws ecs describe-task-definition `

  --task-definition cruise-finder-task `

  --region us-west-2 `

  --query 'taskDefinition' > task-def-temp.json

# Edit task-def-temp.json:
# Add to containerDefinitions[0].environment:
# {"name": "USE_PARAMETER_STORE", "value": "true"}

# Register new revision
aws ecs register-task-definition --cli-input-json file://task-def-temp.json --region us-west-2

```

### Test with Parameter Store

```powershell

# Run task with new revision (replace :74 with your new revision)
aws ecs run-task `

  --cluster cruise-finder-cluster `

  --task-definition cruise-finder-task:74 `

  --launch-type FARGATE `

  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a975322c55a6bd97],securityGroups=[sg-0e1769b0d4a2b1d4e],assignPublicIp=ENABLED}" `

  --region us-west-2

# Watch logs
aws logs tail /ecs/cruise-finder --follow --region us-west-2

```

**Expected log output**:

```text
🔧 Loading credentials from Parameter Store...
✅ AWS credentials loaded from Parameter Store
[rest of normal application logs]

```

**Validation checklist**:

- [ ] Task completes with exit code 0 (success)

- [ ] Logs show "Parameter Store" mode

- [ ] NO mention of "Secrets Manager" in logs

- [ ] S3 file updated

- [ ] CloudFront invalidation created

- [ ] No errors

**Verify S3 update**:

```powershell

aws s3 ls s3://mytripdata8675309/trip_list.json --region us-west-2
# Should show recent timestamp (within last few minutes)

```

**If any issues**: Rollback by running previous revision (`:73`)

**Checkpoint**: cruise_finder successfully using Parameter Store! 🎉

---

## 📅 Day 5-7: Update Scheduled Task & Monitor

### Update EventBridge Rule

```powershell

# Update scheduled task to use new revision
aws events put-targets `

  --rule run-cruise-finder-daily `

  --targets '[{"Id":"CruiseFinderTask","Arn":"arn:aws:ecs:us-west-2:491696534851:cluster/cruise-finder-cluster","RoleArn":"arn:aws:iam::491696534851:role/eventbridgeECSInvokeRole","EcsParameters":{"TaskDefinitionArn":"arn:aws:ecs:us-west-2:491696534851:task-definition/cruise-finder-task:74","LaunchType":"FARGATE","NetworkConfiguration":{"awsvpcConfiguration":{"Subnets":["subnet-0a975322c55a6bd97"],"SecurityGroups":["sg-0e1769b0d4a2b1d4e"],"AssignPublicIp":"ENABLED"}}}}]' `

  --region us-west-2

```

**Checkpoint**: Scheduled task now runs with Parameter Store mode

### Monitor for 3+ Days

**Scheduled task runs daily at 4:00 AM MST (11:00 AM UTC)**

**Daily monitoring**:

```powershell

# Check after scheduled run
aws logs tail /ecs/cruise-finder --since 2h --region us-west-2 | Select-String "Parameter Store"

# Verify S3 updated
aws s3 ls s3://mytripdata8675309/trip_list.json --region us-west-2

# Check for errors
aws logs filter-log-events `

  --log-group-name /ecs/cruise-finder `

  --filter-pattern "ERROR" `

  --start-time $((Get-Date).AddHours(-2).ToUniversalTime().ToString('s') + '000') `

  --region us-west-2

```

**Monitoring checklist** (minimum 3 days):

- [ ] **Day 1**: Scheduled run successful, logs show "Parameter Store"

- [ ] **Day 2**: S3 updated, no errors

- [ ] **Day 3**: CloudFront serving fresh data, cruise-viewer team reports no issues

- [ ] **Day 4-7** (optional): Extended monitoring for extra confidence

**Alert cruise-viewer team**: Monitor trip data loading

**Checkpoint**: cruise_finder stable on Parameter Store for 3+ days ✅

---

## Migration Complete

**cruise_finder migration status**:

- ✅ Using Parameter Store for AWS credentials

- ✅ 3+ days stable operation

- ✅ Secrets Manager still available as fallback

- ✅ Ready to proceed with cruise_admin migration (Phase 3)

**Next steps**:

1. **Week 3**: Migrate cruise_admin to Parameter Store
2. **Week 4**: Delete Secrets Manager (after both apps migrated)
3. **Week 5-6**: Implement Auth0 token caching (cruise_admin only)

**Don't clean up dual-mode code yet** - wait until after Secrets Manager is deleted in Phase 4

---

## 🚨 Rollback Procedures

### Immediate Rollback (During Testing - Day 4)

If Parameter Store mode fails:

```powershell

# Run with previous revision (Secrets Manager mode)
aws ecs run-task `

  --cluster cruise-finder-cluster `

  --task-definition cruise-finder-task:73 `

  --launch-type FARGATE `

  --network-configuration "awsvpcConfiguration={subnets=[subnet-0a975322c55a6bd97],securityGroups=[sg-0e1769b0d4a2b1d4e],assignPublicIp=ENABLED}" `

  --region us-west-2

```

### Scheduled Task Rollback (After Day 5)

If issues arise after switching scheduled task:

```powershell

# Revert EventBridge rule to previous revision
aws events put-targets `

  --rule run-cruise-finder-daily `

  --targets '[{"Id":"CruiseFinderTask","Arn":"arn:aws:ecs:us-west-2:491696534851:cluster/cruise-finder-cluster","RoleArn":"arn:aws:iam::491696534851:role/eventbridgeECSInvokeRole","EcsParameters":{"TaskDefinitionArn":"arn:aws:ecs:us-west-2:491696534851:task-definition/cruise-finder-task:73","LaunchType":"FARGATE","NetworkConfiguration":{"awsvpcConfiguration":{"Subnets":["subnet-0a975322c55a6bd97"],"SecurityGroups":["sg-0e1769b0d4a2b1d4e"],"AssignPublicIp":"ENABLED"}}}}]' `

  --region us-west-2

Write-Host "✅ Rolled back to Secrets Manager mode"

```

---

## ✅ Success Criteria

Migration is successful when ALL these conditions are met:

- [x] **Prerequisites**: Parameter Store infrastructure ready (Phase 1)

- [ ] **Day 1**: `parameter_store.py` created and tested locally

- [ ] **Day 2**: Dual-mode support added, both modes tested locally

- [ ] **Day 3**: IAM updated, deployed, Secrets Manager baseline confirmed

- [ ] **Day 4**: Switched to Parameter Store, manual test successful

- [ ] **Day 5-7**: Scheduled task updated, 3+ days stable

- [ ] **Monitoring**: No errors in CloudWatch logs

- [ ] **Validation**: cruise-viewer team confirms no data issues

- [ ] **Ready**: Proceed to cruise_admin migration (Phase 3)

**Final verification**:

```powershell

# Confirm Parameter Store in use
aws logs filter-log-events `

  --log-group-name /ecs/cruise-finder `

  --filter-pattern "Parameter Store" `

  --start-time $((Get-Date).AddDays(-1).ToUniversalTime().ToString('s') + '000') `

  --region us-west-2 `

  --max-items 5

```

Expected: Recent entries showing "✅ AWS credentials loaded from Parameter Store"

---

## 📊 Expected Outcomes

### Cost

- **Before**: AWS Secrets Manager ~$0.40/month

- **After**: AWS Systems Manager Parameter Store $0.00/month (free tier)

- **Savings**: ~$5/year

### Performance

- **Latency**: Similar or slightly better (~50-100ms vs ~100-200ms)

- **Reliability**: Same (both services highly available)

- **Operational**: Easier management, better integration

### Architecture

- ✅ cruise_finder secrets isolated (AWS credentials only)

- ✅ cruise_admin secrets separated (Auth0 credentials)

- ✅ No functional changes to application behavior

- ✅ Foundation for Auth0 caching (later phases)

---

**Questions?** See `../cruise-apps/REVISED_MIGRATION_PLAN.md` for context
