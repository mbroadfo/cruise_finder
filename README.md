# Cruise Finder - Backend Parsing and Infrastructure

Cruise Finder is a resilient, headless data collection application for scraping and structuring Lindblad Expeditions trip data. It supports rich expedition metadata, category availability, and integrates fully with AWS for persistence and automation. It also powers the frontend UI for the Cruise Viewer application.

---

## ✨ Features Overview

* Extracts Lindblad trip metadata, departure dates, cabin category availability, and pricing.
* Eliminates waitlisted cabins and non-bookable trips.
* Automatically updates trip data daily.
* Stores structured JSON to an S3 bucket for consumption by the Cruise Viewer frontend.
* Deploys with full CI/CD automation using GitHub Actions and Terraform.

---

## 📊 Parsing Architecture

### 1. `trip_parser.py`

* Launches the Lindblad expeditions page.
* Auto-expands the "Show More" button until all trips are visible.
* Iterates through each expedition and collects metadata including:

  * Trip name
  * Destinations
  * Thumbnail image
  * Booking URLs for departures

### 2. `departure_parser.py`

* Visits each booking URL for a given trip.
* Parses each departure date and the ship name.
* Collects the structured booking link for each departure instance.

### 3. `category_parser.py`

* Loads the cabin selection screen for a specific departure.
* Extracts cabin categories, decks, prices, cabin numbers, and availability.
* Applies intelligent exclusion rules:

  * Removes waitlisted categories.
  * Ignores categories with no availability.

All collected data is stored in a structured format:

```json
{
  "trip_name": "...",
  "destinations": "...",
  "departures": [
    {
      "start_date": "2025 May 23",
      "end_date": "2025 Jun 1",
      "ship": "Endurance",
      "categories": [ { ... } ]
    }
  ]
}
```

---

## ✨ CI/CD Pipeline

### GitHub Actions

* CI pipeline lints the Python code and validates Playwright tests.
* CD pipeline builds and pushes a Docker image to Amazon ECR.
* Image is deployed as a container task in AWS ECS.

### Secrets Management

* AWS Secrets Manager holds sensitive values like Auth0 tokens and AWS keys.
* These are injected via `inject_env_from_secrets()` and never hardcoded.

---

## ☁️ AWS Infrastructure (Terraform)

### Overview

Infrastructure is managed using declarative Terraform scripts.

### Modules:

* **ECS Cluster**: Hosts a Fargate container to run `cruise-finder` daily.
* **ECR Repo**: Stores built Docker images from GitHub Actions.
* **CloudWatch Logs**: Tracks all task output and failure events.
* **S3 Bucket**: Destination for parsed JSON data.
* **IAM Roles**: Grant fine-grained access for S3, Secrets Manager, and task execution.
* **CloudWatch Scheduled Rule**: Runs the ECS task every 24 hours.

### `main.tf` Highlights:

```hcl
resource "aws_ecs_task_definition" "cruise_finder" { ... }
resource "aws_cloudwatch_event_rule" "daily_schedule" { schedule_expression = "rate(24 hours)" }
resource "aws_s3_bucket" "trip_data" { bucket = "cruise-viewer-data" }
resource "aws_secretsmanager_secret" "auth_tokens" { name = "cruise-finder-secrets" }
```

---

## 📚 Usage

### Manual Run

```bash
poetry run python src/main.py
```

### Output

* JSON is saved to `output/trips.json` locally or to an S3 bucket in production mode.

---

## ⚡ Frontend Integration

* The Cruise Viewer UI loads this S3 data at startup.
* Trips, departures, and cabin categories are browsable and filterable.
* Favorite selections are managed in `cruise-admin` and synced via Auth0.

---

## 📚 Summary

Cruise Finder is a full-lifecycle expedition availability system built with robust scraping, secure AWS integration, and modern DevOps practices. It serves as the primary data pipeline for the Cruise Viewer experience.
