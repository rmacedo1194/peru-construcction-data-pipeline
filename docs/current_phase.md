# Current Phase

## Phase
Lambda ingestion MVP

## Goal
Implement a Lambda-ready ingestion workflow that downloads approved dataset resources and stores raw files plus metadata in S3.

## Why This Phase Exists
The source discovery phase is complete, but the public portal is not reliable for broad automated exploration on every run.
The ingestion layer should therefore work from trusted inputs such as approved dataset URLs or pre-resolved resource metadata.

## In Scope
- Lambda handler
- Input contract for ingestion requests
- Configuration loading
- Download service
- Raw file persistence to S3
- Metadata manifest generation
- Logging and error handling
- Local execution support

## Out of Scope
- Full portal crawling inside Lambda
- Glue ETL implementation
- EC2 ETL implementation
- Athena modeling
- Production-grade CI/CD hardening
- Global source discovery logic

## Known Inputs
- Source discovery has already been completed
- Trusted resource URLs or resolved dataset metadata will be used as ingestion inputs
- The source may return HTML for exploration, but ingestion should target direct resources when possible

## Acceptance Criteria
- Lambda entrypoint works with a defined event structure
- Local execution works with a sample event
- Raw file is stored in S3 using a deterministic key structure
- A metadata manifest is generated for each ingestion
- Errors are observable through structured logs

## Exit Condition
This phase is complete when a single trusted dataset resource can be ingested end-to-end through the Lambda-ready workflow.