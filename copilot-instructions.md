<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit the VS Code Copilot documentation. -->

# cruise_finder - Lindblad Expeditions Trip Scraper

**Project Type**: Python web scraper deployed as AWS ECS Fargate task  
**Purpose**: Scrape Lindblad Expeditions cruise availability, save to S3, invalidate CloudFront cache  
**Infrastructure**: Terraform (AWS ECS, ECR, CloudWatch, EventBridge, S3, CloudFront)  
**Deployment**: Docker container on ECS Fargate, scheduled via EventBridge (every 3 days)  
**Region**: us-west-2 (all AWS resources)

## Core Technology Stack

- **Language**: Python 3.11+
- **Dependencies**: boto3 (AWS SDK), requests, playwright (web scraping)
- **Infrastructure**: Terraform for AWS resources
- **Container**: Docker for ECS Fargate deployment
- **Orchestration**: AWS ECS Fargate with EventBridge scheduling
- **Storage**: S3 (mytripdata8675309), Terraform state (cruise-finder-tfstate)
- **CDN**: CloudFront distribution for serving trip data
- **Authentication**: IAM roles (no access keys, no secrets manager)

## Development Principles

### Communication Rules
- Keep explanations concise and focused
- Avoid printing full command outputs unless debugging
- State skipped steps briefly (e.g., "No action needed")
- Don't explain project structure unless asked
- **NEVER suggest terminal commands without asking the user first** - especially destructive operations like file deletion
- When user says to proceed with a task, execute it - don't ask for permission again

### Python Environment
- Use virtual environment: `python -m venv .venv`
- Activate: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Unix)
- Install dependencies: `pip install -r requirements.txt`
- Always use configured Python environment (configure_python_environment tool)
- Freeze dependencies: `pip freeze > requirements.txt` after adding packages

### Development Rules

**General**:
- Use current directory as working directory unless specified otherwise
- **PowerShell Commands**: ALWAYS use PowerShell syntax (`;` not `&&`, `cd` not directory separator in same command)
  - ❌ WRONG: `cd infra && terraform plan` (Unix syntax)
  - ✅ CORRECT: `cd infra; terraform plan` (PowerShell syntax)
  - ✅ BETTER: Separate commands or use full paths
- When writing Markdown, ensure headings and lists have blank lines above and below (linting rules)
- Markdown linting during pre-commit: Always run get_errors on all markdown files and fix before committing
- **Markdown Linting**: When encountering many linting errors, use Python/PowerShell scripts to fix systematically rather than manual replace_string_in_file calls
- Project name: "cruise_finder" or "Lindblad Cruise Finder" - be consistent

**Python-Specific**:
- Python version: 3.11+ (matches Dockerfile)
- Always use virtual environment for local development
- Use boto3 for all AWS operations (S3, CloudFront, ECS)
- Use playwright for web scraping (headless browser automation)
- No hardcoded credentials - use IAM roles (ECS task role)
- Test locally by configuring AWS credentials via AWS CLI profile

**Terraform/Infrastructure**:
- All Terraform files in `infra/` directory
- Always run `terraform fmt` in `infra/` before committing Terraform changes
- Region: us-west-2 for all AWS resources (never use us-east-1)
- IAM naming convention: `terraform-lcf-*` (lcf = Lindblad Cruise Finder)
- Never give terraform IAM user permission to modify its own policies (security principle)
- Terraform state stored in S3: `cruise-finder-tfstate`
- Manual IAM policy updates via AWS Console only (see `infra/setup/` for procedures)

**Architecture/Deployment**:
- ECS Fargate task (no Lambda, no EC2)
- Docker container built from Dockerfile at project root
- Container pushed to ECR: `cruise-finder` repository
- Scheduled execution via EventBridge (every 3 days at 4:00 AM MST)
- Data output: S3 bucket `mytripdata8675309` → CloudFront invalidation
- CloudWatch Logs: `/ecs/cruise-finder` (7-day retention)
- No secrets needed (IAM role-based authentication only)

**Code Organization**:
- Application code in `src/` directory
- Entry point: `src/main.py`
- Utilities: `src/category_parser.py`, `src/departure_parser.py`, `src/trip_parser.py`, `src/save_trips.py`
- Tests in `tests/` directory
- Output files in `output/` directory (gitignored)
- Infrastructure in `infra/` directory
- Documentation in project root (README.md, MIGRATION_GUIDE.md, etc.)

**Docker/Container**:
- Base image: `python:3.11-slim`
- Installs Playwright with system dependencies
- Sets PYTHONPATH to include `/app/src`
- Default command: `python -m src.main`
- Build command: `docker build -t cruise-finder:latest .`
- Multi-stage builds not currently used (single stage)

**AWS Services Used**:
- ECS Fargate: Container orchestration
- ECR: Container registry
- EventBridge: Scheduled task execution
- CloudWatch Logs: Application logging
- S3: Trip data storage
- CloudFront: CDN for serving trip data
- IAM: Role-based authentication
- SQS: Dead letter queue for failed EventBridge invocations

