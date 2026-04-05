# SAM Local Run Decisions

This note explains every important decision behind the local AWS SAM workflow for this repo.

The goal is not only to show the commands. The goal is to explain why the local run was designed this way, what it proves, and what it does not prove yet.

## What We Are Simulating

Repo fact: the ingestion entrypoint is [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py).

Repo fact: the local SAM flow uses:

- [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml)
- [`infra/parameters/sam-local-env.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/parameters/sam-local-env.json)
- [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json)
- [`samconfig.toml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/samconfig.toml)

General concept: `sam local invoke` runs your Lambda inside a Docker container that mimics the Lambda runtime. It does not create AWS resources. It only simulates the Lambda execution environment closely enough to test packaging, environment variables, event input, and runtime behavior.

So the local SAM run is meant to answer these questions:

- Does the Lambda package build correctly?
- Can the handler run in a Lambda-like container?
- Does the event contract work the same way as it will in AWS?
- Does the code fetch the trusted source and produce the expected raw payload and manifest?

It is not meant to prove that AWS IAM, S3, or CloudFormation are correct yet. That comes later when the stack is deployed.

## Why We Added A Storage Backend Switch

Repo fact: the config now includes `STORAGE_BACKEND` and `LOCAL_OUTPUT_DIR` in [`app/lambda_app/config.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/config.py).

Repo fact: the storage layer now exposes a backend abstraction in [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py).

Why this exists:

- in AWS, the Lambda should write to S3
- before the stack exists, there is no stack-managed bucket to write to
- we still wanted the local SAM run to complete end-to-end

General concept: this is a classic dependency-boundary decision. The ingestion logic should not care whether persistence goes to real infrastructure or to a local test target. That is why the handler now asks for a storage writer instead of calling S3 directly.

Tradeoff:

- this adds one abstraction layer
- but it keeps the ingestion path stable across local simulation and AWS deployment

Without this abstraction, we would have had two weaker options:

- skip persistence during local testing
- manually create temporary AWS resources before the first real deploy

Both are worse for learning and worse for repeatability.

## Why The Local Backend Writes To Filesystem

Repo fact: local SAM uses `STORAGE_BACKEND=filesystem` in [`infra/parameters/sam-local-env.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/parameters/sam-local-env.json).

Why this exists:

- it lets the function complete the same flow as production
- it preserves the same deterministic key layout used by S3
- it avoids introducing LocalStack or extra moving parts too early

General concept: when testing a first MVP, the most useful local substitute is usually the simplest one that preserves the important contract. Here, the important contract is not "must be S3 right now." The important contract is "must persist the payload and manifest using the same naming logic."

That is why filesystem mirroring is enough for this stage.

## Why We Used `/tmp` Instead Of A Repo Folder

Repo fact: the local env file points `LOCAL_OUTPUT_DIR` to `/tmp/sam-local-output`.

This was not arbitrary. It came from a real runtime constraint we hit.

When SAM runs a Lambda locally, it mounts the project source into the container as read-only. The code directory becomes visible inside the container, but you cannot safely write new files into it. In our case, trying to write to `.sam-local-output` failed because that path lived under the mounted source tree.

General concept: real Lambda functions also have a writable filesystem boundary. In Lambda, the writable temporary directory is `/tmp`. Everything else should be treated as packaged code or managed infrastructure.

So using `/tmp` is actually more Lambda-like than writing beside the source code.

This is a good example of a design decision driven by runtime truth instead of personal preference.

## Why We Exported `DOCKER_HOST` For Colima

Repo fact: the local README flow tells you to export:

```bash
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
```

Why this exists:

- Docker CLI understood the active `colima` context
- AWS SAM CLI still failed to detect a usable container runtime
- explicitly pointing SAM at Colima's Docker socket removed that ambiguity

General concept: tools do not always discover Docker the same way. One tool may respect Docker contexts, while another may look for a default socket or runtime endpoint. When that happens, setting `DOCKER_HOST` is a practical compatibility fix.

Tradeoff:

- this adds one shell setup step
- but it makes the local workflow much more deterministic on macOS with Colima

## Why We Kept A Sample Event File

Repo fact: [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json) is the canonical local test event.

Why this exists:

- it freezes one trusted-input example
- it makes local invocation repeatable
- it teaches the real Lambda contract better than a generated fake event

General concept: for internal functions that consume custom payloads, a checked-in sample event is part of the interface. It is both a test asset and living documentation.

In this repo, the sample event uses an HTML dataset page on purpose. That matches the source reality discovered in [`exploring/datos.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/exploring/datos.py), where the portal behaves like a browser-facing HTML site, not a clean JSON catalogue API.

## Why We Still Run `sam validate` And `sam build`

Repo fact: the documented local sequence is:

1. `sam validate`
2. `sam build`
3. `sam local invoke`

Why this order exists:

- `sam validate` checks that the SAM template is structurally correct
- `sam build` prepares the build artifacts in `.aws-sam/`
- `sam local invoke` runs the function using that packaging model

General concept: this is the same discipline you want in CI and deployment. Validate the infrastructure definition, build the app artifact, then run it. Skipping directly to local invoke makes failures harder to interpret because you don't know whether the problem is in the template, the build, or the function itself.

AWS documentation says `sam build` prepares the application for local testing and deployment by creating build artifacts in `.aws-sam`, and `sam local invoke` runs the function locally in a containerized Lambda-like environment. In this repo, that maps directly to our build and invoke workflow.

## What The Local Run Proves

After the current changes, the SAM local run proves:

- the SAM template points at the right function code
- the Lambda package can be built
- the Lambda runtime starts under Python 3.14
- the event contract is usable in a Lambda-like execution environment
- the download logic works with the trusted sample URL
- the payload and manifest naming logic are stable

## What The Local Run Does Not Prove

It does not yet prove:

- CloudFormation stack creation in AWS
- IAM policy correctness in a real account
- S3 writes against the real bucket
- region, account, and credentials correctness
- post-deploy operational behavior such as CloudWatch troubleshooting

That is why local SAM is a simulation stage, not the final acceptance stage.

## Read Next

- [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`infra/parameters/sam-local-env.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/parameters/sam-local-env.json)
- [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json)
- [AWS SAM: Introduction to testing with sam local invoke](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-invoke.html)
