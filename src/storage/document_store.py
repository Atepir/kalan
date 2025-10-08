"""
Document storage for papers and artifacts.

This module provides storage for research papers, LaTeX documents,
and other research artifacts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for a stored document."""

    document_id: str
    title: str
    authors: list[str]
    document_type: str  # paper, latex, notebook, etc.
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime
    tags: list[str]
    metadata: dict[str, Any]


class DocumentStore:
    """
    File-based document storage.

    Stores research papers, LaTeX documents, and other artifacts
    on the file system with metadata tracking.
    """

    def __init__(self, base_path: Path | None = None):
        """
        Initialize document store.

        Args:
            base_path: Base directory for document storage
        """
        self.settings = get_settings()
        self.base_path = base_path or self.settings.data_dir / "documents"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

    def _get_document_path(self, document_id: str, extension: str = ".pdf") -> Path:
        """
        Get storage path for a document.

        Args:
            document_id: Document identifier
            extension: File extension

        Returns:
            Full path to document file
        """
        # Use first 2 chars of ID for subdirectory (sharding)
        subdir = document_id[:2] if len(document_id) >= 2 else "00"
        doc_dir = self.base_path / subdir
        doc_dir.mkdir(exist_ok=True)

        return doc_dir / f"{document_id}{extension}"

    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA256 checksum of content."""
        return hashlib.sha256(content).hexdigest()

    async def store_document(
        self,
        document_id: str,
        title: str,
        content: bytes,
        document_type: str = "paper",
        authors: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        extension: str = ".pdf",
    ) -> DocumentMetadata:
        """
        Store a document.

        Args:
            document_id: Unique document identifier
            title: Document title
            content: Document content (bytes)
            document_type: Type of document
            authors: List of authors
            tags: Optional tags
            metadata: Optional metadata
            extension: File extension

        Returns:
            Document metadata
        """
        try:
            # Get storage path
            file_path = self._get_document_path(document_id, extension)

            # Write content
            file_path.write_bytes(content)

            # Calculate checksum
            checksum = self._calculate_checksum(content)

            # Create metadata
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                title=title,
                authors=authors or [],
                document_type=document_type,
                file_path=str(file_path),
                file_size=len(content),
                checksum=checksum,
                created_at=datetime.utcnow(),
                tags=tags or [],
                metadata=metadata or {},
            )

            # Store metadata
            await self._store_metadata(doc_metadata)

            self.logger.info(
                "document_stored",
                document_id=document_id,
                size_bytes=len(content),
            )

            return doc_metadata

        except Exception as e:
            self.logger.error(
                "document_store_failed",
                document_id=document_id,
                error=str(e),
            )
            raise

    async def retrieve_document(
        self, document_id: str, extension: str = ".pdf"
    ) -> bytes | None:
        """
        Retrieve a document.

        Args:
            document_id: Document identifier
            extension: File extension

        Returns:
            Document content or None if not found
        """
        try:
            file_path = self._get_document_path(document_id, extension)

            if not file_path.exists():
                self.logger.warning(
                    "document_not_found",
                    document_id=document_id,
                )
                return None

            content = file_path.read_bytes()

            self.logger.info(
                "document_retrieved",
                document_id=document_id,
                size_bytes=len(content),
            )

            return content

        except Exception as e:
            self.logger.error(
                "document_retrieve_failed",
                document_id=document_id,
                error=str(e),
            )
            raise

    async def get_metadata(self, document_id: str) -> DocumentMetadata | None:
        """
        Get document metadata.

        Args:
            document_id: Document identifier

        Returns:
            Document metadata or None if not found
        """
        try:
            metadata_path = self.base_path / "metadata" / f"{document_id}.json"

            if not metadata_path.exists():
                return None

            import json

            data = json.loads(metadata_path.read_text())

            return DocumentMetadata(
                document_id=data["document_id"],
                title=data["title"],
                authors=data["authors"],
                document_type=data["document_type"],
                file_path=data["file_path"],
                file_size=data["file_size"],
                checksum=data["checksum"],
                created_at=datetime.fromisoformat(data["created_at"]),
                tags=data["tags"],
                metadata=data["metadata"],
            )

        except Exception as e:
            self.logger.error(
                "metadata_retrieve_failed",
                document_id=document_id,
                error=str(e),
            )
            raise

    async def delete_document(
        self, document_id: str, extension: str = ".pdf"
    ) -> bool:
        """
        Delete a document.

        Args:
            document_id: Document identifier
            extension: File extension

        Returns:
            True if deleted, False if not found
        """
        try:
            file_path = self._get_document_path(document_id, extension)

            if not file_path.exists():
                return False

            # Delete file
            file_path.unlink()

            # Delete metadata
            metadata_path = self.base_path / "metadata" / f"{document_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()

            self.logger.info(
                "document_deleted",
                document_id=document_id,
            )

            return True

        except Exception as e:
            self.logger.error(
                "document_delete_failed",
                document_id=document_id,
                error=str(e),
            )
            raise

    async def search_documents(
        self,
        document_type: str | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
    ) -> list[DocumentMetadata]:
        """
        Search for documents by criteria.

        Args:
            document_type: Filter by document type
            tags: Filter by tags (any match)
            author: Filter by author name

        Returns:
            List of matching document metadata
        """
        try:
            metadata_dir = self.base_path / "metadata"
            if not metadata_dir.exists():
                return []

            results = []
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    doc_meta = await self.get_metadata(metadata_file.stem)
                    if not doc_meta:
                        continue

                    # Apply filters
                    if document_type and doc_meta.document_type != document_type:
                        continue

                    if tags and not any(tag in doc_meta.tags for tag in tags):
                        continue

                    if author and author not in doc_meta.authors:
                        continue

                    results.append(doc_meta)

                except Exception as e:
                    self.logger.warning(
                        "metadata_read_failed",
                        file=str(metadata_file),
                        error=str(e),
                    )
                    continue

            self.logger.info(
                "document_search_complete",
                results_count=len(results),
            )

            return results

        except Exception as e:
            self.logger.error(
                "document_search_failed",
                error=str(e),
            )
            raise

    async def _store_metadata(self, metadata: DocumentMetadata) -> None:
        """Store document metadata to JSON file."""
        import json

        metadata_dir = self.base_path / "metadata"
        metadata_dir.mkdir(exist_ok=True)

        metadata_path = metadata_dir / f"{metadata.document_id}.json"

        data = {
            "document_id": metadata.document_id,
            "title": metadata.title,
            "authors": metadata.authors,
            "document_type": metadata.document_type,
            "file_path": metadata.file_path,
            "file_size": metadata.file_size,
            "checksum": metadata.checksum,
            "created_at": metadata.created_at.isoformat(),
            "tags": metadata.tags,
            "metadata": metadata.metadata,
        }

        metadata_path.write_text(json.dumps(data, indent=2))


# Singleton instance
_document_store: DocumentStore | None = None


def get_document_store() -> DocumentStore:
    """
    Get the global document store instance.

    Returns:
        DocumentStore instance
    """
    global _document_store
    if _document_store is None:
        _document_store = DocumentStore()
    return _document_store
