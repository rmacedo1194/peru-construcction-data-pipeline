# Task Backlog

## Verified Complete
- [x] Define the Lambda ingestion contract
- [x] Define the event schema for ingestion requests
- [x] Design the handler-to-service flow
- [x] Build the HTTP download service
- [x] Define raw S3 key naming strategy
- [x] Build the raw file writer
- [x] Build the metadata manifest writer
- [x] Add local runner support with AWS SAM and sample events
- [x] Add basic unit tests for core ingestion components
- [x] Add initial CloudFormation/SAM infrastructure for the raw-ingestion Lambda

## Current Priority
- [x] Make `pytest` runnable without manually setting `PYTHONPATH=.`
- [ ] Add Python project metadata and dependency declarations for local development and CI
- [ ] Add a GitHub Actions CI workflow that runs tests plus `sam validate` and `sam build`
- [x] Add a GitHub Actions CD workflow for `dev` deployments using `sam deploy`
- [ ] Define GitHub-to-AWS authentication with a dedicated deploy role and GitHub OIDC
- [x] Define environment configuration strategy for `dev` stack names, region, tags, and SAM parameters
- [ ] Re-deploy the raw-ingestion stack to target the shared `bronze-rmm` bucket instead of the stack-managed raw bucket
- [ ] Clean up the old stack-managed raw bucket after confirming data lands in `bronze-rmm`
- [ ] Add post-deploy smoke validation for Lambda invoke plus raw object and manifest checks
- [ ] Document the AWS account bootstrap for the first `dev` environment

## Next
- [ ] Tighten the Lambda execution role to least privilege for the raw bucket and logs
- [ ] Add retry and backoff strategy for upstream downloads
- [ ] Add idempotency checks for repeated ingestion events
- [ ] Use the recorded checksum for duplicate detection or validation workflows
- [ ] Add basic observability hooks such as log retention, metrics, and alarms
- [ ] Freeze a reusable deployment standard that can be applied to Lambda, Glue, and EC2 workloads
- [ ] Draft the deployment skill backlog item: inputs, required checks, environment assumptions, and failure handling

## Later
- [ ] Build the deployment skill after the workflow and IAM model are stable
- [ ] Extend the shared deployment workflow to Glue jobs
- [ ] Extend the shared deployment workflow to EC2-managed workloads
- [ ] Add support for multiple resources in one run
- [ ] Define a repeatable create-run-destroy workflow for short-lived learning environments
- [ ] Create Athena tables
- [ ] Build cost and performance comparison artifacts

## Deferred
- [ ] Full dynamic portal exploration inside runtime ingestion
- [ ] Parallel subagent orchestration
- [ ] Automated reverse-engineering workflow
