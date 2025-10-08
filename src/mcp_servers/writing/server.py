"""
Writing MCP Server.

Provides Model Context Protocol server for document writing and LaTeX generation.
"""

from __future__ import annotations

from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.mcp_servers.writing.templates import (
    generate_latex_paper,
    generate_abstract,
    generate_section,
    generate_introduction,
    generate_related_work,
    generate_methodology,
    generate_conclusion,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WritingServer:
    """
    MCP Server for writing assistance.

    Provides LaTeX document generation and writing tools.
    """

    def __init__(self):
        """Initialize writing server."""
        self.server = Server("writing-server")
        self.logger = get_logger(__name__)
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available writing tools."""
            return [
                Tool(
                    name="generate_abstract",
                    description="Generate a research paper abstract",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Paper title"},
                            "research_question": {"type": "string", "description": "Research question"},
                            "methodology": {"type": "string", "description": "Methodology summary"},
                            "findings": {"type": "string", "description": "Key findings"},
                        },
                        "required": ["title", "research_question", "methodology", "findings"],
                    },
                ),
                Tool(
                    name="generate_introduction",
                    description="Generate an introduction section",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Research topic"},
                            "motivation": {"type": "string", "description": "Research motivation"},
                            "research_gap": {"type": "string", "description": "Gap in literature"},
                            "contribution": {"type": "string", "description": "Paper contribution"},
                        },
                        "required": ["topic", "motivation", "research_gap", "contribution"],
                    },
                ),
                Tool(
                    name="generate_methodology",
                    description="Generate a methodology section",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "approach": {"type": "string", "description": "Research approach"},
                            "datasets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Datasets used",
                            },
                            "evaluation_metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Evaluation metrics",
                            },
                        },
                        "required": ["approach", "datasets", "evaluation_metrics"],
                    },
                ),
                Tool(
                    name="generate_conclusion",
                    description="Generate a conclusion section",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "findings": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key findings",
                            },
                            "limitations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Study limitations",
                            },
                            "future_work": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Future research directions",
                            },
                        },
                        "required": ["findings", "limitations", "future_work"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute a writing tool."""
            self.logger.info("tool_called", tool=name)

            try:
                if name == "generate_abstract":
                    content = await generate_abstract(
                        title=arguments["title"],
                        research_question=arguments["research_question"],
                        methodology=arguments["methodology"],
                        findings=arguments["findings"],
                    )

                elif name == "generate_introduction":
                    content = await generate_introduction(
                        topic=arguments["topic"],
                        motivation=arguments["motivation"],
                        research_gap=arguments["research_gap"],
                        contribution=arguments["contribution"],
                    )

                elif name == "generate_methodology":
                    content = await generate_methodology(
                        approach=arguments["approach"],
                        datasets=arguments["datasets"],
                        evaluation_metrics=arguments["evaluation_metrics"],
                    )

                elif name == "generate_conclusion":
                    content = await generate_conclusion(
                        findings=arguments["findings"],
                        limitations=arguments["limitations"],
                        future_work=arguments["future_work"],
                    )

                else:
                    content = f"Unknown tool: {name}"

                return [TextContent(type="text", text=content)]

            except Exception as e:
                self.logger.error("tool_execution_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def start(self) -> None:
        """Start the MCP server."""
        self.logger.info("writing_server_starting")

    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("writing_server_stopping")
