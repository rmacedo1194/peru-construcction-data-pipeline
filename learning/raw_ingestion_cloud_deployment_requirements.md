# Raw Ingestion Cloud Deployment Requirements

This note explains the deployment side as if I were acting as the architect and the DevOps owner for this phase.

The question here is not only "how do I run `sam deploy`?" The more important question is "what do I need in place so this Lambda can operate correctly in a real AWS account?"

## What The First Cloud Deployment Is Supposed To Achieve

Repo fact: the current infrastructure slice is intentionally small.

The first deploy is only meant to establish:

- one raw-ingestion Lambda
- one raw S3 bucket
- one minimum-permission IAM setup for the function
- one manual smoke-test path

General concept: a first cloud deployment should prove the narrowest valuable slice. In this project, the narrowest valuable slice is "trusted input goes into Lambda, Lambda writes raw payload plus manifest into S3."

Anything beyond that would add complexity before the ingestion contract is fully validated.

## What You Need Before Running `sam deploy`

### 1. AWS account access

You need:

- an AWS account or a sandbox account you are allowed to use
- a target AWS Region
- credentials configured locally, usually through AWS CLI profiles

General concept: SAM deploy is a cloud operation. It does not work from Docker alone. It needs real AWS credentials because it talks to CloudFormation, S3, IAM, and Lambda APIs.

### 2. Sufficient IAM permissions for the deployer

The human or CI identity running `sam deploy` needs permission to create and update:

- CloudFormation stacks
- S3 buckets or stack-managed S3 resources
- Lambda functions
- IAM roles or IAM policy attachments used by the function
- CloudWatch Logs related resources as needed by the Lambda execution role

In plain language: the deployer needs permission to create the infrastructure, not just permission to invoke the function.

### 3. A deployment region choice

You should decide one explicit region for the first environment, for example `us-east-1` or another team-approved region.

Why this matters:

- CloudFormation stacks are regional
- Lambda is regional
- S3 bucket naming is global, but bucket usage and Lambda integration still depend on the chosen region strategy

Architecturally, one dev region is enough for this phase.

### 4. A naming and environment strategy

Repo fact: [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml) currently defaults to the stack name `peru-construction-raw-ingestion-dev`.

That is a good first move because it makes the environment intention explicit: this is a dev stack, not a production stack.

What you still need to think about soon:

- will there be separate `dev`, `staging`, and `prod` stacks?
- will all environments live in one account or multiple accounts?
- who is allowed to deploy to each one?

For now, one `dev` stack is enough.

## What The Template Already Covers

Repo fact: the template already creates:

- an encrypted S3 bucket
- public access blocks on that bucket
- a Lambda function
- CloudWatch Logs basic execution permission
- `s3:PutObject` permission to the bucket path
- outputs for the function and bucket names

Why these choices were made:

- encryption is a sensible default, even for dev
- block public access avoids accidental exposure
- least-privilege IAM keeps the first slice narrow
- outputs make smoke tests scriptable

General concept: the first cloud deploy should include security defaults early, not as a future cleanup task.

## What Is Still Missing Before Calling This Production-Ready

This first slice is deployable, but it is not production-complete.

From an architect/DevOps perspective, the likely next needs are:

- explicit log retention instead of default indefinite logs
- a stronger bucket policy story if organizational standards require it
- a deployment parameter strategy per environment
- alarms or at least a basic error monitoring path
- CI-based deployment instead of only laptop-based deployment
- secrets handling if future sources require credentials
- idempotency safeguards if the same ingestion event can be replayed frequently

These are not blockers for the first dev deploy. They are the next maturity layer.

## How The Deployment Flow Works

The cloud deployment path is:

1. `sam build`
2. `sam deploy`
3. SAM packages artifacts
4. SAM hands the deployment to CloudFormation
5. CloudFormation creates or updates the stack
6. Lambda becomes invokable with the configured environment

This is the mental model you want:

- SAM is your developer workflow layer
- CloudFormation is your infrastructure execution layer
- Lambda and S3 are the deployed runtime resources

That separation matters because troubleshooting also follows it:

- build issue: source or packaging problem
- deploy issue: CloudFormation, IAM, or account configuration problem
- runtime issue: Lambda code, source behavior, or permissions problem

## What You Need To Smoke Test In AWS

Once deployed, the minimum cloud test should confirm:

- the stack finishes successfully
- the Lambda can be invoked manually
- the function logs appear in CloudWatch
- the raw payload is written to the bucket
- the manifest is written beside it
- the bucket path matches the deterministic naming strategy

That is enough to say the first serverless ingestion slice is alive in the cloud.

## My Architect Recommendation For The Next Step

If I were defining the next operational step for this project, I would do this:

1. Keep the first deploy manual and limited to `dev`
2. Run one known-good smoke test event after each deploy
3. Inspect CloudWatch logs and S3 objects manually at least once
4. Only after that, decide whether to add automation such as schedules or CI/CD

Why:

- this phase is still validating contracts and boundaries
- early automation on unstable contracts creates confusion faster than value
- one clean manual deploy teaches the system much better than premature pipeline work

## Practical Checklist Before You Deploy

- AWS CLI installed and authenticated
- correct AWS profile selected
- correct AWS region selected
- permission to create CloudFormation, Lambda, S3, and IAM resources
- confidence that Python 3.14 is allowed in the target Lambda region/runtime policy
- willingness to approve IAM role creation in the stack
- sample event ready for post-deploy invoke

## Read Next

- [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)
- [AWS SAM: Introduction to deploying with AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-deploy.html)
- [AWS SAM: Options for deploying your application](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/deploying-options.html)
