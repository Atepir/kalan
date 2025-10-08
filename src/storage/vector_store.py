"""
Vector storage using Qdrant.

This module provides semantic search and embedding storage
using Qdrant vector database.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

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


class QdrantVectorStore(VectorStore):
    """
    Qdrant implementation of vector storage.

    Provides semantic search capabilities for papers, concepts, and embeddings.
    """

    def __init__(self):
        """Initialize Qdrant vector store."""
        self.settings = get_settings()
        self.client: AsyncQdrantClient | None = None
        self.logger = get_logger(__name__)

    async def connect(self) -> None:
        """Establish connection to Qdrant."""
        if self.client is not None:
            return

        try:
            self.client = AsyncQdrantClient(
                url=self.settings.qdrant_url,
                timeout=30.0,
            )
            self.logger.info("qdrant_connection_established")

            # Ensure default collection exists
            await self._ensure_default_collection()

        except Exception as e:
            self.logger.error("qdrant_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close connection to Qdrant."""
        if self.client:
            await self.client.close()
            self.client = None
            self.logger.info("qdrant_connection_closed")

    async def create_collection(
        self, collection_name: str, vector_size: int, distance: str = "cosine"
    ) -> None:
        """
        Create a new collection for vectors.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (cosine, euclid, dot)
        """
        if not self.client:
            await self.connect()

        try:
            distance_map = {
                "cosine": Distance.COSINE,
                "euclid": Distance.EUCLID,
                "dot": Distance.DOT,
            }

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE),
                ),
            )

            self.logger.info(
                "collection_created",
                collection=collection_name,
                vector_size=vector_size,
            )

        except Exception as e:
            self.logger.error(
                "collection_creation_failed",
                collection=collection_name,
                error=str(e),
            )
            raise

    async def upsert_vectors(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Insert or update vectors in collection.

        Args:
            collection_name: Target collection
            ids: Vector IDs
            vectors: Vector embeddings
            payloads: Optional metadata for each vector
        """
        if not self.client:
            await self.connect()

        try:
            if payloads is None:
                payloads = [{}] * len(ids)

            points = [
                PointStruct(id=id_, vector=vector, payload=payload)
                for id_, vector, payload in zip(ids, vectors, payloads)
            ]

            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            self.logger.info(
                "vectors_upserted",
                collection=collection_name,
                count=len(ids),
            )

        except Exception as e:
            self.logger.error(
                "vector_upsert_failed",
                collection=collection_name,
                error=str(e),
            )
            raise

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Maximum results to return
            filter_conditions: Optional filters on metadata

        Returns:
            List of search results with scores and payloads
        """
        if not self.client:
            await self.connect()

        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions,
            )

            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload or {},
                })

            self.logger.info(
                "vector_search_complete",
                collection=collection_name,
                results_count=len(search_results),
            )

            return search_results

        except Exception as e:
            self.logger.error(
                "vector_search_failed",
                collection=collection_name,
                error=str(e),
            )
            raise

    async def delete_vectors(
        self, collection_name: str, ids: list[str]
    ) -> None:
        """
        Delete vectors by ID.

        Args:
            collection_name: Collection name
            ids: Vector IDs to delete
        """
        if not self.client:
            await self.connect()

        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=ids,
            )

            self.logger.info(
                "vectors_deleted",
                collection=collection_name,
                count=len(ids),
            )

        except Exception as e:
            self.logger.error(
                "vector_deletion_failed",
                collection=collection_name,
                error=str(e),
            )
            raise

    async def _ensure_default_collection(self) -> None:
        """Ensure the default research_knowledge collection exists."""
        try:
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if "research_knowledge" not in collection_names:
                await self.create_collection(
                    collection_name="research_knowledge",
                    vector_size=384,  # Default embedding size
                    distance="cosine",
                )

        except Exception as e:
            self.logger.warning(
                "default_collection_check_failed",
                error=str(e),
            )

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Note: This is a placeholder. In production, use a proper embedding model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # TODO: Integrate with actual embedding model
        # For now, return dummy vector
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Generate deterministic "embedding"
        embedding = [(hash_int >> i) % 1000 / 1000.0 for i in range(384)]

        return embedding

    async def store_paper_embedding(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        embedding: list[float] | None = None,
    ) -> None:
        """
        Store paper embedding for semantic search.

        Args:
            paper_id: Paper identifier
            title: Paper title
            abstract: Paper abstract
            embedding: Pre-computed embedding (or will generate)
        """
        if embedding is None:
            # Generate embedding from title + abstract
            text = f"{title}\n\n{abstract}"
            embedding = await self.embed_text(text)

        payload = {
            "paper_id": paper_id,
            "title": title,
            "abstract": abstract,
            "type": "paper",
        }

        await self.upsert_vectors(
            collection_name="research_knowledge",
            ids=[paper_id],
            vectors=[embedding],
            payloads=[payload],
        )

    async def search_similar_papers(
        self,
        query_text: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for papers similar to query text.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            List of similar papers
        """
        query_embedding = await self.embed_text(query_text)

        results = await self.search(
            collection_name="research_knowledge",
            query_vector=query_embedding,
            limit=limit,
            filter_conditions={"type": "paper"},
        )

        return results


# Singleton instance
_vector_store: QdrantVectorStore | None = None


def get_vector_store() -> QdrantVectorStore:
    """
    Get the global vector store instance.

    Returns:
        QdrantVectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _vector_store
