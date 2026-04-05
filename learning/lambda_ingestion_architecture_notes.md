# Lambda Ingestion Architecture Notes

This note explains the current `app/lambda_app/` package in a way that helps you both understand it and safely change it.

The focus here is twofold:

- why the architecture is shaped this way
- how the code actually flows at runtime

## Big Picture

Repo fact: this Lambda is not a crawler. It is a raw-ingestion unit.

That means one event should represent one ingestion request:

- validate the input
- fetch one trusted target
- generate deterministic storage paths
- write raw payload and manifest

General concept: that shape keeps the ingestion function testable, retryable, and easier to reason about than a Lambda that also tries to discover datasets dynamically.

## Runtime Flow Example

This is the mental model for one successful run:

```python
event -> lambda_handler()
      -> Settings.from_env()
      -> IngestionEvent.from_dict()
      -> fetch_request()
      -> build_storage_paths()
      -> build_manifest()
      -> create_storage_writer()
      -> write_raw_payload()
      -> write_manifest()
      -> success response
```

If you understand that chain, you understand the package.

## File: `handler.py`

### 1. Purpose of the file

Repo fact: [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py) is the Lambda entrypoint.

Its job is orchestration only:

- load config
- validate the event
- call the downloader
- call storage helpers
- return a small success payload

### 2. Key concepts used and why

- top-level orchestration: keeps the entrypoint small
- structured logging: makes Lambda runs easier to inspect
- explicit exception boundaries: validation errors and runtime failures are easier to interpret

Why this matters:

If `handler.py` also contained HTTP details, S3 details, and manifest-building logic, it would become the hardest file to change safely.

### 3. What it depends on, and what depends on it

It depends on:

- `config.py`
- `models.py`
- `download.py`
- `storage.py`

What depends on it:

- AWS Lambda runtime
- SAM local invoke

### 4. What would break if it were deleted

- Lambda would have no entrypoint
- SAM local invoke would fail
- cloud deployment would create a function that cannot execute your ingestion logic

### Example

```python
settings = Settings.from_env()
ingestion_event = IngestionEvent.from_dict(
    event,
    default_source_id=settings.source_name,
    default_bucket=settings.raw_bucket_name,
    default_prefix=settings.raw_prefix,
)
```

This is the point where raw input stops being “just a dict” and becomes validated application data.

## File: `config.py`

### 1. Purpose of the file

Repo fact: [`app/lambda_app/config.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/config.py) loads environment variables into a typed settings object.

### 2. Key concepts used and why

- `@dataclass(frozen=True)`: configuration becomes immutable once loaded
- environment-based configuration: same code can run locally or in AWS with different env values
- browser-like default headers: matches the source behavior discovered in [`exploring/datos.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/exploring/datos.py)

Why this matters:

Configuration is where environment differences should live. If local-vs-cloud logic leaked everywhere, the code would become hard to follow.

### 3. What it depends on, and what depends on it

It depends on:

- `os`
- `pathlib`

What depends on it:

- `handler.py`
- `download.py`
- `storage.py`

### 4. What would break if it were deleted

- there would be no validated env parsing
- local SAM and cloud deploys would become harder to keep aligned
- request posture and backend selection would become fragile

### Example

```python
storage_backend = os.getenv("STORAGE_BACKEND", "s3").strip().lower() or "s3"
```

This line is what lets the same handler run with S3 in AWS and with filesystem mirroring during local SAM simulation.

## File: `models.py`

### 1. Purpose of the file

Repo fact: [`app/lambda_app/models.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/models.py) defines the ingestion contract and the typed data structures used across the package.

### 2. Key concepts used and why

- `@dataclass`: gives readable structured objects
- validation at the boundary: invalid events fail early
- typed internal objects: later functions receive consistent inputs

Why this matters:

This file is where the system says: “what counts as a valid ingestion request?”

### 3. What it depends on, and what depends on it

It depends on:

- Python dataclasses
- datetime parsing

What depends on it:

- `handler.py`
- `download.py`
- `storage.py`
- tests

### 4. What would break if it were deleted

- event validation would disappear
- downstream code would go back to working with loose dictionaries
- contract errors would show up later and be harder to debug

### Example: event parsing

```python
event = {
    "dataset_id": "licencias-construccion-lima",
    "resource_id": "dataset-page-html",
    "ingestion_id": "2026-04-03T10:00:00Z",
    "request": {
        "kind": "url",
        "url": "https://www.datosabiertos.gob.pe/dataset/licencias-de-construccion",
    },
}
```

That event becomes an `IngestionEvent`, which means later code can safely say `event.request.url` instead of repeatedly checking raw dictionary keys.

## File: `download.py`

### 1. Purpose of the file

Repo fact: [`app/lambda_app/download.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/download.py) is the HTTP boundary.

