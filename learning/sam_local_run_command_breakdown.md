# SAM Local Run Command Breakdown

This note explains the local raw-ingestion run in more detail, line by line.

The main source of confusion is usually this:

- `infra/` looks like "deployment only"
- so it feels like local testing should be `uv run ...`

For a normal Python script, that would often be true.

For this repo, it is not the best mental model anymore.

## The Local Command

This is the local SAM workflow:

```bash
colima start
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
export AWS_DEFAULT_REGION=us-east-1
sam validate --template-file infra/cloudformation/raw_ingestion_template.yaml
sam build --template-file infra/cloudformation/raw_ingestion_template.yaml
sam local invoke RawIngestionFunction \
  --template-file infra/cloudformation/raw_ingestion_template.yaml \
  --env-vars infra/parameters/sam-local-env.json \
  --event infra/events/html-dataset-page.json
```

Now the important part: what each line means.

## `colima start`

This starts the local virtual machine that provides the Docker runtime on your machine.

Why it matters:

`sam local invoke` does not run your Lambda directly in your shell. It runs your Lambda inside a Docker container that mimics the AWS Lambda runtime.

So if Colima is not running, SAM has nowhere to create that container.

## `export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"`

This tells tools where the Docker daemon socket lives.

Why it matters:

- Docker CLI itself may understand Colima context automatically
- AWS SAM CLI may still fail to find the socket unless you point it explicitly

So this line is not about the Lambda. It is about tool-to-tool connectivity.

## `export AWS_DEFAULT_REGION=us-east-1`

This sets a default AWS region in your shell.

Why it matters:

Even some local SAM commands still expect AWS-style context such as region resolution. In this repo, `sam validate` needed a region in the environment to run cleanly.

General concept:

SAM is a local-and-cloud tool, not a pure local runner. So some commands still care about AWS configuration defaults even when you are not deploying.

## `sam validate --template-file infra/cloudformation/raw_ingestion_template.yaml`

This checks whether the SAM template is valid.

What it means in this repo:

- the template syntax is acceptable
- the SAM transform can understand the file
- the resource definitions are structurally valid enough to continue

Why this is local-test relevant:

The local run depends on the same template as the cloud deploy. If the template is broken, the local Lambda simulation is already using a broken infrastructure definition.

This is the main reason `infra/` is not "deployment only."

## `sam build --template-file infra/cloudformation/raw_ingestion_template.yaml`

This builds the Lambda package from the template.

What it does:

- reads the function definition from the template
- resolves `CodeUri`
- copies the source into `.aws-sam/build`
- creates a built template for later steps

Why this matters:

SAM local invoke should test the Lambda the way SAM understands and packages it, not just the raw Python files in your editor.

This is the difference between:

- `uv run some_script.py`
- `sam build` + `sam local invoke`

The first runs plain Python in your local environment.
The second runs a Lambda-shaped package in a Lambda-like container.

## `sam local invoke RawIngestionFunction ...`

This is the real local execution step.

### `RawIngestionFunction`

This is the logical resource name from the SAM template:

```yaml
RawIngestionFunction:
  Type: AWS::Serverless::Function
```

SAM uses that name to know which function definition to run.

### `--template-file infra/cloudformation/raw_ingestion_template.yaml`

This tells SAM which infrastructure definition to use.

Why that matters locally:

The template defines:

- the handler path
- the runtime
- the environment variable names
- the function identity

So yes, the file in `infra/` is part of local testing too.

It is not only for deploy.

### `--env-vars infra/parameters/sam-local-env.json`

This file injects local-only environment variables.

In this repo, the key local differences are:

- `STORAGE_BACKEND=filesystem`
- `LOCAL_OUTPUT_DIR=/tmp/sam-local-output`

That means the same Lambda code runs, but with a local persistence target instead of real S3.

### `--event infra/events/html-dataset-page.json`

This is the actual payload passed into the Lambda handler.

In other words:

- the template tells SAM how to run the function
- the env file tells SAM what environment variables to inject
- the event file tells SAM what input data to pass to the function

These are three different concerns.

## Why Not Just `uv run handler.py`?

This is the most important conceptual clarification.

If you did something like:

```bash
uv run python -c "from app.lambda_app.handler import lambda_handler; ..."
```

you would only be testing Python code execution in your local shell.

You would not be testing:

- Lambda-style container runtime
- the SAM function definition
- the configured handler path from the template
- Docker-based local simulation
- local env file injection via SAM

General concept:

`uv run` is “run Python locally.”
`sam local invoke` is “run the Lambda as a Lambda-like unit locally.”

For this repo, the second one is more faithful to what will happen in AWS.

That is why `run_local.py` was removed. It was a valid debugging helper earlier, but it is no longer the official execution model.

## Example: how the event reaches your code

SAM reads [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json), then passes it as the `event` argument into:

```python
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
```

inside [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py).

So the event file is not magic. It is literally the JSON payload that becomes the `event` variable in the handler.

## What The `infra/` Template Contributes To Local Run

For local run, the template contributes these critical facts:

- handler: `app.lambda_app.handler.lambda_handler`
- runtime: `python3.14`
- memory size
- timeout
- environment variable names and defaults

If the template said the handler was different, SAM local invoke would run something else.

That is why the template is part of local runtime truth, not only deployment truth.

## What The Local SAM Run Proves Better Than `uv run`

It proves:

- your Lambda entrypoint is wired correctly
- SAM understands your function definition
- Docker can run the Lambda runtime
- the event shape works through the same interface AWS Lambda uses

It does not prove:

- the AWS stack deploys successfully
- S3 permissions work in the cloud
- IAM is correct in a real account

## Read Next

- [`how_aws_sam_works.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/how_aws_sam_works.md)
- [`infra/cloudformation/raw_ingestion_template.yaml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/cloudformation/raw_ingestion_template.yaml)
- [`infra/parameters/sam-local-env.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/parameters/sam-local-env.json)
- [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json)
