# 🇵🇪 Peru Construction Data Pipeline (AWS)

## 📌 Overview
End-to-end data engineering project that ingests, processes, and analyzes public datasets from Peru’s open data platform, focusing on construction activity (building licenses).

The pipeline is built on AWS and compares two ETL approaches:
- Serverless ETL using AWS Glue (Spark)
- Custom ETL using EC2 (Python)

---

## 🎯 Objectives
- Build a production-style data pipeline in AWS
- Compare Glue vs EC2 for ETL workloads
- Implement infrastructure as code (CloudFormation)
- Automate deployments with CI/CD (GitHub Actions)
- Demonstrate real-world data modeling and optimization

---

## 🧩 Architecture

```
API / Public Dataset
        ↓
     Lambda
        ↓
   S3 (raw layer)
        ↓
   ┌───────────────┬───────────────┐
   ↓               ↓
Glue (Spark)     EC2 (Python)
   ↓               ↓
   └──────→ S3 (processed - parquet)
                      ↓
                  Athena
```

---

## 🛠️ Tech Stack

- AWS S3 (Data Lake)
- AWS Lambda (Ingestion)
- AWS Glue (ETL - Spark)
- EC2 (Custom ETL - Python)
- Athena (Query layer)
- CloudWatch (Monitoring)
- CloudFormation (IaC)
- GitHub Actions (CI/CD)

---

## 📂 Repository Structure

```
.
├── app/
│   ├── lambda/
│   ├── glue/
│   ├── ec2_jobs/
│   └── shared/
│
├── infra/
│   └── cloudformation/
│
├── docs/
│   ├── architecture.md
│   ├── datasets.md
│   ├── cost-analysis.md
│   └── performance-comparison.md
│
├── tests/
├── .github/workflows/
└── README.md
```

---

## 📊 Data Sources

- Peru Open Data Platform (datosabiertos.gob.pe)
- Example datasets:
  - Building licenses (municipalities)
  - Urban development data

---

## 🔄 Data Layers

### Raw
- Original files as ingested
- Stored as CSV/JSON
- Partitioned by ingestion date

### Processed
- Cleaned and normalized
- Stored as Parquet
- Partitioned for performance

### Analytics
- Athena tables
- Aggregations and KPIs

---

## ⚙️ ETL Approaches

### 1. AWS Glue (Spark)
- Scalable, managed
- Good for large datasets
- Less control, higher cost

### 2. EC2 (Python)
- Flexible and customizable
- Cost-efficient for medium workloads
- Easier debugging

---

## 📈 KPIs (Example)

- Number of licenses per month
- Activity by district
- Growth trends in construction
- Distribution by project type

---

## 🚀 CI/CD

- GitHub Actions for:
  - Deploying Lambda
  - Deploying CloudFormation stacks
  - Running tests

---

## ☁️ Infrastructure (IaC)

Defined using CloudFormation:
- S3 buckets
- IAM roles
- Lambda functions
- Glue jobs
- Monitoring resources

## Local SAM Simulation And First Deploy

This repo now includes a first-pass SAM template for the raw-ingestion Lambda at `infra/cloudformation/raw_ingestion_template.yaml`.

The goal of the local flow is to simulate the Lambda as it will run on AWS:
- package the function with SAM
- run it inside a Docker container
- keep the same event contract
- mirror S3 writes to the local filesystem before the AWS stack exists

### Prerequisites

- AWS SAM CLI installed
- Docker installed
- Colima available for local Docker runtime on macOS

### Local Invoke Workflow

1. Start the container runtime:

```bash
colima start
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
```

2. Validate the SAM template:

```bash
sam validate --template-file infra/cloudformation/raw_ingestion_template.yaml
```

3. Build the Lambda package:

```bash
sam build --template-file infra/cloudformation/raw_ingestion_template.yaml
```

4. Invoke the function locally with the sample HTML dataset-page event:

```bash
sam local invoke RawIngestionFunction \
  --template-file infra/cloudformation/raw_ingestion_template.yaml \
  --env-vars infra/parameters/sam-local-env.json \
  --event infra/events/html-dataset-page.json
```

The local invoke uses `STORAGE_BACKEND=filesystem`, so artifacts are written to `/tmp/sam-local-output` inside the SAM Lambda container using the same key layout the S3 backend uses in AWS. That path is intentional: SAM mounts the source tree read-only, while `/tmp` is the writable area that matches Lambda runtime behavior.
If you use Colima, exporting `DOCKER_HOST` helps SAM talk to Colima's Docker socket directly instead of relying on Docker context discovery.

### First AWS Deploy

Deploy the first slice with SAM:

```bash
sam deploy --template-file infra/cloudformation/raw_ingestion_template.yaml
```

This first stack creates:
- one raw-ingestion Lambda
- one raw S3 bucket with block-public-access enabled
- IAM permissions for CloudWatch Logs and `s3:PutObject`

### Post-Deploy Smoke Test

1. Get the deployed function name:

```bash
aws cloudformation describe-stacks \
  --stack-name peru-construction-raw-ingestion-dev \
  --query "Stacks[0].Outputs[?OutputKey=='RawIngestionFunctionName'].OutputValue" \
  --output text
```

2. Invoke the Lambda with the same trusted-input payload:

```bash
aws lambda invoke \
  --function-name "$(aws cloudformation describe-stacks \
    --stack-name peru-construction-raw-ingestion-dev \
    --query "Stacks[0].Outputs[?OutputKey=='RawIngestionFunctionName'].OutputValue" \
    --output text)" \
  --payload fileb://infra/events/html-dataset-page.json \
  /tmp/raw-ingestion-response.json
```

3. Confirm the payload and manifest land in the raw bucket path emitted by the function response or by inspecting the stack output bucket.

---

## 📉 Cost & Performance Comparison

See:
- docs/cost-analysis.md
- docs/performance-comparison.md

---

## 🔍 Future Improvements

- Step Functions orchestration
- Data quality checks (Great Expectations)
- Iceberg tables
- Streaming ingestion

---

## 🧠 Key Learnings

- Trade-offs between serverless and custom ETL
- Data modeling for analytics
- Cost optimization in AWS
- Designing scalable pipelines

---

## 👨‍💻 Author

Roger Macedo  
Data Engineer
