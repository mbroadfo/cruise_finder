# Phase 0: IAM Cleanup - Quick Start

## 📁 Files in This Directory

- **README.md** - Complete step-by-step instructions (start here!)
- **PHASE_0_IAM_CLEANUP.md** - Detailed background and technical docs
- **terraform-lcf-infrastructure.json** - Policy for ECS, ECR, CloudWatch, etc.
- **terraform-lcf-state-management.json** - Policy for Terraform state bucket
- **terraform-lcf-task-policy-mgmt.json** - Policy for ECS task IAM versioning
- **terraform-lcf-research.json** - Policy for read-only debugging

## 🚀 Quick Start (5 Minutes)

### What You'll Do

1. Create 4 new IAM policies in AWS Console (copy/paste JSON)
2. Attach them to the `terraform` IAM user
3. Test terraform and Python app
4. Remove 9 old MRB-contaminated policies
5. Retest everything

### Step 1: Create Policies (AWS Console)

Navigate to: **IAM → Policies → Create policy**

For each JSON file, click "Create policy" → "JSON" tab → paste contents:

1. ✅ `terraform-lcf-infrastructure` (from terraform-lcf-infrastructure.json)
2. ✅ `terraform-lcf-state-management` (from terraform-lcf-state-management.json)
3. ✅ `terraform-lcf-task-policy-mgmt` (from terraform-lcf-task-policy-mgmt.json)
4. ✅ `terraform-lcf-research` (from terraform-lcf-research.json)

### Step 2: Attach to terraform User

Navigate to: **IAM → Users → terraform → Permissions → Add permissions**

Select and attach all 4 new policies created above.

### Step 3: Test

```powershell
# Test terraform
cd C:\Users\Mike\Documents\Python\cruise_finder\infra
terraform plan

# Test Python
cd ..
C:/Users/Mike/Documents/Python/cruise_finder/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); from save_trips import s3; print('✅ Works')"
```

### Step 4: Remove Old Policies

Navigate to: **IAM → Users → terraform → Permissions**

Remove these 9 policies (click checkbox → Remove):

- ❌ terraform-rds
- ❌ terraform-infra-policy
- ❌ terraform-task-access
- ❌ terraform-assume-role-policy
- ❌ terraform-lcf-permissions
- ❌ terraform-read-current-state
- ❌ terraform-s3-policy
- ❌ terraform-pass-roll
- ❌ terraform-lambda-deploy

### Step 5: Retest

Rerun tests from Step 3. If anything fails, immediately re-attach old policies!

---

## 📋 Final State

terraform user should have exactly **5 policies**:

- ✅ terraform-lcf-infrastructure
- ✅ terraform-lcf-state-management
- ✅ terraform-lcf-ssm (already existed)
- ✅ terraform-lcf-task-policy-mgmt
- ✅ terraform-lcf-research

---

## 🔐 Security Note

We **intentionally do NOT** automate this with scripts because:

- terraform user should NOT be able to modify its own IAM permissions
- Prevents privilege escalation
- Requires human review and approval for IAM changes
- Follows principle of least privilege

---

## ❓ Need Help?

See **README.md** for complete instructions with screenshots and troubleshooting.
