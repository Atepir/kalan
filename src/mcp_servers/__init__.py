"""
MCP Servers for the Research Collective.

This package provides Model Context Protocol servers for:
- Literature search (arXiv, Semantic Scholar)
- Experiment execution (sandboxed code execution)
- Knowledge queries (vector and graph search)
- Writing assistance (LaTeX generation)
"""

from src.mcp_servers.experiments import ExperimentServer
from src.mcp_servers.knowledge import KnowledgeServer
from src.mcp_servers.literature import LiteratureServer
from src.mcp_servers.writing import WritingServer

__all__ = [
    "LiteratureServer",
    "ExperimentServer",
    "KnowledgeServer",
    "WritingServer",
]
