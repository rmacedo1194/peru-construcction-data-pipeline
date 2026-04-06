# What was built

This note explains how to run the deployed raw-ingestion Lambda manually and how to schedule it later.

It is grounded in this repo's current design:

- the Lambda handler expects a custom ingestion event payload
- the repo includes sample payloads under [`infra/events/`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events)
- the stack currently deploys one Lambda function, but no schedule or trigger resource is defined in the SAM template

# Why it was built this way

Repo fact: the Lambda is a generic "ingest one trusted resource" function, not a crawler and not an always-on service.

General concept: Lambda does nothing by itself. It always needs an invoker. That invoker might be:

- a human clicking `Test` in the console
- the AWS CLI calling `lambda invoke`
- EventBridge Scheduler firing on a timetable
- another AWS service such as S3, API Gateway, or Step Functions

Decision rationale: this repo keeps the ingestion contract explicit. Instead of hardcoding one source in the function code, the caller sends a JSON event telling the Lambda what to fetch and where to store it.

That makes the same function reusable for:

- manual smoke tests
- scheduled recurring runs
- future orchestrators

# Key decisions and tradeoffs

## Decision 1: use a custom event contract

Why:

- one Lambda can ingest many approved sources
- the source-specific details stay in the event payload
- testing is easier because you can save and replay known-good events

Tradeoff:

- someone has to provide that event payload
- scheduling is not just "run the function"; it is "run the function with this JSON input"

## Decision 2: no trigger is defined in the SAM template yet

Why:

- the ingestion contract is still being stabilized
- manual invocation is simpler while learning
- it avoids accidental recurring runs and surprise AWS costs

Tradeoff:

- after deployment, the function exists but nothing automatically calls it
- you must invoke it manually or add a schedule/trigger

## Decision 3: keep sample events in the repo

Why:

- they act as runnable examples
- they document the expected schema better than prose alone

Tradeoff:

- you must keep them updated if the event contract changes

# Code walkthrough

## 1. What the Lambda expects as input

The handler in [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py) receives `event` and immediately validates it through [`IngestionEvent.from_dict()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/models.py).

That means the payload must contain these important fields:

- `dataset_id`
- `resource_id`
- `ingestion_id`
- `request.kind`
- `request.url`

Optional fields still matter too:

- `source_id`
- `request.method`
- `request.headers`
- `metadata`
- `storage.bucket`
- `storage.prefix`

If `storage.bucket` is omitted, the Lambda falls back to the deployed environment variable `RAW_BUCKET_NAME`.

## 2. The repo already gives you example events

Use these as your starting point:

- [`infra/events/mml-cercado-lima-licencias.csv.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/mml-cercado-lima-licencias.csv.json)
- [`infra/events/mml-cercado-lima-conformidad.csv.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/mml-cercado-lima-conformidad.csv.json)
- [`infra/events/san-isidro-licencias-edificacion.csv.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/san-isidro-licencias-edificacion.csv.json)
- [`infra/events/html-dataset-page.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/html-dataset-page.json)

For learning and smoke testing, the CSV examples are the better target than the HTML page example.

## 3. Why the function does not "know the event" on its own

General concept: a Lambda function does not invent input data. The caller provides the event.

In this repo, the function logic is:

1. receive event JSON
2. validate it
3. fetch the URL described in the event
4. write payload + manifest to S3
5. return a success response with bucket and key information

So the event is not discovered by the function. It is supplied by whoever invokes the function.

## 4. How to run it manually in the AWS console

### Lambda console test

1. Open AWS Console.
2. Go to Lambda.
3. Open your function.
4. Go to the `Test` tab.
5. Create a new test event.
6. Paste one of the repo event payloads.
7. Change `ingestion_id` to a fresh timestamp so the storage path is unique.
8. Run `Test`.

Useful first payload:

- start from [`infra/events/mml-cercado-lima-licencias.csv.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/mml-cercado-lima-licencias.csv.json)

What to check after running:

- execution result says success
- response includes `bucket`, `raw_key`, and `manifest_key`
- CloudWatch logs show `Starting raw ingestion` and `Raw ingestion completed`
- objects exist in the target bucket path

## 5. How to run it manually with the AWS CLI

If you want CLI instead of console, this is the cleanest pattern.

### Step 1: refresh AWS auth if needed

If your AWS SSO session is expired, run your normal SSO login command first.

Example pattern:

```bash
aws sso login --profile <your-profile>
```

### Step 2: get the function name from CloudFormation

This avoids hardcoding the function name:

```bash
aws cloudformation describe-stacks \
  --stack-name peru-construction-raw-ingestion-dev \
  --region us-east-2 \
  --query "Stacks[0].Outputs[?OutputKey=='RawIngestionFunctionName'].OutputValue" \
  --output text
```

### Step 3: invoke it with one of the repo events

