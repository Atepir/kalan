"""
Writing MCP Server package.

Provides LaTeX document generation and writing assistance.
"""

from src.mcp_servers.writing.server import WritingServer
from src.mcp_servers.writing.templates import (
    generate_latex_paper,
    generate_abstract,
    generate_section,
)

__all__ = [
    "WritingServer",
    "generate_latex_paper",
    "generate_abstract",
    "generate_section",
]
