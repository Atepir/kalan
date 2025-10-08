"""
Literature MCP Server package.

Provides access to research paper databases including arXiv and Semantic Scholar.
"""

from src.mcp_servers.literature.server import LiteratureServer
from src.mcp_servers.literature.tools import (
    search_arxiv,
    search_semantic_scholar,
    get_paper_details,
    get_citations,
)

__all__ = [
    "LiteratureServer",
    "search_arxiv",
    "search_semantic_scholar",
    "get_paper_details",
    "get_citations",
]
