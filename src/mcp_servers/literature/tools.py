"""
Literature search tools for arXiv and Semantic Scholar.

Provides functions for searching papers, retrieving details, and citation tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import arxiv
import httpx

from src.storage.state_store import get_state_store
from src.storage.vector_store import get_vector_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PaperResult:
    """Result from paper search."""

    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: datetime
    url: str
    source: str  # arxiv, semantic_scholar
    citation_count: int = 0
    pdf_url: str | None = None
    venue: str | None = None


async def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> list[PaperResult]:
    """
    Search arXiv for papers.

    Args:
        query: Search query
        max_results: Maximum number of results
        sort_by: Sort order (relevance, date, citations)

    Returns:
        List of paper results
    """
    logger.info("searching_arxiv", query=query, max_results=max_results)

    try:
        # Map sort options to arxiv sort criteria
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "date": arxiv.SortCriterion.SubmittedDate,
            "citations": arxiv.SortCriterion.Relevance,  # arXiv doesn't support citation sorting
        }

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_map.get(sort_by, arxiv.SortCriterion.Relevance),
        )

        results = []
        for paper in search.results():
            result = PaperResult(
                paper_id=paper.entry_id.split("/")[-1],  # Extract arXiv ID
                title=paper.title,
                authors=[author.name for author in paper.authors],
                abstract=paper.summary,
                published_date=paper.published,
                url=paper.entry_id,
                source="arxiv",
                pdf_url=paper.pdf_url,
            )
            results.append(result)

            # Store in database for future reference
            state_store = get_state_store()
            await state_store.save_paper(
                paper_id=result.paper_id,
                title=result.title,
                abstract=result.abstract,
                metadata={
                    "authors": result.authors,
                    "published_date": result.published_date.isoformat(),
                    "url": result.url,
                    "pdf_url": result.pdf_url,
                    "source": "arxiv",
                },
            )

            # Store embedding for semantic search
            vector_store = get_vector_store()
            await vector_store.store_paper_embedding(
                paper_id=result.paper_id,
                title=result.title,
                abstract=result.abstract,
            )

        logger.info("arxiv_search_complete", results_count=len(results))
        return results

    except Exception as e:
        logger.error("arxiv_search_failed", query=query, error=str(e))
        raise


async def search_semantic_scholar(
    query: str,
    max_results: int = 10,
    fields: list[str] | None = None,
) -> list[PaperResult]:
    """
    Search Semantic Scholar for papers.

    Args:
        query: Search query
        max_results: Maximum number of results
        fields: Optional fields to retrieve

    Returns:
        List of paper results
    """
    logger.info("searching_semantic_scholar", query=query, max_results=max_results)

    try:
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

        # Default fields to retrieve
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "authors",
                "year",
                "citationCount",
                "url",
                "venue",
            ]

        params = {
            "query": query,
            "limit": max_results,
            "fields": ",".join(fields),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        results = []
        for paper in data.get("data", []):
            # Handle missing abstract
            abstract = paper.get("abstract", "No abstract available")
            if not abstract:
                abstract = "No abstract available"

            result = PaperResult(
                paper_id=paper["paperId"],
                title=paper.get("title", "Unknown Title"),
                authors=[author.get("name", "Unknown") for author in paper.get("authors", [])],
                abstract=abstract,
                published_date=datetime(paper.get("year", 2000), 1, 1),
                url=paper.get("url", ""),
                source="semantic_scholar",
                citation_count=paper.get("citationCount", 0),
                venue=paper.get("venue"),
            )
            results.append(result)

            # Store in database
            state_store = get_state_store()
            await state_store.save_paper(
                paper_id=result.paper_id,
                title=result.title,
                abstract=result.abstract,
                metadata={
                    "authors": result.authors,
                    "year": paper.get("year"),
                    "citation_count": result.citation_count,
                    "url": result.url,
                    "venue": result.venue,
                    "source": "semantic_scholar",
                },
            )

            # Store embedding
            vector_store = get_vector_store()
            await vector_store.store_paper_embedding(
                paper_id=result.paper_id,
                title=result.title,
                abstract=result.abstract,
            )

        logger.info("semantic_scholar_search_complete", results_count=len(results))
        return results

    except Exception as e:
        logger.error("semantic_scholar_search_failed", query=query, error=str(e))
        raise


async def get_paper_details(paper_id: str, source: str = "arxiv") -> dict[str, Any] | None:
    """
    Get detailed information about a paper.

    Args:
        paper_id: Paper identifier
        source: Source database (arxiv, semantic_scholar)

    Returns:
        Paper details or None if not found
    """
    logger.info("fetching_paper_details", paper_id=paper_id, source=source)

    try:
        # First check database
        state_store = get_state_store()
        paper = await state_store.get_paper(paper_id)

        if paper:
            logger.info("paper_found_in_database", paper_id=paper_id)
            return paper

        # If not in database, fetch from source
        if source == "arxiv":
            search = arxiv.Search(id_list=[paper_id])
            for paper_obj in search.results():
                paper = {
                    "paper_id": paper_id,
                    "title": paper_obj.title,
                    "abstract": paper_obj.summary,
                    "authors": [author.name for author in paper_obj.authors],
                    "published_date": paper_obj.published.isoformat(),
                    "url": paper_obj.entry_id,
                    "pdf_url": paper_obj.pdf_url,
                    "source": "arxiv",
                }

                # Save to database
                await state_store.save_paper(
                    paper_id=paper_id,
                    title=paper["title"],
                    abstract=paper["abstract"],
                    metadata=paper,
                )

                logger.info("paper_fetched_from_arxiv", paper_id=paper_id)
                return paper

        elif source == "semantic_scholar":
            async with httpx.AsyncClient() as client:
                url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
                params = {
                    "fields": "paperId,title,abstract,authors,year,citationCount,url,venue"
                }
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

            paper = {
                "paper_id": paper_id,
                "title": data.get("title"),
                "abstract": data.get("abstract", "No abstract available"),
                "authors": [author.get("name") for author in data.get("authors", [])],
                "year": data.get("year"),
                "citation_count": data.get("citationCount", 0),
                "url": data.get("url"),
                "venue": data.get("venue"),
                "source": "semantic_scholar",
            }

            # Save to database
            await state_store.save_paper(
                paper_id=paper_id,
                title=paper["title"],
                abstract=paper["abstract"],
                metadata=paper,
            )

            logger.info("paper_fetched_from_semantic_scholar", paper_id=paper_id)
            return paper

        logger.warning("paper_not_found", paper_id=paper_id, source=source)
        return None

    except Exception as e:
        logger.error("fetch_paper_details_failed", paper_id=paper_id, error=str(e))
        raise


async def get_citations(paper_id: str, max_results: int = 20) -> list[dict[str, Any]]:
    """
    Get papers that cite a given paper (Semantic Scholar only).

    Args:
        paper_id: Paper identifier
        max_results: Maximum number of citations

    Returns:
        List of citing papers
    """
    logger.info("fetching_citations", paper_id=paper_id, max_results=max_results)

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
            params = {
                "fields": "paperId,title,authors,year,citationCount",
                "limit": max_results,
            }
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        citations = []
        for item in data.get("data", []):
            citing_paper = item.get("citingPaper", {})
            citations.append({
                "paper_id": citing_paper.get("paperId"),
                "title": citing_paper.get("title"),
                "authors": [author.get("name") for author in citing_paper.get("authors", [])],
                "year": citing_paper.get("year"),
                "citation_count": citing_paper.get("citationCount", 0),
            })

        logger.info("citations_fetched", paper_id=paper_id, count=len(citations))
        return citations

    except Exception as e:
        logger.error("fetch_citations_failed", paper_id=paper_id, error=str(e))
        raise


async def get_references(paper_id: str, max_results: int = 20) -> list[dict[str, Any]]:
    """
    Get papers referenced by a given paper (Semantic Scholar only).

    Args:
        paper_id: Paper identifier
        max_results: Maximum number of references

    Returns:
        List of referenced papers
    """
    logger.info("fetching_references", paper_id=paper_id, max_results=max_results)

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
            params = {
                "fields": "paperId,title,authors,year,citationCount",
                "limit": max_results,
            }
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        references = []
        for item in data.get("data", []):
            cited_paper = item.get("citedPaper", {})
            references.append({
                "paper_id": cited_paper.get("paperId"),
                "title": cited_paper.get("title"),
                "authors": [author.get("name") for author in cited_paper.get("authors", [])],
                "year": cited_paper.get("year"),
                "citation_count": cited_paper.get("citationCount", 0),
            })

        logger.info("references_fetched", paper_id=paper_id, count=len(references))
        return references

    except Exception as e:
        logger.error("fetch_references_failed", paper_id=paper_id, error=str(e))
        raise
