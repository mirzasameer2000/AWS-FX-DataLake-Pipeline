# AWS-FX-DataLake-Pipeline
Serverless FX data lake pipeline on AWS (Lambda + Step Functions + S3 + Athena) that ingests daily exchange rates from Frankfurter API and enables SQL analytics.

This repository documents an end-to-end **serverless Data Engineering mini project** built on AWS.  
The pipeline ingests **exchange rates** from the **Frankfurter API**, stores raw data in **Amazon S3** using a partitioned data lake structure, orchestrates ingestion and metadata refresh with **AWS Step Functions**, and enables SQL analytics using **Amazon Athena**.

> ✅ **Next step (not enabled in this lab):** Add **EventBridge Scheduler** to run the Step Functions workflow automatically on a daily schedule.

---

## Table of Contents

- [Project Goal](#project-goal)
- [Architecture](#architecture)
- [Services Used](#services-used)
- [Prerequisites](#prerequisites)
- [Step-by-Step Implementation](#step-by-step-implementation)
  - [Step 1 — Create the S3 bucket](#step-1--create-the-s3-bucket)
  - [Step 2 — Create the Lambda function (Python 3.13)](#step-2--create-the-lambda-function-python-313)
  - [Step 3 — Test Lambda and verify S3 outputs](#step-3--test-lambda-and-verify-s3-outputs)
  - [Step 4 — Set up Athena query results location](#step-4--set-up-athena-query-results-location)
  - [Step 5 — Create Athena database and table](#step-5--create-athena-database-and-table)
  - [Step 6 — Create the Step Functions workflow](#step-6--create-the-step-functions-workflow)
  - [Step 7 — Run the pipeline manually](#step-7--run-the-pipeline-manually)
  - [Step 8 — Query results in Athena](#step-8--query-results-in-athena)
- [Next Step — Add Scheduling (Optional)](#next-step--add-scheduling-optional)
- [Repo Structure](#repo-structure)
- [Screenshots Checklist](#screenshots-checklist)
- [Cost Control Notes](#cost-control-notes)

---

## Project Goal

Build a beginner-friendly AWS data pipeline that demonstrates **core AWS essentials for Data Engineering**:

- ingest external data (API)
- store it in a data lake (S3)
- orchestrate runs (Step Functions)
- make data queryable (Athena)
- document how scheduling would be added (EventBridge Scheduler)

---

## Architecture

**Frankfurter API → AWS Lambda (Python 3.13) → Amazon S3 (raw lake, partitioned) → AWS Step Functions → Amazon Athena**

---

## Services Used

- **Amazon S3**: data lake storage
- **AWS Lambda (Python 3.13)**: ingestion/processing function
- **AWS Step Functions**: orchestration (Lambda invoke + Athena partition repair)
- **Amazon Athena**: SQL querying of partitioned data in S3
- **IAM Role (LabRole)**: permissions to run services (Learner Lab compatible)
- **CloudWatch Logs**: Lambda execution logs

---

## Prerequisites

- AWS Academy Learner Lab started
- Region: **N. Virginia (us-east-1)**
- A role available (commonly **LabRole**) to allow Lambda, Step Functions, S3, Athena access

---

## Step-by-Step Implementation

### Step 1 — Create the S3 bucket

1. AWS Console → search **S3**
2. Click **Create bucket**
3. Region: **us-east-1**
4. Bucket name used in this project:
   - `fx-lake-sameer-24169956`
5. Keep **Block all public access** enabled
6. Create folders inside the bucket:
   - `raw/`
   - `athena-results/`

✅ This bucket stores both raw ingested data and Athena query outputs.

---

### Step 2 — Create the Lambda function (Python 3.13)

1. AWS Console → search **Lambda**
2. Click **Create function**
3. Name: `fx_ingest_rates` (or your chosen name)
4. Runtime: **Python 3.13**
5. Architecture: **x86_64**
6. Permissions:
   - Use existing execution role: **LabRole** (recommended in Learner Lab)
7. Create function

#### Configure Lambda environment variables (recommended)
Configuration → Environment variables:

- `BUCKET_NAME` = `fx-lake-sameer-24169956`
- `RAW_PREFIX` = `raw`
- `BASE` = `EUR`
- `SYMBOLS` = `USD,GBP,CHF,HUF,PKR,CAD,AUD,INR,SEK` 

#### Lambda code
- Stored in: `lambda/lambda_function.py`
- Uses the Frankfurter API and writes:
  - `rates.ndjson` (long-format rows)
  - `raw_response.json` (full response)

---

### Step 3 — Test Lambda and verify S3 outputs

1. In Lambda → click **Test**
2. Create test event:
   - Name: `TestLatestRates`
   - JSON:
     ```json
     { "date": "latest" }
     ```
3. Run test

✅ Verify in S3:
- `raw/dt=YYYY-MM-DD/rates.ndjson`
- `raw/dt=YYYY-MM-DD/raw_response.json`

---

### Step 4 — Set up Athena query results location

In Athena, the query editor must have a query result output folder configured.

Set it to:
- `s3://fx-lake-sameer-24169956/athena-results/`

✅ This ensures Athena can write query output files to S3.

---

### Step 5 — Create Athena database and table

All SQL files are stored in `athena/`.

#### 5.1 Create database
File: `athena/01_create_db.sql`
```sql
CREATE DATABASE IF NOT EXISTS fx_lake;
