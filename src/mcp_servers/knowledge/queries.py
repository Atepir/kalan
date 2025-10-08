"""
Knowledge query functions for vector and graph stores.

Provides semantic search and graph traversal operations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.storage.graph_store import get_graph_store
from src.storage.vector_store import get_vector_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def semantic_search(
    query: str,
    collection: str = "research_knowledge",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Perform semantic search on vector store.

    Args:
        query: Search query
        collection: Collection to search
        limit: Maximum results

    Returns:
        List of search results
    """
    logger.info("semantic_search", query=query, collection=collection)

    try:
        vector_store = get_vector_store()
        await vector_store.connect()

        # Generate query embedding
        query_embedding = await vector_store.embed_text(query)

        # Search
        results = await vector_store.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=limit,
        )

        logger.info("semantic_search_complete", results_count=len(results))
        return results

    except Exception as e:
        logger.error("semantic_search_failed", query=query, error=str(e))
        raise


async def graph_query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Execute a Cypher query on the graph store.

    Args:
        cypher: Cypher query string
        parameters: Query parameters

    Returns:
        Query results
    """
    logger.info("graph_query", cypher=cypher[:100])

    try:
        graph_store = get_graph_store()
        await graph_store.connect()

        results = await graph_store.query(cypher, parameters)

        logger.info("graph_query_complete", results_count=len(results))
        return results

    except Exception as e:
        logger.error("graph_query_failed", error=str(e))
        raise


async def find_related_concepts(
    concept: str,
    max_depth: int = 2,
) -> list[dict[str, Any]]:
    """
    Find concepts related to a given concept.

    Args:
        concept: Starting concept
        max_depth: Maximum relationship depth

    Returns:
        List of related concepts
    """
    logger.info("find_related_concepts", concept=concept, max_depth=max_depth)

    try:
        graph_store = get_graph_store()
        await graph_store.connect()

        results = await graph_store.find_related_concepts(concept, max_depth)

        logger.info("related_concepts_found", concept=concept, count=len(results))
        return results

    except Exception as e:
        logger.error("find_related_concepts_failed", concept=concept, error=str(e))
        raise


async def get_agent_knowledge(agent_id: UUID) -> dict[str, Any]:
    """
    Get an agent's knowledge graph.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent's knowledge data
    """
    logger.info("get_agent_knowledge", agent_id=str(agent_id))

    try:
        graph_store = get_graph_store()
        await graph_store.connect()

        cypher = """
        MATCH (a:Agent {id: $agent_id})-[k:KNOWS]->(c:Concept)
        RETURN c.name AS concept,
               k.depth AS depth,
               k.confidence AS confidence
        ORDER BY k.depth DESC, k.confidence DESC
        """

        results = await graph_store.query(cypher, {"agent_id": str(agent_id)})

        knowledge_data = {
            "agent_id": str(agent_id),
            "concepts": [
                {
                    "name": r["concept"],
                    "depth": r["depth"],
                    "confidence": r["confidence"],
                }
                for r in results
            ],
        }

        logger.info(
            "agent_knowledge_retrieved",
            agent_id=str(agent_id),
            num_concepts=len(results),
        )

        return knowledge_data

    except Exception as e:
        logger.error("get_agent_knowledge_failed", agent_id=str(agent_id), error=str(e))
        raise


async def find_experts(
    topic: str,
    min_depth: float = 0.7,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Find agents who are experts on a topic.

    Args:
        topic: Topic to find experts for
        min_depth: Minimum knowledge depth
        limit: Maximum results

    Returns:
        List of expert agents
    """
    logger.info("find_experts", topic=topic, min_depth=min_depth)

    try:
        graph_store = get_graph_store()
        await graph_store.connect()

        cypher = """
        MATCH (a:Agent)-[k:KNOWS]->(c:Concept {name: $topic})
        WHERE k.depth >= $min_depth
        RETURN a.id AS agent_id,
               k.depth AS depth,
               k.confidence AS confidence
        ORDER BY k.depth DESC, k.confidence DESC
        LIMIT $limit
        """

        results = await graph_store.query(
            cypher,
            {
                "topic": topic,
                "min_depth": min_depth,
                "limit": limit,
            },
        )

        logger.info("experts_found", topic=topic, count=len(results))
        return results

    except Exception as e:
        logger.error("find_experts_failed", topic=topic, error=str(e))
        raise
