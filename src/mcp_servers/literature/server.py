"""
Literature MCP Server.

Provides Model Context Protocol server for literature search and paper access.
"""

from __future__ import annotations

from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.mcp_servers.literature.tools import (
    search_arxiv,
    search_semantic_scholar,
    get_paper_details,
    get_citations,
    get_references,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LiteratureServer:
    """
    MCP Server for literature search and paper access.

    Provides tools for searching arXiv and Semantic Scholar,
    retrieving paper details, and tracking citations.
    """

    def __init__(self):
        """Initialize literature server."""
        self.server = Server("literature-server")
        self.logger = get_logger(__name__)
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available literature tools."""
            return [
                Tool(
                    name="search_arxiv",
                    description="Search arXiv for research papers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10,
                            },
                            "sort_by": {
                                "type": "string",
                                "enum": ["relevance", "date"],
                                "description": "Sort order",
                                "default": "relevance",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="search_semantic_scholar",
                    description="Search Semantic Scholar for research papers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_paper_details",
                    description="Get detailed information about a specific paper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "paper_id": {
                                "type": "string",
                                "description": "Paper identifier",
                            },
                            "source": {
                                "type": "string",
                                "enum": ["arxiv", "semantic_scholar"],
                                "description": "Source database",
                                "default": "arxiv",
                            },
                        },
                        "required": ["paper_id"],
                    },
                ),
                Tool(
                    name="get_citations",
                    description="Get papers that cite a given paper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "paper_id": {
                                "type": "string",
                                "description": "Paper identifier",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of citations",
                                "default": 20,
                            },
                        },
                        "required": ["paper_id"],
                    },
                ),
                Tool(
                    name="get_references",
                    description="Get papers referenced by a given paper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "paper_id": {
                                "type": "string",
                                "description": "Paper identifier",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of references",
                                "default": 20,
                            },
                        },
                        "required": ["paper_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute a literature tool."""
            self.logger.info("tool_called", tool=name, arguments=arguments)

            try:
                if name == "search_arxiv":
                    results = await search_arxiv(
                        query=arguments["query"],
                        max_results=arguments.get("max_results", 10),
                        sort_by=arguments.get("sort_by", "relevance"),
                    )
                    content = self._format_search_results(results)

                elif name == "search_semantic_scholar":
                    results = await search_semantic_scholar(
                        query=arguments["query"],
                        max_results=arguments.get("max_results", 10),
                    )
                    content = self._format_search_results(results)

                elif name == "get_paper_details":
                    paper = await get_paper_details(
                        paper_id=arguments["paper_id"],
                        source=arguments.get("source", "arxiv"),
                    )
                    content = self._format_paper_details(paper)

                elif name == "get_citations":
                    citations = await get_citations(
                        paper_id=arguments["paper_id"],
                        max_results=arguments.get("max_results", 20),
                    )
                    content = self._format_citations(citations)

                elif name == "get_references":
                    references = await get_references(
                        paper_id=arguments["paper_id"],
                        max_results=arguments.get("max_results", 20),
                    )
                    content = self._format_references(references)

                else:
                    content = f"Unknown tool: {name}"

                return [TextContent(type="text", text=content)]

            except Exception as e:
                self.logger.error("tool_execution_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _format_search_results(self, results: list) -> str:
        """Format search results for display."""
        if not results:
            return "No results found."

        lines = [f"Found {len(results)} papers:\n"]
        for i, paper in enumerate(results, 1):
            lines.append(f"{i}. {paper.title}")
            lines.append(f"   Authors: {', '.join(paper.authors[:3])}")
            lines.append(f"   ID: {paper.paper_id}")
            lines.append(f"   URL: {paper.url}")
            if paper.citation_count:
                lines.append(f"   Citations: {paper.citation_count}")
            lines.append(f"   Abstract: {paper.abstract[:200]}...")
            lines.append("")

        return "\n".join(lines)

    def _format_paper_details(self, paper: dict | None) -> str:
        """Format paper details for display."""
        if not paper:
            return "Paper not found."

        lines = [
            f"Title: {paper.get('title')}",
            f"ID: {paper.get('paper_id')}",
            f"Authors: {', '.join(paper.get('authors', []))}",
            f"URL: {paper.get('url')}",
            "",
            "Abstract:",
            paper.get('abstract', 'No abstract available'),
        ]

        if paper.get('citation_count'):
            lines.insert(4, f"Citations: {paper['citation_count']}")

        return "\n".join(lines)

    def _format_citations(self, citations: list) -> str:
        """Format citations for display."""
        if not citations:
            return "No citations found."

        lines = [f"Found {len(citations)} citing papers:\n"]
        for i, paper in enumerate(citations, 1):
            lines.append(f"{i}. {paper.get('title')}")
            lines.append(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
            lines.append(f"   Year: {paper.get('year')}")
            lines.append("")

        return "\n".join(lines)

    def _format_references(self, references: list) -> str:
        """Format references for display."""
        if not references:
            return "No references found."

        lines = [f"Found {len(references)} referenced papers:\n"]
        for i, paper in enumerate(references, 1):
            lines.append(f"{i}. {paper.get('title')}")
            lines.append(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
            lines.append(f"   Year: {paper.get('year')}")
            lines.append("")

        return "\n".join(lines)

    async def start(self) -> None:
        """Start the MCP server."""
        self.logger.info("literature_server_starting")
        # Server startup logic would go here
        # In practice, this would initialize the MCP transport layer

    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("literature_server_stopping")
        # Server shutdown logic would go here
