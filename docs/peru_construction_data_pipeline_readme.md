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

