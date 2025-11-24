# Phase 0: Terraform IAM Permission Cleanup - Manual Setup

**Date**: November 23, 2025  
**Purpose**: Clean up terraform user permissions - remove MRB contamination  
**Method**: Manual policy creation via AWS Console (no automation)  
**Security Note**: We intentionally don't give the terraform user permission to modify its own IAM policies

---

## 🎯 Goal

Replace 10 scattered policies (some with MRB contamination) with 5 clean, focused policies for cruise_finder only.

**From**: 10 policies with mixed cruise_finder + MRB permissions  
**To**: 5 clean policies for cruise_finder only

---

## 📋 Summary of Changes

### Policies to Remove (MRB Contamination)

- ❌ `terraform-rds` - MRB database (cruise_finder has no RDS)
- ❌ `terraform-lambda-deploy` - MRB Lambda functions
- ❌ `terraform-s3-policy` - Only for MRB S3 bucket
- ❌ `terraform-assume-role-policy` - MRB Lambda role
- ❌ `terraform-infra-policy` - Mixed LCF + MRB S3 buckets
- ❌ `terraform-read-current-state` - Too broad, unfocused
- ❌ `terraform-pass-roll` - Has MRB Lambda role
- ❌ `terraform-lcf-permissions` - Tiny policy, merging into research
- ❌ `terraform-task-access` - Renaming to terraform-lcf-task-policy-mgmt

-### New Clean Policies (cruise_finder only)

- ✅ `terraform-lcf-infrastructure` - Core IaC (ECS, ECR, CloudWatch, etc.)
- ✅ `terraform-lcf-state-management` - Terraform state bucket access
- ✅ `terraform-lcf-task-policy-mgmt` - ECS task IAM policy versioning
- ✅ `terraform-lcf-research` - Read-only debugging permissions
- ✅ `terraform-lcf-ssm` - Already exists and clean, keep as-is

---

## 📝 Manual Setup Instructions

### Step 1: Create New IAM Policies (AWS Console)

Navigate to: **AWS Console → IAM → Policies → Create policy**

For each JSON file in this directory, create a new policy:

#### 1.1 Create `terraform-lcf-infrastructure`

1. Click **"Create policy"**
2. Click **"JSON"** tab
3. Copy contents from `terraform-lcf-infrastructure.json`
4. Paste into JSON editor
5. Click **"Next"**
6. **Policy name**: `terraform-lcf-infrastructure`
7. **Description**: `Core IaC permissions for cruise_finder ECS Fargate application`
8. Click **"Create policy"**

#### 1.2 Create `terraform-lcf-state-management`

1. Click **"Create policy"**
2. Click **"JSON"** tab
3. Copy contents from `terraform-lcf-state-management.json`
4. Paste into JSON editor
5. Click **"Next"**
6. **Policy name**: `terraform-lcf-state-management`
7. **Description**: `Terraform state bucket access for cruise_finder`
8. Click **"Create policy"**

#### 1.3 Create `terraform-lcf-task-policy-mgmt`

1. Click **"Create policy"**
2. Click **"JSON"** tab
3. Copy contents from `terraform-lcf-task-policy-mgmt.json`
4. Paste into JSON editor
5. Click **"Next"**
6. **Policy name**: `terraform-lcf-task-policy-mgmt`
7. **Description**: `ECS task IAM policy versioning for cruise_finder`
8. Click **"Create policy"**

#### 1.4 Create `terraform-lcf-research`

1. Click **"Create policy"**
2. Click **"JSON"** tab
3. Copy contents from `terraform-lcf-research.json`
4. Paste into JSON editor
5. Click **"Next"**
6. **Policy name**: `terraform-lcf-research`
7. **Description**: `Read-only permissions for debugging and enhancement work`
8. Click **"Create policy"**

---

### Step 2: Attach New Policies to terraform User

Navigate to: **AWS Console → IAM → Users → terraform**

