"""
Knowledge MCP Server.

Provides Model Context Protocol server for knowledge queries.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.mcp_servers.knowledge.queries import (
    semantic_search,
    graph_query,
    find_related_concepts,
    get_agent_knowledge,
    find_experts,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeServer:
    """
    MCP Server for knowledge queries.

    Provides access to vector and graph knowledge stores.
    """

    def __init__(self):
        """Initialize knowledge server."""
        self.server = Server("knowledge-server")
        self.logger = get_logger(__name__)
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available knowledge tools."""
            return [
                Tool(
                    name="semantic_search",
                    description="Search knowledge base using semantic similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results",
                                "default": 10,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="find_related_concepts",
                    description="Find concepts related to a given concept",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "description": "Starting concept",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum relationship depth",
                                "default": 2,
                            },
                        },
                        "required": ["concept"],
                    },
                ),
                Tool(
                    name="get_agent_knowledge",
                    description="Get an agent's knowledge graph",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Agent identifier (UUID)",
                            },
                        },
                        "required": ["agent_id"],
                    },
                ),
                Tool(
                    name="find_experts",
                    description="Find agents who are experts on a topic",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic to find experts for",
                            },
                            "min_depth": {
                                "type": "number",
                                "description": "Minimum knowledge depth (0-1)",
                                "default": 0.7,
                            },
                        },
                        "required": ["topic"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute a knowledge tool."""
            self.logger.info("tool_called", tool=name)

            try:
                if name == "semantic_search":
                    results = await semantic_search(
                        query=arguments["query"],
                        limit=arguments.get("limit", 10),
                    )
                    content = self._format_search_results(results)

                elif name == "find_related_concepts":
                    results = await find_related_concepts(
                        concept=arguments["concept"],
                        max_depth=arguments.get("max_depth", 2),
                    )
                    content = self._format_related_concepts(results)

                elif name == "get_agent_knowledge":
                    agent_id = UUID(arguments["agent_id"])
                    knowledge = await get_agent_knowledge(agent_id)
                    content = self._format_agent_knowledge(knowledge)

                elif name == "find_experts":
                    results = await find_experts(
                        topic=arguments["topic"],
                        min_depth=arguments.get("min_depth", 0.7),
                    )
                    content = self._format_experts(results)

                else:
                    content = f"Unknown tool: {name}"

                return [TextContent(type="text", text=content)]

            except Exception as e:
                self.logger.error("tool_execution_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _format_search_results(self, results: list) -> str:
        """Format semantic search results."""
        if not results:
            return "No results found."

        lines = [f"Found {len(results)} results:\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. Score: {result['score']:.3f}")
            payload = result.get("payload", {})
            if payload.get("title"):
                lines.append(f"   Title: {payload['title']}")
            if payload.get("paper_id"):
                lines.append(f"   ID: {payload['paper_id']}")
            lines.append("")

        return "\n".join(lines)

    def _format_related_concepts(self, results: list) -> str:
        """Format related concepts results."""
        if not results:
            return "No related concepts found."

        lines = [f"Found {len(results)} related concepts:\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result.get('name')}")
            lines.append(f"   Distance: {result.get('distance')}")
            if result.get("relationship_types"):
                lines.append(f"   Relations: {', '.join(result['relationship_types'])}")
            lines.append("")

        return "\n".join(lines)

    def _format_agent_knowledge(self, knowledge: dict) -> str:
        """Format agent knowledge."""
        concepts = knowledge.get("concepts", [])
        if not concepts:
            return "Agent has no recorded knowledge."

        lines = [f"Agent {knowledge['agent_id']} knows {len(concepts)} concepts:\n"]
        for i, concept in enumerate(concepts, 1):
            lines.append(f"{i}. {concept['name']}")
            lines.append(f"   Depth: {concept['depth']:.2f}")
            lines.append(f"   Confidence: {concept['confidence']:.2f}")
            lines.append("")

        return "\n".join(lines)

    def _format_experts(self, results: list) -> str:
        """Format expert search results."""
        if not results:
            return "No experts found."

        lines = [f"Found {len(results)} experts:\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. Agent: {result.get('agent_id')}")
            lines.append(f"   Depth: {result.get('depth'):.2f}")
            lines.append(f"   Confidence: {result.get('confidence'):.2f}")
            lines.append("")

        return "\n".join(lines)

    async def start(self) -> None:
        """Start the MCP server."""
        self.logger.info("knowledge_server_starting")

    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("knowledge_server_stopping")