**Cost Optimization**:
- ECS Fargate: Pay per task execution (minimal cost for 3-day schedule)
- S3: Free tier covers usage
- CloudFront: Free tier covers usage
- CloudWatch Logs: 7-day retention keeps costs minimal
- No Secrets Manager ($0.40/month saved by using IAM roles)
- No RDS/MongoDB (no database needed for this scraper)

**Migration/Cleanup History**:
- ✅ Phase 0 (Nov 23, 2025): Removed MRB-contaminated IAM policies, consolidated to 5 clean terraform-lcf-* policies
- ✅ Secrets Manager removal: Eliminated unused aws_secrets.py, simplified to IAM role authentication
- See MIGRATION_GUIDE.md and SECRETS_MANAGER_USAGE.md for historical context

### Testing Strategy

**Local Testing**:
- Configure Python environment: Use `configure_python_environment` tool
- Install dependencies: `pip install -r requirements.txt`
- Run syntax checks: `python -m py_compile src/*.py`
- Test imports: `python -c "import sys; sys.path.insert(0, 'src'); from main import main"`
- Test AWS connectivity: Ensure AWS CLI profile configured (`terraform` profile recommended)
- Run scraper locally: `python -m src.main` (requires AWS credentials)

**Unit Tests**:
- Test framework: pytest (if added)
- Test directory: `tests/`
- Existing tests: `test_departure_filter.py`, `test_departure.py`, `test_trip_parser.py`
- Run tests: `pytest tests/` (when pytest is configured)

**Integration Testing**:
- Docker build: `docker build -t cruise-finder:latest .`
- Docker run locally: `docker run --rm -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... cruise-finder:latest`
- Manual ECS task run: Use AWS CLI to trigger task and monitor logs
- CloudWatch Logs: Check `/ecs/cruise-finder` for execution logs

**Deployment Testing**:
- Terraform plan: `cd infra; terraform plan` (PowerShell syntax)
- Build and push to ECR: See README.md deployment section
- Manual task execution: `aws ecs run-task --cluster cruise-finder-cluster ...`
- Verify S3 upload: Check `s3://mytripdata8675309/trip_list.json`
- Verify CloudFront invalidation: Check distribution `E22G95LIEIJY6O`

---

## PRE-COMMIT CHECKLIST

When the user indicates readiness to commit, execute this checklist systematically:

### 1. Review Uncommitted Files

```powershell
git status
```

- Review each file and categorize:
  - **Keep**: Essential code, config, documentation
  - **Delete**: Temporary files, test data, build artifacts, `__pycache__/`, `.pyc` files
