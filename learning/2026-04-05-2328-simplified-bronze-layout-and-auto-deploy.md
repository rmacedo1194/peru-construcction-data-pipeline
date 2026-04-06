# What was built

I simplified the bronze storage layout and updated the deploy workflow to run automatically on pushes to `main`.

The raw-ingestion behavior now becomes:

- one source folder in the bucket
- one dated file per ingestion event
- no per-run folder tree
- no `manifest.json`

And the GitHub Actions workflow now starts automatically on:

- `push` to `main`
- manual `workflow_dispatch`

# Why it was built this way

Repo fact: the earlier storage design was optimized for traceability and replay safety. It created a deep path and wrote a manifest beside every payload.

General concept: that kind of design makes sense in larger data platforms, but it is too heavy for a learning project whose bronze goal is "download the raw file and land it in S3 in a clean place."

Decision rationale: for this repo, the simpler design is easier to browse, easier to explain, and easier to operate:

- `s3://bronze-rmm/peru-open-data/<timestamp>-<resource>.csv`

That matches your stated goal better than a warehouse-style raw partition layout.

For deployment, GitHub Actions cannot react to a local commit that stays on your machine. It can react to a `push` event on GitHub. So the practical version of "deploy every time I commit" is:

- commit locally
- push to GitHub
- GitHub Actions deploys automatically

# Key decisions and tradeoffs

## Decision 1: remove `manifest.json`

Why:

- reduces clutter in the bronze bucket
- keeps the bronze layer file-oriented
- matches the current project stage

Tradeoff:

- fetch metadata is no longer persisted as a sibling object
- debugging and lineage rely more on logs and the event payload used for invocation

## Decision 2: flatten the key structure

Why:

- easier S3 navigation
- easier public explanation
- simpler downstream expectations

Tradeoff:

- less path-level metadata
- uniqueness now depends mainly on the timestamped file name

## Decision 3: auto-deploy on `push` to `main`

Why:

- matches the workflow you asked for
- keeps deployment automatic only after code is actually published to GitHub

Tradeoff:

- every push to `main` becomes deploy-capable
- this is convenient for a learning project but would usually be stricter in larger teams

# Code walkthrough

## 1. Storage key generation

[`build_storage_paths()`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py) now creates a key like:

- `peru-open-data/2026-04-03T10-00-00Z-dataset-page-html.html`

The file name combines:

- the ingestion timestamp
- the `resource_id`
- the detected file extension

That gives you a readable and mostly collision-safe raw object key.

## 2. Prefix behavior

[`config.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/config.py) now defaults `RAW_PREFIX` to empty.

That is why the object key starts directly with `peru-open-data/...` instead of `raw/peru-open-data/...`.

## 3. Manifest removal

[`handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py) no longer builds or writes a manifest.

The storage writer interface also now writes only the payload.

## 4. Deploy trigger

[`deploy-dev.yml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/.github/workflows/deploy-dev.yml) now triggers on:

- `push` to `main`
- `workflow_dispatch`

That means the deploy runs automatically after each push to `main`.

# How to change this safely later

1. If you later need stronger lineage, do not jump immediately back to one `manifest.json` per file.

Consider lighter options first:

- richer CloudWatch logs
- a small run catalog file
- DynamoDB for ingestion run metadata

2. If you later want multiple environments, do not auto-deploy every branch.

Keep:

- `push` to `main` for `dev`
- protected/manual flow for more serious environments

3. If you later want prettier file names, you can swap `resource_id` for a dedicated field like `output_name`.

That would be cleaner than overloading `resource_id` forever.

# Terms or patterns to learn next

- S3 object key design
- deployment trigger
- GitHub Actions `push` event
- traceability vs operational simplicity
- file-oriented bronze layer

# Read next

- [`app/lambda_app/storage.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/storage.py)
- [`app/lambda_app/handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/app/lambda_app/handler.py)
- [`tests/test_handler.py`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/tests/test_handler.py)
- [`deploy-dev.yml`](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/.github/workflows/deploy-dev.yml)
