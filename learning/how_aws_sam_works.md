# How AWS SAM Works In This Project

This note explains AWS SAM itself, then connects that explanation to how this repo uses it.

## What AWS SAM Is

General concept: AWS SAM stands for AWS Serverless Application Model.

It has two connected parts:

- a template format for defining serverless infrastructure
- a CLI for building, testing, and deploying that infrastructure

That means SAM is not just "a local runner." It is both:

1. a shorthand way to define Lambda-related infrastructure
2. a workflow tool that turns that definition into build, local test, and deployment actions

AWS documentation describes the `AWS::Serverless` transform as a CloudFormation transform that converts SAM syntax into standard CloudFormation. That is the key idea behind the whole toolchain.

## How SAM Is Represented In This Repo

Repo fact: the SAM template is [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml).

Repo fact: the first important line is:

```yaml
Transform: AWS::Serverless-2016-10-31
```

Why this exists:

- it tells AWS and the SAM CLI that this file uses SAM syntax
- it allows us to use `AWS::Serverless::Function` instead of writing the full lower-level Lambda resource wiring by hand

General concept: SAM is an authoring convenience on top of CloudFormation, not a separate infrastructure engine. CloudFormation is still the thing that actually creates resources in AWS.

## What `sam build` Does

Repo fact: the project has a SAM config file at [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml).

Repo fact: when we ran `sam build`, SAM created artifacts under `.aws-sam/build`.

General concept: `sam build` prepares your function code and template for the next steps. According to AWS docs, it creates a `.aws-sam` directory with build artifacts that `sam local` and `sam deploy` then use.

In this repo, that means:

- it reads the template
- it resolves `CodeUri: ../../`
- it copies the Lambda source into the build output
- it prepares a built template under `.aws-sam/build/template.yaml`

Why this matters:

- local invoke should test what you are actually going to package
- deploy should ship the built artifact, not some vague state of your working directory

General concept: build is the contract point between source code and runtime artifact.

## What `sam local invoke` Does

Repo fact: the local invoke command points at:

- the template
- the function logical ID `RawIngestionFunction`
- the local env file
- the sample event file

General concept: `sam local invoke` starts a Docker container that mimics the Lambda runtime, injects the configured environment variables, passes in the event payload, and runs the function handler.

In this repo, that maps to:

- template chooses the function
- env file changes the backend to `filesystem`
- event file supplies a trusted input
- Docker provides the Lambda-like runtime boundary

This is why Colima and Docker matter for local SAM. Without a container runtime, SAM cannot simulate Lambda execution.

## How Local SAM Connects To Cloud Deployment

This is the part many people miss.

Local SAM and cloud SAM are not two separate architectures. They are two stages of the same workflow:

1. author template and function code
2. `sam build`
3. `sam local invoke` for local runtime simulation
4. `sam deploy` to create real AWS resources

General concept: SAM reuses the same template definition for both local and cloud workflows. That is the main value of the tool. You do not define your Lambda one way locally and a different way for the cloud. You define it once, then exercise it in multiple environments.

In this repo, the connection is very direct:

- same function definition
- same handler
- same environment variable structure
- same event contract
- different persistence backend depending on environment

That last line is important. The infrastructure shape stays the same, but the local simulation swaps one dependency so the Lambda can complete before the real AWS bucket exists.

## What `sam deploy` Does

General concept: `sam deploy` takes the built application and deploys it to AWS using CloudFormation.

AWS docs say SAM uses CloudFormation for deployment. That means:

- SAM packages the artifacts
- SAM uploads them as needed
- SAM asks CloudFormation to create or update the stack
- CloudFormation creates the resources in dependency order

In this repo, `sam deploy` would create:

- one S3 bucket
- one Lambda function
- one IAM execution role policy set
- stack outputs for the function and bucket names

So the cloud path is not "SAM directly creates Lambda." The more accurate statement is:

SAM prepares and submits a CloudFormation deployment that creates Lambda and the related resources.

## Why We Used SAM Instead Of Raw CloudFormation Only

This is an architect/devops tradeoff decision.

Why SAM is a good fit here:

- the first deployable slice is mostly serverless
- Lambda is the primary runtime in this phase
- the template stays shorter and easier to read
- local invoke support comes from the same toolchain

What raw CloudFormation alone would make harder:

- authoring serverless resources by hand
- local Lambda testing
- keeping local build and cloud deployment under one workflow

Tradeoff:

- SAM is great for serverless-focused stacks
- if this repo later grows into a broader AWS platform with many non-serverless components, you may eventually mix SAM with regular CloudFormation or move to another IaC layer for consistency

For this first Lambda ingestion slice, SAM is the right level of abstraction.

## Why The Template Has Parameters

Repo fact: the template has parameters for `SourceName`, `RawPrefix`, `RequestTimeout`, `StorageBackend`, and `LocalOutputDir`.

General concept: template parameters let you keep one infrastructure definition while varying environment-specific values.

In this repo, that matters because:

- cloud deploy should use `s3`
- local invoke should use `filesystem`
- timeout and prefixes may evolve without rewriting the template

This is not just convenience. It is a separation-of-concerns decision: infrastructure shape lives in the template, environment-specific values can change per run or per environment.

## What Would Break If SAM Were Removed

If you removed SAM from this repo right now:

- local Docker-based Lambda simulation would disappear
- the current serverless template would need to be rewritten in plain CloudFormation
- the build and deploy workflow would become more manual
- the first cloud deployment path would lose its current consistency

That does not mean SAM is mandatory forever. It means it currently provides the cleanest bridge between local Lambda simulation and first AWS deployment.

## Read Next

- [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)
- [AWS::Serverless transform](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html)
- [AWS SAM: How AWS SAM works](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam-overview.html)
