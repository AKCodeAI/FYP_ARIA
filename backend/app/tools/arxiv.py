
import re
import xml.etree.ElementTree as ET

import httpx


# Official arXiv API endpoint
ARXIV_URL = "https://export.arxiv.org/api/query"

# XML namespace used by arXiv's Atom response
ATOM = "{http://www.w3.org/2005/Atom}"


def clean_text(value: str | None) -> str:
    """Remove extra spaces and line breaks from text."""
    if value is None:
        return ""

    return re.sub(r"\s+", " ", value).strip()


def parse_papers(xml_content: str) -> list[dict]:
    """Convert arXiv Atom XML into structured paper data."""

    # Invalid XML should raise a ParseError.
    # FastAPI will handle this as an upstream failure.
    root = ET.fromstring(xml_content)

    papers = []

    for entry in root.findall(f"{ATOM}entry"):

        title = clean_text(
            entry.findtext(f"{ATOM}title")
        )

        abstract = clean_text(
            entry.findtext(f"{ATOM}summary")
        )

        url = clean_text(
            entry.findtext(f"{ATOM}id")
        )

        published = clean_text(
            entry.findtext(f"{ATOM}published")
        )

        # Extract paper authors
        authors = [
            clean_text(author.findtext(f"{ATOM}name"))
            for author in entry.findall(f"{ATOM}author")
        ]

        # Remove empty names
        authors = [name for name in authors if name]

        # Skip invalid entries
        if not title or not url or "api/errors" in url:
            continue

        papers.append({
            "id": url.rstrip("/").split("/")[-1],
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "url": url,
            "source": "arxiv",
        })

    return papers


async def search_arxiv(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    """Search arXiv using a research topic."""

    # Remove unwanted quotes and whitespace
    safe_query = clean_text(
        query.replace('"', " ")
    )

    if not safe_query:
        return []

    # arXiv search parameters
    params = {
        "search_query": f'all:"{safe_query}"',
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    # HTTP request headers
    headers = {
        "User-Agent": "ARIA-FYP/0.1 (academic research project)",
        "Accept": "application/atom+xml",
    }

    # Fetch real papers from the internet
    async with httpx.AsyncClient(timeout=20.0) as client:

        response = await client.get(
            ARXIV_URL,
            params=params,
            headers=headers,
        )

        # Raise HTTPStatusError for unsuccessful responses
        response.raise_for_status()

    # Convert the XML response into Python dictionaries
    return parse_papers(response.text)
