"""
Experiments MCP Server.

Provides Model Context Protocol server for sandboxed code execution.
"""

from __future__ import annotations

from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.mcp_servers.experiments.sandbox import execute_python_code
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ExperimentServer:
    """
    MCP Server for experiment execution.

    Provides sandboxed Python code execution for research experiments.
    """

    def __init__(self):
        """Initialize experiment server."""
        self.server = Server("experiment-server")
        self.logger = get_logger(__name__)
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available experiment tools."""
            return [
                Tool(
                    name="execute_python",
                    description="Execute Python code in a sandboxed environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute",
                            },
                            "timeout_seconds": {
                                "type": "integer",
                                "description": "Maximum execution time",
                                "default": 300,
                            },
                        },
                        "required": ["code"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Execute an experiment tool."""
            self.logger.info("tool_called", tool=name)

            try:
                if name == "execute_python":
                    result = await execute_python_code(
                        code=arguments["code"],
                        timeout_seconds=arguments.get("timeout_seconds", 300),
                    )
                    content = self._format_execution_result(result)
                else:
                    content = f"Unknown tool: {name}"

                return [TextContent(type="text", text=content)]

            except Exception as e:
                self.logger.error("tool_execution_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _format_execution_result(self, result) -> str:
        """Format execution result for display."""
        lines = [
            f"Execution {'succeeded' if result.success else 'failed'}",
            f"Time: {result.execution_time_ms:.2f}ms",
            "",
        ]

        if result.stdout:
            lines.append("Output:")
            lines.append(result.stdout)
            lines.append("")

        if result.stderr:
            lines.append("Errors:")
            lines.append(result.stderr)
            lines.append("")

        if result.error:
            lines.append(f"Error: {result.error}")

        if result.return_value is not None:
            lines.append(f"Return value: {result.return_value}")

        return "\n".join(lines)

    async def start(self) -> None:
        """Start the MCP server."""
        self.logger.info("experiment_server_starting")

    async def stop(self) -> None:
        """Stop the MCP server."""
        self.logger.info("experiment_server_stopping")