- Delete any files that don't belong in the repository
- Confirm `.gitignore` is properly excluding:
  - `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
  - `.venv/`, `venv/`, `env/`
  - `output/` (local output directory)
  - `.env` (if any exist - should not be committed)
  - `.DS_Store`, `.vscode/`, IDE-specific files

### 2. Security Audit

- Search all files for hardcoded secrets, passwords, API keys, tokens, AWS account IDs
- Check Python files: `src/**/*.py`, `tests/**/*.py`
- Check documentation: `*.md`, `*.txt`
- Check configuration: `*.json`, `*.yaml`, `*.toml`, `.env.example`
- Check Terraform: `infra/**/*.tf` (look for exposed credentials)
- Verify all AWS authentication uses IAM roles (no hardcoded keys)
- Confirm no sensitive AWS account numbers in public docs (use placeholders if needed)
- Check Dockerfile for exposed secrets in ENV or ARG directives

### 3. Code Quality Check

**Python**:

```powershell
# Syntax check all Python files
python -m py_compile src/*.py
python -m py_compile tests/*.py

# If pytest configured, run tests
pytest tests/ --tb=short

# Check imports work
python -c "import sys; sys.path.insert(0, 'src'); from main import main; print('✅ Imports OK')"
```

**Terraform**:

```powershell
cd infra
terraform fmt -check
# If formatting needed:
terraform fmt
terraform validate
cd ..
```

**Docker**:

```powershell
# Build test (optional, can be slow)
docker build -t cruise-finder:test . --no-cache
```

### 4. Markdown Linting

**CRITICAL**: Always check and fix markdown linting errors before commit:

```powershell
# Check for markdown errors using VS Code get_errors tool
# Fix all MD* errors (blank lines, heading spacing, etc.)
```

Common issues:
- **MD032**: Lists need blank lines before/after
- **MD022**: Headings need blank lines before/after  
- **MD024**: Duplicate headings (add context to make unique)
- **MD009**: Trailing spaces
- **MD031**: Fenced code blocks need blank lines

### 5. Documentation Review

- Check `README.md` for accuracy and completeness
- Update `MIGRATION_GUIDE.md` if migration-related changes
- Update `SECRETS_MANAGER_USAGE.md` if secrets/IAM changes
- Review `infra/setup/` documentation if IAM policy changes
- Ensure commands and examples are current (especially PowerShell syntax)
- Update architecture descriptions if infrastructure changed
- Remove duplicate information - link instead of copy

### 6. Prepare Changelog Entry

- Read existing `CHANGELOG.md` (create if missing)
- Add new entry with today's date
- Use format: `## [Version] - YYYY-MM-DD` or `## [Unreleased] - YYYY-MM-DD`
- Categories: Added, Changed, Fixed, Removed, Security, Infrastructure
- Write clear descriptions of changes
- Include technical details for developers
- Multiple same-day entries: Use unique titles or context (e.g., `### Changed - IAM Cleanup`)

Example:

```markdown
## [Unreleased] - 2025-11-23

### Changed - IAM Cleanup
- Removed 9 MRB-contaminated policies from terraform user
- Consolidated to 5 clean terraform-lcf-* policies
- Improved security by preventing self-modification

### Removed - Secrets Manager
- Deleted unused aws_secrets.py module
- Simplified to IAM role-based authentication
- Updated Terraform IAM policy to remove Secrets Manager permissions
```

### 7. Update Copilot Instructions (This File)

- Review conversation for patterns, corrections, or issues discovered
- Add new development rules based on lessons learned
- Update naming conventions if any inconsistencies found
- Document new tooling or workflow patterns
- Add project-specific conventions discovered during development
- Remove outdated or superseded instructions
- Update version numbers, dates, or status indicators as needed

### 8. Commit & Push

```powershell
# Stage all changes
git add .

# Verify what's being committed
git status

# Write descriptive commit message
git commit -m "<type>(<scope>): <subject>"

# Push to remote
git push origin master
```

**Commit Message Format**:
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `infra`
- Scope: `iam`, `secrets`, `terraform`, `docker`, `scraper`, `docs`
- Subject: Clear, imperative mood description

**Examples**:

```
feat(scraper): add retry logic for failed web requests
fix(docker): correct Playwright installation in Dockerfile  
docs: update README with Phase 0 IAM cleanup procedures
infra(terraform): remove Secrets Manager permissions from ECS task
chore: update copilot instructions for Python environment
refactor(iam): consolidate to 5 clean terraform-lcf policies
```

### Execution Notes

- Execute checklist items sequentially
- Report status after each major step
- Ask for user confirmation before destructive actions (file deletion, etc.)
- If issues are found, fix them before proceeding to commit
- Keep the user informed of progress without excessive verbosity
- If any step fails, stop and resolve before continuing

## Common Mistakes to Avoid

### PowerShell Environment Mistakes
- ❌ **NEVER use Unix shell syntax** (`&&`, `||`) in PowerShell commands
- ❌ **NEVER use forward slashes in cd commands** like `cd infra && terraform plan`
- ✅ **ALWAYS use PowerShell syntax**: semicolon (`;`) for command chaining
- ✅ **ALWAYS test command syntax** before suggesting to user

### File Management Mistakes
- ❌ **NEVER delete files without explicit user confirmation** - especially documentation files
- ❌ **NEVER assume a file is "not needed"** without asking the user
- ✅ **ALWAYS ask before deleting** any file, even if it seems temporary or unused
- ✅ **READ FILE CONTENT** before making assumptions about its purpose

### Pre-Commit Process Mistakes
- ❌ **NEVER skip linting checks** - markdown linting errors are NEVER acceptable in commits
- ❌ **NEVER use manual edits for systematic issues** - use scripts for bulk fixes
- ❌ **NEVER suggest committing** without completing ALL checklist steps
- ✅ **ALWAYS verify all markdown files are lint-clean** before staging
- ✅ **ALWAYS use Python/PowerShell scripts** for fixing multiple similar linting errors
- ✅ **ALWAYS check file contents** after user makes changes (files may have been edited)

### Tool Usage Mistakes
- ❌ **NEVER run destructive tool calls in parallel** - ask first, then execute sequentially
- ❌ **NEVER assume the user wants something deleted** based on the filename alone
- ✅ **ALWAYS wait for user confirmation** on destructive actions
- ✅ **ALWAYS read current file state** before editing (user may have made changes)

### Communication Mistakes
- ❌ **NEVER ask redundant questions** - if user says "proceed", don't ask "should I proceed?"
- ❌ **NEVER stop mid-checklist** to ask permission for the next step (they already said go)
- ✅ **EXECUTE the checklist systematically** when user says "prepare to commit"
- ✅ **ASK ONLY for truly destructive or ambiguous actions** (like deleting files)

### Markdown Linting Mistakes
- ❌ **NEVER make 50+ individual replace_string_in_file calls** to fix linting errors
- ❌ **NEVER ignore multiple blank line errors** (they count as many errors)
- ✅ **USE Python scripts with regex** to fix systematic markdown issues in one operation
- ✅ **COLLAPSE multiple operations** into single script execution for efficiency

### Context Awareness Mistakes
- ❌ **NEVER forget the shell environment** - this project uses PowerShell on Windows
- ❌ **NEVER mix Unix and Windows command syntax**
- ❌ **NEVER run commands without checking current directory** - commands may fail or affect wrong location
- ✅ **CHECK the shell type** in context before suggesting commands
- ✅ **ALWAYS use PowerShell-compatible syntax** for this project
- ✅ **ALWAYS check terminal context for current working directory** before running commands
- ✅ **CHANGE to correct directory first** if command requires specific location (e.g., `cd infra` before `terraform plan`)
