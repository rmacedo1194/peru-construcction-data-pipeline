# GitHub Actions Dev Deploy Workflow

This note explains the first deployment workflow added to this repo:

- [`deploy-dev.yml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/.github/workflows/deploy-dev.yml)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)

The goal is to make the deploy path easy to inspect, easy to change, and safe enough for a learning project.

## Why This Workflow Exists

Repo fact: the Lambda code and SAM template already existed, but the repository did not yet have a GitHub Actions workflow that could deploy the stack through your AWS deploy role.

General concept: a deployment workflow is not just "run `sam deploy` somewhere else." It is a repeatable contract between:

- GitHub as the orchestrator
- AWS IAM as the trust boundary
- SAM as the packaging and deployment tool
- CloudFormation as the actual infrastructure engine

That separation matters because each layer can fail for a different reason.

## Why The Trigger Is Manual

The workflow uses only `workflow_dispatch`.

Repo fact: this project is a learning project with short-lived environments that you plan to create, test, and destroy.

General concept: automatic deploys on every push are useful when a system is stable and meant to stay online. They are less useful when:

- the infrastructure is still being learned
- the cost should stay predictable
- you want to decide intentionally when AWS resources get created

That is why the workflow starts manual-first.

## How The Workflow Is Structured

The job runs these stages in order:

1. Check out the repository
2. Install Python
3. Install the AWS SAM CLI
4. Install `pytest`
5. Run unit tests
6. Validate the SAM template
7. Build the SAM application
8. Assume the AWS deploy role through GitHub OIDC
9. Run `sam deploy --config-env dev`

Why this order:

- tests fail fast before cloud work starts
- template validation catches infrastructure definition mistakes
- build checks that the SAM package can actually be assembled
- AWS credentials are only requested after local validation succeeds

That last point is a useful backend habit: delay privileged actions until cheaper checks pass first.

## The Most Important Security Decision

This line is the security center of the workflow:

`role-to-assume: arn:aws:iam::380592535850:role/github-actions-deploy-role`

Repo fact: the workflow does not store static AWS access keys in GitHub.

General concept: with OIDC, GitHub proves its identity to AWS at runtime and temporarily receives credentials for the specific role. That is better than long-lived keys because:

- there is no permanent AWS secret sitting in GitHub repository settings
- the credentials expire automatically
- the IAM trust policy can restrict which repository and branch or workflow may assume the role

So the trust model becomes "GitHub may assume this role under specific rules" instead of "GitHub permanently knows an AWS password-like secret."

## Why `samconfig.toml` Was Updated

The workflow deploys with:

`sam deploy --config-env dev`

That only works cleanly if the repo defines a named `dev` SAM config section.

Repo fact: [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml) now has:

- `default.global.parameters.region = "us-east-2"`
- `dev.global.parameters.region = "us-east-2"`
- `dev.deploy.parameters` for the `peru-construction-raw-ingestion-dev` stack

General concept: this is configuration separation. Instead of hardcoding every deployment choice directly inside the workflow file, the workflow calls a named environment and SAM reads the environment-specific values from `samconfig.toml`.

That design helps later because:

- the workflow stays short
- deploy parameters stay versioned in the repo
- a future `staging` or `prod` config could be added without rewriting the whole pipeline

Even though this project is not targeting long-lived production right now, using named config environments is still a good habit.

## Why The Workflow Still Runs Tests Locally Inside CI

You might ask: if this is a deployment workflow, why not skip tests and just deploy?

Because deployment failures are more expensive than test failures.

Repo fact: the workflow runs:

- `pytest -q`
- `sam validate --template-file infra/cloudformation/raw_ingestion_template.yaml`
- `sam build --template-file infra/cloudformation/raw_ingestion_template.yaml`

General concept: CI/CD should reject obviously broken states before they reach AWS. In backend work, this is one of the most important process boundaries:

- local/test validation proves the artifact is plausible
- deployment proves AWS can accept and create the infrastructure
- smoke testing proves the runtime behavior works after deployment

Those are three different checks, not one.

## How To Manipulate This Workflow Safely

If you want to experiment, these are good controlled changes:

### 1. Change the trigger

You can add:

- `push` to a branch
- path filters
- environment protection later

Start manual. Add automatic triggers only when you understand the cost and failure behavior.

### 2. Change the role session name

This is useful for CloudTrail readability. It does not change permissions.

### 3. Add a smoke-test step after deploy

That would be the next maturity step. For example:

- invoke the deployed Lambda
- inspect the response
- optionally confirm the bucket output path

This is a better next experiment than adding more infrastructure complexity.

### 4. Split CI from CD

Right now the workflow includes test and deploy in one file because the repo is still small.

Later, a cleaner shape is:

- one `ci.yml` for tests, validation, and build
- one `deploy-dev.yml` for deployment only

That split becomes more useful once multiple services or environments exist.

## Common Failure Modes To Expect

If this workflow fails, the likely category is usually one of these:

1. GitHub cannot assume the role
Cause: the AWS IAM trust policy for GitHub OIDC is wrong or incomplete.

2. SAM deploy starts but CloudFormation fails
Cause: the deploy role is missing permissions for IAM, S3, Lambda, or CloudFormation operations.

3. Build works but runtime later fails
Cause: Lambda code or environment behavior is wrong even though packaging succeeded.

This is the core backend lesson: build success, deploy success, and runtime success are not the same thing.

## Read Next

- [`deploy-dev.yml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/.github/workflows/deploy-dev.yml)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)
- [`learning/raw_ingestion_cloud_deployment_requirements.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/raw_ingestion_cloud_deployment_requirements.md)
- [`learning/how_aws_sam_works.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/how_aws_sam_works.md)
