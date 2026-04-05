# Dataset Exploration Design Notes

Fecha: 2026-04-02

## Objective

Design `datos.py` as an exploration tool that helps answer this question first:

`Which dataset page URL should I inspect or download from?`

This is a different problem from:

`How do I download the files?`

That distinction matters because the Peru open data portal is easier to explore through its HTML catalogue than through one clean public catalogue API.

## The Main Design Idea

Before downloading anything, split the work into two phases:

1. Discovery
2. Download

### Why discovery comes first

If you skip discovery, you usually end up with a downloader that is too rigid:

- it assumes you already know the correct dataset URL
- it assumes the source has one clear API
- it mixes searching, filtering, parsing, and downloading in one place

That becomes hard to debug.

So the script was redesigned to behave like a small catalogue explorer:

- scan dataset listing pages
- extract dataset cards
- keep useful metadata
- rank likely matches for a keyword search
- print the dataset page URLs you should inspect next

## Why the script is not using a simple JSON API

The first assumption was reasonable:

```python
response = requests.get(url)
datasets = response.json()
```

That would be fine if the URL returned JSON.

But the portal homepage and dataset listing return HTML, not JSON.

Also, even though the platform exposes DKAN-style API behavior in some places, the global catalogue endpoints were not the most reliable entrypoint for exploration. The site is protected by a web application firewall, and requests that look like bot/API traffic can get blocked or behave differently.

So for exploration, the safer approach is:

- treat the catalogue as HTML
- parse the result cards
- use the dataset page URLs as the stable output of the exploration phase

This is a pragmatic backend decision:

- use API when it is clean and reliable
- use HTML parsing when the UI listing is the most dependable source of catalogue discovery

## What `datos.py` does now

The current design has five responsibilities.

### 1. Build catalogue page URLs

Function:

- `build_page_url(page_number)`

Why:

- keeps URL construction in one place
- makes pagination logic easy to inspect
- avoids hardcoding page URLs throughout the script

### 2. Fetch HTML with a reusable session

Function:

- `fetch_html(session, url)`

Why:

- one `requests.Session()` reuses connections
- browser-like headers reduce the chance of the portal returning WAF-style errors
- keeps HTTP concerns separate from parsing concerns

### 3. Parse one dataset card into structured data

Function:

- `extract_dataset_entries(html, page_number)`

Output model:

- `DatasetEntry`

Why this matters:

- the script is no longer passing around loose tuples everywhere
- a dataset now has a shape:
  - title
  - page URL
  - organization
  - topics
  - file formats
  - source page number

That structure will help later when building the downloader.

### 4. Iterate through the full catalogue

Function:

- `iter_datasets(max_pages=None)`

Why:

- hides pagination from the rest of the code
- yields one dataset at a time
- deduplicates repeated URLs

This is a useful backend pattern:

- one layer handles transport and pagination
- another layer handles filtering and business logic

### 5. Rank likely matches for a search query

Functions:

- `matches_terms(...)`
- `score_entry(...)`
- `explore_datasets(...)`

Why:

The goal is not just to dump thousands of datasets. The goal is to help you find the dataset page you probably want.

The ranking is intentionally simple:

- matches in the title score highest
- matches in the organization help, but less
- matches in topics help too
- earlier pages get a small bonus because they are usually more recent

This is not a search engine. It is a practical exploration heuristic.

That tradeoff is good here because:

- simple code is easier to maintain
- the ranking rules are easy to understand
- you can change the weights later without redesigning the script

## Why exploration metadata matters

The script prints:

- dataset title
- dataset page URL
- page number
- organization
- topics
- formats

This metadata matters because when you are deciding what to download, the dataset page title alone is usually not enough.

Examples:

- an organization name can tell you whether the data is municipal, regional, or national
- topics can tell you whether the dataset is really about construction, permits, urban development, or something adjacent
- formats tell you whether the next step will likely be CSV, XLSX, ZIP, or an API-backed resource

That means the explorer is already doing the first stage of dataset triage.

## How to think about the next script

The next script should not replace the explorer. It should consume its output.

Good backend separation would be:

1. `datos.py`
   - find likely dataset page URLs

2. `dataset_resources.py`
   - open one dataset page
   - extract resource links, formats, and possible API endpoints

3. `download_resources.py`
   - download files into a raw layer
   - track success/failure
   - save metadata manifest

This separation is worth it because each phase answers a different question.

### Explorer question

`Which dataset page should I use?`

### Resource extraction question

`What downloadable files or API resources exist on that page?`

### Download question

`Can I fetch them reliably and store them?`

## Design Tradeoffs

### Why regex parsing is acceptable here

Normally, HTML parsing with a dedicated parser is safer than regex.

But in this repo, the current tradeoff was:

- keep dependencies minimal
- avoid adding packages just to explore the catalogue
- target a repeated HTML card structure that is fairly regular

That makes regex acceptable for this stage, as long as we understand the limitation:

- if the portal markup changes significantly, the extractor may need updating

For a production crawler, moving to `BeautifulSoup` or `lxml` would be a reasonable upgrade.

### Why not download inside the same loop

Because that would mix two different failure modes:

- search/parsing failures
- file/API download failures

Keeping them separate makes debugging easier and makes retries cleaner.

### Why use a dataclass

`DatasetEntry` makes the code easier to read than raw tuples or dictionaries with ad-hoc keys.

It also teaches an important backend lesson:

- when data starts to have meaning, give it a clear shape

That reduces accidental mistakes later.

## Practical CLI examples

Explore recent datasets without filtering:

```bash
source .venv/bin/activate
python datos.py --max-pages 2
```

Search for datasets about licenses and construction:

```bash
source .venv/bin/activate
python datos.py --query "licencias construccion" --max-pages 40 --limit 10
```

Search more loosely when you are still exploring:

```bash
source .venv/bin/activate
python datos.py --query "urbano municipal" --match any --max-pages 40 --limit 15
```

## The Backend Thinking To Keep

When you work with public data portals, think in this order:

1. What is the discovery surface?
2. What is the resource surface?
3. What is the download mechanism?
4. What metadata should I save so I can reproduce the process later?

That order prevents a common mistake:

- building a downloader before you have a stable way to identify the right datasets

## Read next

- [datos.py](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/datos.py)
- [api_client_design_notes.md](/Users/rogermacedomilla/Documents/GitHub/peru-construcction-data-pipeline/docs/api_client_design_notes.md)
- Python `dataclasses`: [official docs](https://docs.python.org/3/library/dataclasses.html)
- Python `requests.Session`: [requests advanced usage](https://requests.readthedocs.io/en/latest/user/advanced/)
