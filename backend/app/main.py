import logging
import xml.etree.ElementTree as ET
import httpx
from fastapi import FastAPI, Query,HTTPException
from app.tools.arxiv import search_arxiv

logger = logging.getLogger(__name__) # that is getlogger object is used to log messages for a specific module or class. It allows you to control the logging level and format for that specific module or class, rather than using the root logger which applies to the entire application.

app =FastAPI(
    title="ARIA smart research assistant",
    description="ARIA is a smart research assistant that helps researchers to find relevant papers from arXiv and other sources. It uses advanced search algorithms to provide accurate and relevant results.",
    version="0.2.0"
)


@app.get("/")
def home():
    return {
        "message":"Welcome to ARIA",
        "project":"smart research assistant",
        "status":"running"
    }


@app.get("/health")
def health_check():
    return {
        "status":"healthy",
        "service":"ARIA backend"
    }


@app.get('/papers/search')
async def search_papers(
    query: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="The search query for papers.",
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description="The maximum number of papers to return.",
    ),
):


    """Fetch papers matching the query."""
    try:
        papers = await search_arxiv(query=query, max_results=limit)
        return papers
    except httpx.HTTPStatusError as exc:
        logger.warning("arxiv returned HTTP %s", exc.response.status_code)
        raise HTTPException(
            status_code=502,
            detail="arxiv rejected the API request",
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("arxiv connection error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="cannot reach arxiv right now",
        ) from exc
    except ET.ParseError as exc:
        logger.exception("invalid arxiv xml response")
        raise HTTPException(
            status_code=502,
            detail="arxiv returned invalid XML",
        ) from exc
    return {
        "query": query,
        "source": "arxiv",
        "total": len(papers),
        "papers": papers,
    }