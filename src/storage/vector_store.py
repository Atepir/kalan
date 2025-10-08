"""
Vector storage interface (simplified - Qdrant removed).

This module provides a stub interface for vector storage.
The implementation has been simplified by removing Qdrant dependency.
If you need vector search in the future, consider using PostgreSQL with pgvector.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore(ABC):
    """Abstract interface for vector storage."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to vector database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def create_collection(
        self, collection_name: str, vector_size: int, distance: str = "cosine"
    ) -> None:
        """Create a new collection for vectors."""
        pass

    @abstractmethod
    async def upsert_vectors(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]] | None = None,
    ) -> None:
        """Insert or update vectors."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete_vectors(
        self, collection_name: str, ids: list[str]
    ) -> None:
        """Delete vectors by ID."""
        pass


class SimpleVectorStore(VectorStore):
    """
    Simplified vector storage implementation (stub).

    This is a no-op implementation since Qdrant has been removed for simplicity.
    If you need vector search in the future, consider using PostgreSQL with pgvector.
    """

    def __init__(self):
        """Initialize simple vector store."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._collections: dict[str, dict] = {}
        self._connected = False

    async def connect(self) -> None:
        """Establish connection (no-op)."""
        if not self._connected:
            self.logger.info("vector_store_connected (stub implementation)")
            self._connected = True

    async def disconnect(self) -> None:
        """Close connection (no-op)."""
        if self._connected:
            self.logger.info("vector_store_disconnected")
            self._connected = False

    async def create_collection(
        self, collection_name: str, vector_size: int, distance: str = "cosine"
    ) -> None:
        """
        Create a new collection for vectors (no-op).

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (cosine, euclid, dot)
        """
        if collection_name not in self._collections:
            self._collections[collection_name] = {
                "vector_size": vector_size,
                "distance": distance,
                "vectors": {}
            }
            self.logger.info(
                "collection_created (stub)",
                collection=collection_name,
                vector_size=vector_size,
            )

    async def upsert_vectors(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Insert or update vectors in collection (no-op).

        Args:
            collection_name: Target collection
            ids: Vector IDs
            vectors: Vector embeddings
            payloads: Optional metadata for each vector
        """
        self.logger.info(
            "vectors_upserted (stub)",
            collection=collection_name,
            count=len(ids),
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors (returns empty list).

        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Maximum results to return
            filter_conditions: Optional filters on metadata

        Returns:
            Empty list (stub implementation)
        """
        self.logger.info(
            "vector_search_complete (stub)",
            collection=collection_name,
            results_count=0,
        )
        return []

    async def delete_vectors(
        self, collection_name: str, ids: list[str]
    ) -> None:
        """
        Delete vectors by ID (no-op).

        Args:
            collection_name: Collection name
            ids: Vector IDs to delete
        """
        self.logger.info(
            "vectors_deleted (stub)",
            collection=collection_name,
            count=len(ids),
        )

    async def store_paper_embedding(
        self,
        paper_id: str,
        title: str,
        abstract: str,
    ) -> None:
        """
        Store paper embedding (no-op).

        Args:
            paper_id: Unique paper identifier
            title: Paper title
            abstract: Paper abstract
        """
        self.logger.info(
            "paper_embedding_stored (stub)",
            paper_id=paper_id,
        )

    async def search_papers(
        self,
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar papers (returns empty list).

        Args:
            query_text: Search query
            limit: Maximum results
            filters: Optional metadata filters

        Returns:
            Empty list (stub implementation)
        """
        self.logger.info(
            "paper_search_complete (stub)",
            query=query_text,
            results_count=0,
        )
        return []

    async def store_concept_embedding(
        self,
        concept_id: UUID | str,
        name: str,
        description: str,
    ) -> None:
        """
        Store concept embedding (no-op).

        Args:
            concept_id: Unique concept identifier
            name: Concept name
            description: Concept description
        """
        self.logger.info(
            "concept_embedding_stored (stub)",
            concept_id=str(concept_id),
        )

    async def search_concepts(
        self,
        query_text: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for similar concepts (returns empty list).

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            Empty list (stub implementation)
        """
        self.logger.info(
            "concept_search_complete (stub)",
            query=query_text,
            results_count=0,
        )
        return []


# Singleton instance
_vector_store: SimpleVectorStore | None = None


def get_vector_store() -> SimpleVectorStore:
    """
    Get the singleton vector store instance.

    Returns:
        SimpleVectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = SimpleVectorStore()
    return _vector_store
