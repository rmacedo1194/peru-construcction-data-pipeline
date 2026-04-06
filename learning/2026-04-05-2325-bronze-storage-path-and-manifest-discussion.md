# What was built

This note captures the storage design discussion for the raw-ingestion Lambda before changing the code.

The focus is:

- whether the S3 object path is too deep for this project
- whether `manifest.json` is necessary in the bronze bucket

No code was changed in this step. This is an architecture review note.

# Why it was built this way

Repo fact: the current storage layout is created in [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py).

The current raw object path is built from:

- storage prefix
- source ID
- dataset ID
- resource ID
- year
- month
- day
- ingestion ID

Then the payload is written as:

- `payload.csv`
- `payload.html`
- `payload.json`

And the same folder also gets:

- `manifest.json`

General concept: this is a traceability-first design. It is trying to preserve run history, replay safety, and source metadata.

Decision rationale: that kind of layout is often useful in data engineering systems when:

- many datasets share one bucket
- many runs happen over time
- you need an audit trail of what happened in each run

But the right design depends on the real project goal, not on generic best practice.

# Key decisions and tradeoffs

## Decision 1: flatten the raw storage path

Your proposed target is effectively:

- `s3://bronze-rmm/peru-open-data/<file-name>.csv`

or maybe:

- `s3://bronze-rmm/peru-open-data/<date>-<file-name>.csv`

Why this is attractive:

- much easier to browse in S3
- easier to explain publicly
- closer to how a human thinks about "downloaded files"
- matches a smaller learning project better than a warehouse-style partition path

Tradeoff:

- you lose some run-level traceability in the object key
- if the same dataset is ingested again, naming collisions become a real design question
- metadata that is not visible in the file name has to live somewhere else or be accepted as lost

## Decision 2: remove `manifest.json`

Why this is attractive:

- less clutter in the bucket
- simpler bronze layout
- easier to inspect manually

Tradeoff:

- you lose a structured record of:
  - requested URL
  - final URL after redirects
  - headers used
  - content type
  - checksum
  - fetch timestamp
  - source metadata

If you remove the manifest, you are choosing a file-only raw layer instead of a traceability-first raw layer.

## Decision 3: optimize for the real project stage

For this repo, the project goal right now is not enterprise-grade lineage. It is:

- learn architecture
- practice AWS deployment
- build a clean raw landing layer
- compare approaches later

That means a simpler layout is probably better than a highly normalized ingestion folder structure.

# Code walkthrough

## 1. Where the current path is created

[`build_storage_paths()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py) builds the current S3 key.

Today it creates a base key like:

`raw/peru-open-data/<dataset>/<resource>/YYYY/MM/DD/<ingestion-id>/`

Then it appends:

- `payload.<ext>`
- `manifest.json`

## 2. Where the manifest comes from

[`build_manifest()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py) collects runtime metadata into an `IngestionManifest`.

That manifest is then written by:

- [`S3StorageWriter.write_manifest()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`FilesystemStorageWriter.write_manifest()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)

## 3. What the tests currently assume

[`tests/test_handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/tests/test_handler.py) currently assumes:

- payload path ends with `/payload.<ext>`
- manifest path ends with `/manifest.json`
- both objects are written

So if the storage design changes, those tests should change too.

# How to change this safely later

If you choose simplicity, the clean design for this repo would be:

- remove `raw/` prefix from the object key
- keep only `source_id` as the folder
- write one file per event using a meaningful file name

Example:

- `s3://bronze-rmm/peru-open-data/2026-04-05-mml-cercado-lima-licencias.csv`

or if you want slightly more uniqueness:

- `s3://bronze-rmm/peru-open-data/2026-04-05T232500Z-mml-cercado-lima-licencias.csv`

My recommendation for this repo is:

1. simplify the key structure
2. remove `manifest.json`
3. keep source metadata in logs for now
4. if later you need lineage, add a lightweight catalog file or DynamoDB index instead of putting one manifest beside every raw object

That is simpler and fits the current project maturity better.

# Terms or patterns to learn next

- object key design
- data lineage
- traceability vs simplicity
- idempotency
- naming collisions
- bronze layer conventions

# Read next

- [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`tests/test_handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/tests/test_handler.py)
- [`docs/task_backlog.md`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/docs/task_backlog.md)