1. Click **"Permissions"** tab
2. Click **"Add permissions"** → **"Attach policies directly"**
3. Search for and select:
   - ✅ `terraform-lcf-infrastructure`
   - ✅ `terraform-lcf-state-management`
   - ✅ `terraform-lcf-task-policy-mgmt`
   - ✅ `terraform-lcf-research`
4. Click **"Add permissions"**

**Verify**: The terraform user should now have **14 total policies** (10 old + 4 new + terraform-lcf-ssm already exists)

---

### Step 3: Test with New Policies

Before removing old policies, verify everything works:

#### 3.1 Test Terraform

```powershell
cd C:\Users\Mike\Documents\Python\cruise_finder\infra

# Test plan (read-only)
terraform plan

# If plan succeeds, test apply (only if safe changes)
terraform apply
```

**Expected**: No permission errors, successful plan/apply

#### 3.2 Test Python Application

```powershell
cd C:\Users\Mike\Documents\Python\cruise_finder

# Test imports
C:/Users/Mike/Documents/Python/cruise_finder/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); from main import invalidate_cloudfront_cache; from save_trips import save_to_json; print('✅ All imports successful')"

# Test S3 client
C:/Users/Mike/Documents/Python/cruise_finder/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); from save_trips import s3, S3_BUCKET_NAME; print(f'✅ S3 client initialized for bucket: {S3_BUCKET_NAME}')"
```

**Expected**: No errors, successful initialization

---

### Step 4: Detach Old Policies (Only After Testing)

⚠️ **WARNING**: Only proceed if Step 3 tests pass!

Navigate to: **AWS Console → IAM → Users → terraform → Permissions**

For each old policy, click the checkbox and then click **"Remove"**:

1. ❌ Remove `terraform-rds`
2. ❌ Remove `terraform-infra-policy`
3. ❌ Remove `terraform-task-access`
4. ❌ Remove `terraform-assume-role-policy`
5. ❌ Remove `terraform-lcf-permissions`
6. ❌ Remove `terraform-read-current-state`
7. ❌ Remove `terraform-s3-policy`
8. ❌ Remove `terraform-pass-roll`
9. ❌ Remove `terraform-lambda-deploy`

-**Keep these policies**:

- ✅ `terraform-lcf-infrastructure` (new)
- ✅ `terraform-lcf-state-management` (new)
- ✅ `terraform-lcf-task-policy-mgmt` (new)
- ✅ `terraform-lcf-research` (new)
- ✅ `terraform-lcf-ssm` (existing, clean)

**Final count**: terraform user should have **5 policies total**

---

### Step 5: Retest Everything

After detaching old policies, immediately retest:

#### 5.1 Retest Terraform

```powershell
cd C:\Users\Mike\Documents\Python\cruise_finder\infra
terraform plan
terraform apply
```

**If this fails**: Immediately re-attach the old policies and investigate

#### 5.2 Retest Python Application

```powershell
cd C:\Users\Mike\Documents\Python\cruise_finder
C:/Users/Mike/Documents/Python/cruise_finder/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); from save_trips import s3; print('✅ Still works')"
```

#### 5.3 Monitor for 1 Week

- Run scheduled ECS task and verify it completes successfully
- Check CloudWatch logs for errors
- Verify S3 uploads still work
- Verify CloudFront invalidations still work

---

### Step 6: Delete Old Policies (Optional - After 1 Week)

⚠️ **CAUTION**: Only delete after confirming everything works for at least 1 week!

Navigate to: **AWS Console → IAM → Policies**

For each old policy, search by name, then:

1. Check if policy is attached to any users/roles
2. If not attached, click policy name
3. Click **"Actions"** → **"Delete"**
4. Confirm deletion

**Note**: You may need to delete old policy versions first:

1. Click policy name
2. Click **"Policy versions"** tab
3. Delete all old versions (keep only v1)
4. Then delete the policy