It is responsible for:

- building the request
- applying the configured headers
- executing the fetch
- returning a structured `FetchResult`

### 2. Key concepts used and why

- one narrow HTTP function: easier to test and replace later
- explicit timeout: avoids hanging requests
- response metadata capture: needed for observability and manifest generation

Why this matters:

You do not want request logic duplicated inside the handler and inside tests.

### 3. What it depends on, and what depends on it

It depends on:

- `urllib.request`
- `config.py`
- `models.py`

What depends on it:

- `handler.py`

### 4. What would break if it were deleted

- the ingestion flow would lose its fetch capability
- the handler would either fail or have to absorb network logic

### Example

```python
headers = settings.default_request_headers()
headers.update(request.headers)
```

This is where caller-specific headers are layered on top of the portal-safe defaults.

## File: `storage.py`

### 1. Purpose of the file

Repo fact: [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py) now owns all persistence-related responsibilities:

- deterministic key generation
- manifest construction
- storage writer selection
- S3 persistence
- filesystem persistence for local SAM

### 2. Key concepts used and why

- deterministic path generation
- backend abstraction
- manifest as persistence metadata

Why this matters:

This file is where idempotency is currently anchored.

The current model is:

- same `source_id`
- same `dataset_id`
- same `resource_id`
- same `ingestion_id`

produce the same storage keys.

That means retries are path-idempotent: they overwrite the same objects instead of creating new ones with different random names.

Important clarification:

This is not full deduplication. If the payload changes but the identifiers stay the same, the new run will still overwrite the old object path.

### 3. What it depends on, and what depends on it

It depends on:

- `config.py`
- `models.py`
- `boto3` for S3 backend creation

What depends on it:

- `handler.py`
- tests

### 4. What would break if it were deleted

- there would be no stable raw/manifest key generation
- no persistence backend switch for SAM vs AWS
- no manifest creation
- no raw writes

### Example: deterministic key generation

```python
raw/peru-open-data/licencias-construccion-lima/dataset-page-html/2026/04/03/2026-04-03t10-00-00z/payload.html
```

This path exists because key generation is derived from business identifiers, not from random UUIDs.

That is good for:

- retries
- debugging
- replay
- downstream discoverability

### Example: manifest creation

```python
manifest = build_manifest(
    event=ingestion_event,
    fetch_result=fetch_result,
    storage_paths=storage_paths,
)
```

The manifest is the audit record of the raw ingestion step.

## Why `run_local.py` Was Removed

Repo fact: `run_local.py` is no longer needed because `sam local invoke` is now the official local execution path.

Why this decision was made:

- SAM is closer to the real Lambda runtime
- it uses the same infrastructure definition
- it tests the handler under the same packaging model used for deploy

General concept: one official local path is better than two overlapping local paths when the goal is learning and operational clarity.

Keeping both `run_local.py` and SAM would force you to ask:

- which one is the real behavior?
- which one should docs teach?
- which one should regressions trust?

For this repo, SAM is the better answer.

## Why The Package Is Split Into These Files

You were concerned that many modules might become a mess.

That concern is valid, but the current split is still reasonable after consolidation:

- `handler.py`: orchestration
- `config.py`: environment parsing
- `models.py`: contract and typed data
- `download.py`: HTTP boundary
- `storage.py`: persistence boundary

This is a good MVP split because each file owns one main reason to change.

What was removed:

- `manifest.py` was too small to justify its own module
- `run_local.py` duplicated the SAM-first local execution story

That is the moderate consolidation line: remove thin files, keep important boundaries.

## Safe Experiments

These are good beginner changes that should be safe if you want to learn by modifying code:

1. Change `REQUEST_TIMEOUT` in the SAM local env file and watch the handler still behave the same.
2. Add a harmless metadata field in the sample event and confirm it appears in the manifest.
3. Change the default `RAW_PREFIX` and see how the storage path changes.
4. Add a new non-sensitive request header and verify it appears in the manifest.

## Danger Zones

These are changes that can easily break the architecture or contract:

1. Removing `ingestion_id` validation in `models.py`
2. Changing key generation to use random values
3. Moving HTTP logic into `handler.py`
4. Making local filesystem writes target the mounted source tree instead of `/tmp` during SAM local invoke
5. Treating path-level idempotency as if it were full deduplication

## Read Next

- [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py)
- [`app/lambda_app/models.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/models.py)
- [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`learning/sam_local_run_decisions.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/learning/sam_local_run_decisions.md)
