# Lambda App Code Walkthrough

This note is for learning by reading code and then changing it carefully.

It is more concrete than the architecture note. Think of it as a guided walkthrough of how one request moves through the package.

## One Request, Step By Step

We start with a payload like this:

```json
{
  "dataset_id": "licencias-construccion-lima",
  "resource_id": "dataset-page-html",
  "ingestion_id": "2026-04-03T10:00:00Z",
  "request": {
    "kind": "url",
    "url": "https://www.datosabiertos.gob.pe/dataset/licencias-de-construccion"
  }
}
```

### Step 1: the handler receives the event

The first important call is:

```python
settings = Settings.from_env()
```

This reads environment variables such as:

- `RAW_BUCKET_NAME`
- `RAW_PREFIX`
- `STORAGE_BACKEND`
- `LOCAL_OUTPUT_DIR`

Why this matters:

The event should describe the ingestion request. The environment should describe where and how the function is running.

### Step 2: the raw dict becomes an `IngestionEvent`

Then the handler does:

```python
ingestion_event = IngestionEvent.from_dict(...)
```

That call checks:

- required identifiers exist
- `request.kind` is valid
- the URL exists
- the ingestion ID parses like a timestamp

If you break this validation, later code becomes less trustworthy because every function would need to protect itself from malformed input.

### Step 3: the downloader fetches the source

The next important call is:

```python
fetch_result = fetch_request(ingestion_event.request, settings)
```

This returns a `FetchResult` that contains:

- response body
- final URL
- content type
- content length
- status code
- checksum

The checksum is useful because it gives you a stable fingerprint of what was fetched, even if you are not doing full deduplication yet.

### Step 4: storage paths are calculated

The next call is:

```python
storage_paths = build_storage_paths(ingestion_event, fetch_result)
```

This is the idempotency anchor.

If these identifiers do not change:

- source
- dataset
- resource
- ingestion ID

then the resulting object path does not change either.

That means the same run can be replayed without creating multiple differently named raw objects.

### Step 5: the manifest is created

Then the code does:

```python
manifest = build_manifest(
    event=ingestion_event,
    fetch_result=fetch_result,
    storage_paths=storage_paths,
)
```

This turns the request plus the response plus the storage result into an audit document.

That matters because raw ingestion is not only about storing data. It is about storing evidence of what happened.

### Step 6: a storage backend is selected

Next:

```python
storage_writer = create_storage_writer(settings)
```

This is where the environment decides whether the write target is:

- S3
- filesystem mirror

Why this is a good design:

The handler does not need to know which backend it is using. It only needs a writer that supports the expected operations.

### Step 7: payload and manifest are written

Finally:

```python
storage_writer.write_raw_payload(storage_paths, fetch_result)
storage_writer.write_manifest(storage_paths, manifest)
```

That is the end of one ingestion unit.

## How To Read The Code Safely

If you are learning, do not read the package file-by-file in alphabetical order.

Read it in runtime order:

1. `handler.py`
2. `models.py`
3. `download.py`
4. `storage.py`
5. `config.py`

That order mirrors the flow of execution better.

## Good Learning Changes To Try

### Try 1: add one metadata field

Add this to the sample event:

```json
"metadata": {
  "source_page": "https://www.datosabiertos.gob.pe/dataset",
  "experiment": "learning-run"
}
```

Then confirm that the manifest captures it.

What you learn:

- how event metadata travels through the system
- where manifests are built

### Try 2: change the raw prefix

Change `RAW_PREFIX` and rerun SAM.

What you learn:

- config affects storage layout
- storage key generation is deterministic but configurable

### Try 3: break the event on purpose

Remove `ingestion_id` from the sample event.

What you learn:

- where validation happens
- what kind of failure happens at the boundary

This is a good safe failure because it teaches the contract without changing architecture.

## Changes That Teach The Wrong Lesson

These changes may look educational but actually distort the architecture:

1. adding random UUIDs into object keys
2. moving URL fetching directly into the handler
3. bypassing `IngestionEvent.from_dict()` and reading raw dictionaries everywhere
4. deleting the manifest because “the raw file is enough”

Those changes reduce clarity, traceability, and retry safety.

## Read Next

- [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py)
- [`app/lambda_app/download.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/download.py)
- [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`tests/test_handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/tests/test_handler.py)
