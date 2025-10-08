"""
Storage layer for the MCP Research Collective.

This package provides interfaces to various storage backends:
- PostgreSQL (state_store) - Agent state, papers, experiments
- Vector Store (vector_store) - Simplified stub (Qdrant removed)
- Neo4j (graph_store) - Knowledge graphs and relationships
- Document storage for papers and artifacts
"""

from src.storage.document_store import DocumentStore
from src.storage.graph_store import GraphStore, Neo4jGraphStore
from src.storage.state_store import AgentStateStore, PostgresStateStore
from src.storage.vector_store import SimpleVectorStore, VectorStore

__all__ = [
    # State storage
    "AgentStateStore",
    "PostgresStateStore",
    # Vector storage
    "VectorStore",
    "SimpleVectorStore",
    # Graph storage
    "GraphStore",
    "Neo4jGraphStore",
    # Document storage
    "DocumentStore",
]
