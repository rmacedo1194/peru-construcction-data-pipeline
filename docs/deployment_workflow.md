# Deployment Workflow – Raw Ingestion Lambda

## Overview

This project follows a **controlled deployment model**:

- Local development and validation first
- GitHub as the source of truth
- GitHub Actions as the deployment orchestrator
- AWS SAM + CloudFormation as the deployment engine
- AWS as the runtime environment

The goal is to avoid manual, ad-hoc deployments and ensure reproducibility.

---

## High-Level Flow

Local → GitHub → CI/CD → AWS → Validation

---

## Deployment Flow Diagram

```text
Local Dev
   ↓
Local Tests
   ↓
Push to GitHub
   ↓
GitHub Actions
   ↓
SAM Build
   ↓
SAM Deploy
   ↓
AWS Dev
   ↓
Smoke Test
```

---

## Step-by-Step Workflow

### 1. Local Development

- Implement Lambda logic
- Update the SAM template if needed
- Add or update tests
- Keep code and infrastructure definition versioned together

---

### 2. Local Validation

Run:

- Unit tests for business logic
- Handler tests for Lambda input/output
- Optional runtime emulation with AWS SAM

Example:

```bash
sam build
sam local invoke -e events/sample.json
```

---

### 3. Artifact Ready Criteria

An artifact is ready for deployment when:

- Tests pass
- Code is reviewed
- Event contract is validated
- Local behavior is stable enough for dev deployment

---

### 4. Push to GitHub

- The repository is the single source of truth
- A branch such as `develop` or `main` can trigger deployment
- The deployable state must always come from versioned code, not from manual local changes

---

### 5. GitHub Actions Responsibilities

The CI/CD pipeline should:

- Checkout the repository
- Install dependencies
- Run tests
- Build the application with SAM
- Deploy using SAM

Core commands:

```bash
sam build
sam deploy --config-env dev --no-confirm-changeset --no-fail-on-empty-changeset
```

---

### 6. AWS Deployment Path

Deployment flow:

```text
GitHub Actions
   ↓
AWS SAM
   ↓
CloudFormation
   ↓
Creates/updates:
- Lambda function
- IAM execution role
- CloudWatch log group

Uses:
- Shared raw/bronze S3 bucket (`bronze-rmm`)
- SAM-managed artifact bucket for deployment packaging
```

---

### 7. Post-Deploy Smoke Test

After deployment, validate:

- Stack deployed successfully
- Lambda can be invoked
- Logs appear in CloudWatch
- Raw data is written to S3
- Manifest is generated correctly
- Bucket path matches the naming strategy

---

## Environment Strategy

### Current

- `dev`

Recommended path:

- Start with one clean `dev` environment
- Use short-lived create-run-destroy cycles while learning
- Stabilize the contract before adding more environments

---

## Testing Strategy

| Level | Tool | Purpose |
|------|------|--------|
| Unit | pytest | Validate business logic |
| Handler | pytest | Validate Lambda entrypoint behavior |
| Runtime | AWS SAM local | Validate packaging and runtime behavior |
| Cloud | AWS dev | Final validation with real resources |

---

## Key Principles

- No direct manual deployments as the primary workflow
- GitHub is the source of truth
- CI/CD is the deployment gatekeeper
- Infrastructure is defined as code
- Validate locally before deploying
- Keep the first environment simple

---

## Recommended Repository Structure

```text
project-root/
├── app/
│   └── lambda/
├── infra/
│   └── cloudformation/
├── events/
├── tests/
├── .github/
│   └── workflows/
├── template.yaml
├── samconfig.toml
└── README.md
```

---

## Operational Mental Model

Use this separation of concerns:

- **Application code** = Lambda logic
- **SAM template** = deployment definition
- **CloudFormation** = infrastructure execution layer
- **GitHub Actions** = deployment orchestrator
- **AWS** = real runtime environment

---

## Future Improvements

Later, this workflow can evolve with:

- GitHub OIDC for secure AWS authentication
- Separate deploy jobs for additional environments only if the project later needs them
- Approval gates before production deploy
- CloudWatch alarms
- Log retention policies
- Rollback strategy
- Integration smoke tests after deploy

---

## Summary

The deployment model for this project is:

**develop locally → validate locally → push to GitHub → deploy through GitHub Actions → validate in AWS dev**

This keeps deployments reproducible, reviewable, and aligned with infrastructure as code practices.
