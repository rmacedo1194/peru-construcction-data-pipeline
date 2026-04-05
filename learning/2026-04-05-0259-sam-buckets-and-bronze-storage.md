# What was built

I changed the raw-ingestion SAM template so the stack no longer creates its own raw bucket.

Instead, the stack now:

- writes ingestion output to the existing shared bucket name `bronze-rmm`
- keeps that bucket name as a deployment parameter in [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)
- packages only the `app/` directory into the Lambda artifact
- leaves the AWS SAM managed artifact bucket as a separate deployment concern

I also updated the backlog and deployment docs to reflect that architecture.

# Why it was built this way

Repo fact: the previous template created a stack-specific bucket through the `RawBucket` resource in [`raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml).

General concept: there are two very different kinds of S3 buckets involved in a SAM deployment:

1. runtime bucket
This is where the Lambda writes business data, in this project the raw ingestion payloads and manifests.

2. artifact bucket
This is where SAM uploads deployment packages before CloudFormation updates the stack.

Decision rationale: if you want a shared bronze layer reused by Lambda, Glue, and other services, the runtime bucket should not be owned by one service stack. It should be treated as shared infrastructure.

That is why `bronze-rmm` is the better target for ingestion data, while the `aws-sam-cli-managed-default-samclisourcebucket-...` bucket remains normal and expected for deployment packaging.

# Key decisions and tradeoffs

## Decision 1: stop creating the raw bucket inside this stack

Why:

- a Lambda stack should not own a shared bronze layer if multiple services will write to it
- deleting or replacing the stack should not implicitly control the lifecycle of shared storage
- the bucket name should be stable and intentional, not auto-generated from a stack logical ID

Tradeoff:

- the stack now assumes `bronze-rmm` already exists
- bucket provisioning must happen somewhere else, either manually for now or in a shared-storage stack later

## Decision 2: keep `resolve_s3 = true`

Why:

- SAM still needs a place to upload the zipped deployment artifact before CloudFormation deploys
- that artifact bucket is operational infrastructure, not data-lake storage

Tradeoff:

- you will continue to see a bucket like `aws-sam-cli-managed-default-samclisourcebucket-...`
- that bucket can be surprising until you separate "deployment artifacts" from "runtime data"

## Decision 3: put `RawBucketName=bronze-rmm` in `samconfig.toml`

Why:

- the desired bucket becomes versioned repo configuration
- GitHub Actions and local deploys use the same setting

Tradeoff:

- if you later want multiple environments, this parameter will need environment-specific values

# Code walkthrough

## 1. The runtime bucket name now comes from a parameter

In [`raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml), the new `RawBucketName` parameter defaults to `bronze-rmm`.

That means CloudFormation no longer invents a bucket name for the runtime storage path.

## 2. The Lambda receives that name through environment variables

The function environment still sets `RAW_BUCKET_NAME`, but now it uses `!Ref RawBucketName` instead of `!Ref RawBucket`.

Repo fact: in [`config.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/config.py), `Settings.from_env()` reads `RAW_BUCKET_NAME`.

General concept: the application code does not need to know whether the bucket was created by CloudFormation, manually, or by another stack. It just needs a bucket name at runtime.

That is a useful backend boundary:

- infrastructure decides resource identity
- application code consumes configuration

## 3. The IAM policy now points at the shared bucket ARN

The function policy now grants `s3:PutObject` on:

`arn:${AWS::Partition}:s3:::${RawBucketName}/*`

That means the Lambda can write into `bronze-rmm` even though this template no longer creates that bucket.

## 4. `samconfig.toml` now locks the deploy parameter

[`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml) now includes:

`parameter_overrides = "RawBucketName=bronze-rmm"`

That is what makes local deploy commands and GitHub Actions use the same bucket target.

## 5. Why your deployment seemed to include docs, learning, and infra

Repo fact: the older template used `CodeUri: ../../`, which points at the repository root from inside the `infra/cloudformation/` folder.

General concept: `CodeUri` decides what files SAM packages into the Lambda artifact zip. That does not mean every packaged file becomes an AWS resource, but it does mean those files are uploaded as part of the function bundle.

Decision rationale: a Lambda artifact should contain only runtime code and the files it actually needs. Packaging docs, exploration scripts, infra notes, and learning files increases artifact size and blurs the deployment boundary.

That is why the template now uses:

- `CodeUri: ../../app`
- `Handler: lambda_app.handler.lambda_handler`

## 6. Why the two buckets you saw are both real but serve different purposes

Bucket 1:

`aws-sam-cli-managed-default-samclisourcebucket-1tjoffxw0byv`

Meaning:

- created by AWS SAM because `resolve_s3 = true`
- used to upload deployment artifacts such as the packaged template and Lambda bundle
- not your ingestion output bucket

Bucket 2:

`peru-construction-raw-ingestion-dev-rawbucket-8h1dr6bnocac`

Meaning:

- created by the old version of your CloudFormation stack
- intended to be the runtime raw storage bucket for ingestion data
- this is the bucket you no longer want the stack to own

# How to change this safely later

1. If `bronze-rmm` does not exist yet, create it first before redeploying this stack.

2. Re-deploy the stack after this template change.
CloudFormation should update the Lambda configuration and IAM policy so the function writes to `bronze-rmm`.

3. Run one smoke test invocation and confirm:

- Lambda succeeds
- objects land in `s3://bronze-rmm/...`
- the manifest and payload keys match the expected deterministic path

4. Only after that, clean up the old bucket created by the earlier stack version.

5. If later you want fully managed shared infra, create a separate storage stack for bronze/silver/gold buckets instead of putting them into individual service stacks.

# Terms or patterns to learn next

- CloudFormation parameter
- shared infrastructure vs service-owned infrastructure
- runtime configuration through environment variables
- least-privilege IAM policy
- deployment artifact bucket vs business-data bucket

# Read next

- [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)
- [`docs/deployment_workflow.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/docs/deployment_workflow.md)
- [`learning/github_actions_deploy_dev_workflow.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/github_actions_deploy_dev_workflow.md)