-**Policies to delete**:

- `terraform-rds`
- `terraform-infra-policy`
- `terraform-task-access`
- `terraform-assume-role-policy`
- `terraform-lcf-permissions`
- `terraform-read-current-state`
- `terraform-s3-policy`
- `terraform-pass-roll`
- `terraform-lambda-deploy`

---

## ✅ Checklist

- [ ] **Step 1**: Created 4 new policies in AWS Console
- [ ] **Step 2**: Attached new policies to terraform user
- [ ] **Step 3**: Tested terraform plan/apply successfully
- [ ] **Step 3**: Tested Python application successfully
- [ ] **Step 4**: Detached 9 old policies from terraform user
- [ ] **Step 5**: Retested terraform successfully
- [ ] **Step 5**: Retested Python application successfully
- [ ] **Step 5**: Monitored for 1 week - no issues
- [ ] **Step 6**: Deleted old policies (optional)

---

## 📊 Before vs After

### Before (10 policies - messy)

```text
terraform-rds (MRB)
terraform-infra-policy (mixed LCF + MRB)
terraform-lcf-ssm ✅
terraform-task-access (poor naming)
terraform-assume-role-policy (MRB Lambda)
terraform-lcf-permissions (tiny)
terraform-read-current-state (huge, unfocused)
terraform-s3-policy (MRB only)
terraform-pass-roll (mixed)
terraform-lambda-deploy (MRB)
```

### After (5 policies - clean)

```text
terraform-lcf-infrastructure ✅
terraform-lcf-state-management ✅
terraform-lcf-ssm ✅
terraform-lcf-task-policy-mgmt ✅
terraform-lcf-research ✅
```

**Result**: Clean, maintainable, zero MRB contamination! 🎉

---

## 🚨 Rollback Procedure

If anything breaks after Step 4:

1. **Immediately re-attach old policies** via AWS Console
2. Navigate to: **IAM → Users → terraform → Permissions**
3. Click **"Add permissions"** → **"Attach policies directly"**
4. Search for and re-attach the needed old policies
5. Test terraform/application again
6. Investigate what permission was missing in the new policies

---

## 📝 Policy Descriptions

### terraform-lcf-infrastructure

**Purpose**: Core infrastructure-as-code permissions  

**Resources**: ECS, ECR, CloudWatch Logs, EventBridge, IAM roles/policies, CloudFront, VPC networking, S3 (mytripdata8675309), SQS  

**Scope**: Create, update, delete cruise_finder infrastructure

### terraform-lcf-state-management

**Purpose**: Terraform state file access  

**Resources**: S3 (cruise-finder-tfstate bucket)  

**Scope**: Read/write state, manage state bucket settings

### terraform-lcf-task-policy-mgmt

**Purpose**: ECS task IAM policy versioning  

**Resources**: IAM policy (ecs-cruise-finder-task-access)  

**Scope**: Create/delete policy versions for ECS task role

### terraform-lcf-research

**Purpose**: Read-only access for debugging and enhancement  

**Resources**: IAM, ECS, ECR, Logs, Events, EC2, CloudFront, S3, SQS  

**Scope**: Describe, list, get (no create/update/delete)

### terraform-lcf-ssm

**Purpose**: Parameter Store access  

**Resources**: SSM parameters (cruise-finder/prod/*)  

**Scope**: Put, get, delete parameters for cruise_finder

---

## 🔐 Security Principle

**Why manual setup?**

We intentionally do NOT give the terraform user permission to create/attach/detach IAM policies to itself. This follows the principle of least privilege:

- ✅ terraform user can manage infrastructure (ECS, ECR, etc.)
- ✅ terraform user can version ECS task policies
- ❌ terraform user CANNOT modify its own permissions
- ❌ terraform user CANNOT attach policies to itself

**Result**: Prevents privilege escalation and requires human approval for IAM changes.