```bash
aws lambda invoke \
  --region us-east-2 \
  --function-name "$(aws cloudformation describe-stacks \
    --stack-name peru-construction-raw-ingestion-dev \
    --region us-east-2 \
    --query "Stacks[0].Outputs[?OutputKey=='RawIngestionFunctionName'].OutputValue" \
    --output text)" \
  --payload fileb://infra/events/mml-cercado-lima-licencias.csv.json \
  /tmp/raw-ingestion-response.json
```

### Step 4: inspect the response

```bash
cat /tmp/raw-ingestion-response.json
```

### Step 5: check logs

You can use the Lambda console, or the CLI if you know the log group name.

For a first learning pass, the console is easier:

- Lambda
- your function
- `Monitor`
- `View CloudWatch logs`

## 6. How to schedule it

The simplest AWS-native scheduling choice here is EventBridge Scheduler.

Why this is a good fit:

- it runs on a time schedule
- it can target Lambda directly
- it can send a fixed JSON payload

That fixed JSON payload is the key idea. Your schedule is not only "run every day." It is also "run with this exact event body."

## 7. How to schedule it in the console

### Using EventBridge Scheduler

1. Open AWS Console.
2. Search for `EventBridge Scheduler`.
3. Create schedule.
4. Choose either:
   - one-time schedule
   - recurring schedule
5. Choose the target type `AWS Lambda Invoke`.
6. Select your Lambda function.
7. In the input section, paste the event JSON you want the function to receive.
8. Choose or create the execution role the scheduler will use.
9. Create the schedule.

Important:

- if you want to ingest one source on a schedule, use one saved event payload
- if you want multiple sources on different cadences, create multiple schedules

That is often simpler than putting many URLs into one function call.

## 8. How to schedule it with the AWS CLI

EventBridge Scheduler CLI usually looks like this pattern:

```bash
aws scheduler create-schedule \
  --name raw-ingestion-mml-licencias-daily \
  --region us-east-2 \
  --schedule-expression 'rate(1 day)' \
  --flexible-time-window '{"Mode":"OFF"}' \
  --target '{
    "Arn":"<lambda-arn>",
    "RoleArn":"<scheduler-invoke-role-arn>",
    "Input":"{\"source_id\":\"peru-open-data\",\"dataset_id\":\"mml-resoluciones-licencias-edificacion\",\"resource_id\":\"cercado-lima-licencias-csv\",\"ingestion_id\":\"2026-04-05T03:00:00Z\",\"request\":{\"kind\":\"url\",\"url\":\"https://www.datosabiertos.gob.pe/sites/default/files/DATASET%20RESOLUCION%20DE%20LICENCIAS%20DE%20EDIFICACION%20MOD%20A%2CB%2CC%2CD.csv\",\"method\":\"GET\",\"headers\":{\"Referer\":\"https://www.datosabiertos.gob.pe/dataset/resoluciones-de-licencias-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima\"}},\"metadata\":{\"dataset_page_url\":\"https://www.datosabiertos.gob.pe/dataset/resoluciones-de-licencias-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima\",\"scope\":\"Cercado de Lima\",\"publisher\":\"Municipalidad Metropolitana de Lima\",\"signal_type\":\"permit_issuance\",\"notes\":\"Primary MML construction permit source for scheduled raw-ingestion testing.\"}}"
  }'
```

Two practical warnings:

1. `ingestion_id` should not be a permanently fixed value in a recurring schedule.
If you keep it fixed, your deterministic storage path will repeat and objects may overwrite each other.

2. Because of that, the current event contract is better for manual runs than for recurring schedules.
For a real recurring schedule, you will probably want a small wrapper pattern later, such as:

- scheduler triggers Lambda with a simpler event like `{ "job": "mml-licencias-daily" }`
- Lambda generates `ingestion_id` at runtime and maps the job name to the source config

That would be a better scheduling architecture than hardcoding timestamps into Scheduler input.

# How to change this safely later

1. Keep using manual test events until you are confident the event contract is stable.

2. When you are ready for schedules, do not schedule the current sample events unchanged if they contain a fixed `ingestion_id`.

3. Prefer one schedule per source at first.
That makes failures easier to isolate.

4. If you add scheduling in infrastructure as code later, put the schedule resource in the SAM/CloudFormation template instead of only creating it manually in the console.

5. If you expect many recurring sources, consider adding a wrapper contract:

- scheduler sends a small job identifier
- Lambda resolves the source config internally
- Lambda generates the current run timestamp itself

That design is easier to operate than maintaining large JSON payloads in many schedules.

# Terms or patterns to learn next

- Lambda invocation
- test event
- EventBridge Scheduler
- CloudWatch Logs
- custom event contract
- deterministic object keys
- infrastructure trigger vs runtime payload

# Read next

- [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py)
- [`app/lambda_app/models.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/models.py)
- [`infra/events/mml-cercado-lima-licencias.csv.json`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/infra/events/mml-cercado-lima-licencias.csv.json)
- [AWS Lambda console testing](https://docs.aws.amazon.com/lambda/latest/dg/testing-functions.html)
- [AWS SAM deploy behavior](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-deploy.html)
