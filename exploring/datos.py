from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import urljoin

import requests

BASE_URL = "https://www.datosabiertos.gob.pe"
DATASET_LIST_URL = f"{BASE_URL}/dataset"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}

# Each search result card is a self-contained HTML block, so parsing per card is
# more stable than scanning the whole page for unrelated links.
ARTICLE_PATTERN = re.compile(
    r'<article class="node-search-result row".*?</article>',
    re.DOTALL,
)
TITLE_PATTERN = re.compile(
    r'<h2 class="node-title"><a href="(?P<href>/dataset/[^"]+)"[^>]*>(?P<title>.*?)</a></h2>',
    re.DOTALL,
)
ORG_PATTERN = re.compile(r'<div class="group-membership">(?P<org>.*?)</div>', re.DOTALL)
TOPIC_PATTERN = re.compile(
    r'<a class="name" href="https://www\.datosabiertos\.gob\.pe/search/field_topic/[^"]+">(?P<topic>.*?)</a>',
    re.DOTALL,
)
FORMAT_PATTERN = re.compile(r'data-format="(?P<format>[^"]+)"')
LAST_PAGE_PATTERN = re.compile(r'class="pager-last[^"]*".*?href="(?P<href>[^"]+)"', re.DOTALL)
PAGE_NUMBER_PATTERN = re.compile(r"page=0%2C(?P<page>\d+)")


# A small structured model keeps the exploration phase readable and makes later
# download steps easier because the metadata already has a home.
@dataclass(frozen=True)
class DatasetEntry:
    page_number: int
    title: str
    url: str
    organization: str | None
    topics: tuple[str, ...]
    formats: tuple[str, ...]


def strip_tags(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def fetch_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def build_page_url(page_number: int) -> str:
    if page_number == 0:
        return DATASET_LIST_URL

    return (
        f"{BASE_URL}/search/type/dataset"
        f"?query=&sort_by=changed&sort_order=DESC&page=0%2C{page_number}"
    )


def extract_last_page_number(html: str) -> int:
    match = LAST_PAGE_PATTERN.search(html)
    if not match:
        return 0

    href = unescape(match.group("href"))
    page_match = PAGE_NUMBER_PATTERN.search(href)
    if not page_match:
        return 0

    return int(page_match.group("page"))


def extract_dataset_entries(html: str, page_number: int) -> list[DatasetEntry]:
    entries: list[DatasetEntry] = []

    for article_html in ARTICLE_PATTERN.findall(html):
        title_match = TITLE_PATTERN.search(article_html)
        if not title_match:
            continue

        title = strip_tags(title_match.group("title"))
        url = urljoin(BASE_URL, unescape(title_match.group("href")))

        org_match = ORG_PATTERN.search(article_html)
        organization = strip_tags(org_match.group("org")) if org_match else None

        topics = tuple(
            strip_tags(match.group("topic"))
            for match in TOPIC_PATTERN.finditer(article_html)
        )
        formats = tuple(dict.fromkeys(match.group("format").lower() for match in FORMAT_PATTERN.finditer(article_html)))

        entries.append(
            DatasetEntry(
                page_number=page_number,
                title=title,
                url=url,
                organization=organization,
                topics=topics,
                formats=formats,
            )
        )

    return entries


def iter_datasets(max_pages: int | None = None) -> Iterable[DatasetEntry]:
    session = requests.Session()
    session.headers.update(HEADERS)

    first_page_html = fetch_html(session, build_page_url(0))
    last_page_number = extract_last_page_number(first_page_html)

    if max_pages is not None:
        last_page_number = min(last_page_number, max_pages - 1)

    seen_urls: set[str] = set()

    for page_number in range(last_page_number + 1):
        html = first_page_html if page_number == 0 else fetch_html(session, build_page_url(page_number))
        for entry in extract_dataset_entries(html, page_number):
            if entry.url in seen_urls:
                continue
            seen_urls.add(entry.url)
            yield entry


def tokenize_query(query: str) -> list[str]:
    return [token for token in normalize_text(query).split() if token]


def matches_terms(entry: DatasetEntry, query_terms: list[str], match_mode: str) -> bool:
    if not query_terms:
        return True

    haystacks = [normalize_text(entry.title)]
    if entry.organization:
        haystacks.append(normalize_text(entry.organization))
    haystacks.extend(normalize_text(topic) for topic in entry.topics)

    present = [any(term in haystack for haystack in haystacks) for term in query_terms]
    if match_mode == "all":
        return all(present)
    return any(present)


def score_entry(entry: DatasetEntry, query: str, query_terms: list[str]) -> int:
    title = normalize_text(entry.title)
    organization = normalize_text(entry.organization or "")
    topics = [normalize_text(topic) for topic in entry.topics]

    score = 0

    if query and query in title:
        score += 100
    if query and query in organization:
        score += 40

    # This is a ranking heuristic, not a correctness rule. It helps surface the
    # most likely dataset pages first while keeping the code simple to inspect.
    for term in query_terms:
        if term in title:
            score += 20
        elif term in organization:
            score += 10
        elif any(term in topic for topic in topics):
            score += 8

    score += max(0, 10 - entry.page_number)
    return score


def explore_datasets(
    *,
    query: str | None,
    max_pages: int | None,
    limit: int,
    match_mode: str,
) -> tuple[list[DatasetEntry], int]:
    entries = list(iter_datasets(max_pages=max_pages))
    if not query:
        return entries[:limit], len(entries)

    normalized_query = normalize_text(query)
    query_terms = tokenize_query(query)

    matches = [
        entry
        for entry in entries
        if matches_terms(entry, query_terms, match_mode)
    ]
    matches.sort(
        key=lambda entry: (
            -score_entry(entry, normalized_query, query_terms),
            entry.page_number,
            entry.title,
        )
    )
    return matches[:limit], len(entries)


def print_entry(index: int, entry: DatasetEntry) -> None:
    print(f"{index}. {entry.title}")
    print(f"   URL: {entry.url}")
    print(f"   Page: {entry.page_number}")
    if entry.organization:
        print(f"   Organization: {entry.organization}")
    if entry.topics:
        print(f"   Topics: {', '.join(entry.topics)}")
    if entry.formats:
        print(f"   Formats: {', '.join(entry.formats)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore Peru open-data dataset pages and find the dataset URL you need."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Keywords to find likely dataset pages, for example: 'licencias construccion lima'.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Only scan the first N catalogue pages. Useful for quick tests.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum number of results to print.",
    )
    parser.add_argument(
        "--match",
        choices=("all", "any"),
        default="all",
        help="Require all query terms to match, or allow any matching term.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results, scanned_count = explore_datasets(
        query=args.query,
        max_pages=args.max_pages,
        limit=args.limit,
        match_mode=args.match,
    )

    if args.query:
        print(f"Scanned {scanned_count} datasets from the portal catalogue.")
        print(f"Best matches for query: {args.query!r}")
    else:
        print(f"Scanned {scanned_count} datasets from the portal catalogue.")
        print("No query provided, so showing the first datasets discovered.")

    if not results:
        print("No matching dataset pages were found.")
        return

    for index, entry in enumerate(results, start=1):
        print_entry(index, entry)


if __name__ == "__main__":
    main()
