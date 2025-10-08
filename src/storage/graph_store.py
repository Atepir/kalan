"""
Graph storage using Neo4j.

This module provides knowledge graph storage for concepts,
relationships, and agent interactions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GraphStore(ABC):
    """Abstract interface for graph storage."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to graph database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def create_node(
        self, label: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a node in the graph."""
        pass

    @abstractmethod
    async def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Create a relationship between nodes."""
        pass

    @abstractmethod
    async def query(self, cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a Cypher query."""
        pass

    @abstractmethod
    async def find_related_concepts(
        self, concept: str, max_depth: int = 2
    ) -> list[dict[str, Any]]:
        """Find concepts related to a given concept."""
        pass


class Neo4jGraphStore(GraphStore):
    """
    Neo4j implementation of graph storage.

    Stores knowledge graphs, concept relationships, and collaboration networks.
    """

    def __init__(self):
        """Initialize Neo4j graph store."""
        self.settings = get_settings()
        self.driver: AsyncDriver | None = None
        self.logger = get_logger(__name__)

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self.driver is not None:
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )

            # Verify connectivity
            await self.driver.verify_connectivity()

            self.logger.info("neo4j_connection_established")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            self.logger.error("neo4j_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close connection to Neo4j."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self.logger.info("neo4j_connection_closed")

    async def create_node(
        self, label: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a node in the graph.

        Args:
            label: Node label (e.g., "Concept", "Agent", "Paper")
            properties: Node properties

        Returns:
            Created node data
        """
        if not self.driver:
            await self.connect()

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    f"""
                    CREATE (n:{label} $props)
                    RETURN n
                    """,
                    props=properties,
                )

                record = await result.single()
                node = dict(record["n"])

                self.logger.info(
                    "node_created",
                    label=label,
                    node_id=properties.get("id", "unknown"),
                )

                return node

        except Exception as e:
            self.logger.error(
                "node_creation_failed",
                label=label,
                error=str(e),
            )
            raise

    async def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Create a relationship between nodes.

        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
        """
        if not self.driver:
            await self.connect()

        try:
            async with self.driver.session() as session:
                props = properties or {}
                await session.run(
                    f"""
                    MATCH (a {{id: $from_id}})
                    MATCH (b {{id: $to_id}})
                    MERGE (a)-[r:{relationship_type}]->(b)
                    SET r += $props
                    RETURN r
                    """,
                    from_id=from_node_id,
                    to_id=to_node_id,
                    props=props,
                )

                self.logger.info(
                    "relationship_created",
                    from_id=from_node_id,
                    to_id=to_node_id,
                    type=relationship_type,
                )

        except Exception as e:
            self.logger.error(
                "relationship_creation_failed",
                from_id=from_node_id,
                to_id=to_node_id,
                error=str(e),
            )
            raise

    async def query(
        self, cypher: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query.

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records
        """
        if not self.driver:
            await self.connect()

        try:
            async with self.driver.session() as session:
                result = await session.run(cypher, parameters or {})
                records = await result.data()

                self.logger.debug(
                    "query_executed",
                    records_count=len(records),
                )

                return records

        except Exception as e:
            self.logger.error(
                "query_execution_failed",
                error=str(e),
            )
            raise

    async def find_related_concepts(
        self, concept: str, max_depth: int = 2
    ) -> list[dict[str, Any]]:
        """
        Find concepts related to a given concept.

        Args:
            concept: Starting concept
            max_depth: Maximum relationship depth to traverse

        Returns:
            List of related concepts with relationships
        """
        if not self.driver:
            await self.connect()

        try:
            cypher = """
            MATCH path = (c:Concept {name: $concept})-[*1..%d]-(related:Concept)
            RETURN DISTINCT related.name AS name,
                   related.domain AS domain,
                   length(path) AS distance,
                   [r in relationships(path) | type(r)] AS relationship_types
            ORDER BY distance, name
            """ % max_depth

            results = await self.query(cypher, {"concept": concept})

            self.logger.info(
                "related_concepts_found",
                concept=concept,
                count=len(results),
            )

            return results

        except Exception as e:
            self.logger.error(
                "find_related_concepts_failed",
                concept=concept,
                error=str(e),
            )
            raise

    async def store_agent_knowledge_graph(
        self, agent_id: UUID, topics: dict[str, Any]
    ) -> None:
        """
        Store an agent's knowledge graph.

        Args:
            agent_id: Agent identifier
            topics: Agent's knowledge topics
        """
        if not self.driver:
            await self.connect()

        try:
            agent_id_str = str(agent_id)

            # Create agent node
            await self.create_node(
                "Agent",
                {"id": agent_id_str, "type": "research_agent"},
            )

            # Create concept nodes and relationships
            for topic_name, topic_data in topics.items():
                # Create concept node
                await self.create_node(
                    "Concept",
                    {
                        "id": f"{agent_id_str}_{topic_name}",
                        "name": topic_name,
                        "depth": topic_data.get("depth", 0),
                        "confidence": topic_data.get("confidence", 0),
                    },
                )

                # Link agent to concept
                await self.create_relationship(
                    from_node_id=agent_id_str,
                    to_node_id=f"{agent_id_str}_{topic_name}",
                    relationship_type="KNOWS",
                    properties={
                        "depth": topic_data.get("depth", 0),
                        "confidence": topic_data.get("confidence", 0),
                    },
                )

            self.logger.info(
                "agent_knowledge_graph_stored",
                agent_id=agent_id_str,
                num_topics=len(topics),
            )

        except Exception as e:
            self.logger.error(
                "store_knowledge_graph_failed",
                agent_id=str(agent_id),
                error=str(e),
            )
            raise

    async def store_mentorship_relationship(
        self,
        mentor_id: UUID,
        student_id: UUID,
        topic: str,
        strength: float = 1.0,
    ) -> None:
        """
        Store a mentorship relationship.

        Args:
            mentor_id: Mentor agent ID
            student_id: Student agent ID
            topic: Topic being mentored
            strength: Relationship strength (0-1)
        """
        if not self.driver:
            await self.connect()

        try:
            await self.create_relationship(
                from_node_id=str(mentor_id),
                to_node_id=str(student_id),
                relationship_type="MENTORS",
                properties={
                    "topic": topic,
                    "strength": strength,
                },
            )

            self.logger.info(
                "mentorship_stored",
                mentor_id=str(mentor_id),
                student_id=str(student_id),
                topic=topic,
            )

        except Exception as e:
            self.logger.error(
                "store_mentorship_failed",
                mentor_id=str(mentor_id),
                student_id=str(student_id),
                error=str(e),
            )
            raise

    async def find_potential_mentors(
        self,
        student_id: UUID,
        topic: str,
        min_depth: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Find potential mentors for a student on a topic.

        Args:
            student_id: Student agent ID
            topic: Topic needing mentoring
            min_depth: Minimum knowledge depth required

        Returns:
            List of potential mentors
        """
        if not self.driver:
            await self.connect()

        try:
            cypher = """
            MATCH (mentor:Agent)-[k:KNOWS]->(c:Concept {name: $topic})
            WHERE k.depth >= $min_depth
              AND mentor.id <> $student_id
              AND NOT (mentor)-[:MENTORS]->(:Agent {id: $student_id})
            RETURN mentor.id AS mentor_id,
                   k.depth AS knowledge_depth,
                   k.confidence AS confidence
            ORDER BY k.depth DESC, k.confidence DESC
            LIMIT 10
            """

            results = await self.query(
                cypher,
                {
                    "topic": topic,
                    "min_depth": min_depth,
                    "student_id": str(student_id),
                },
            )

            self.logger.info(
                "potential_mentors_found",
                student_id=str(student_id),
                topic=topic,
                count=len(results),
            )

            return results

        except Exception as e:
            self.logger.error(
                "find_mentors_failed",
                student_id=str(student_id),
                topic=topic,
                error=str(e),
            )
            raise

    async def _create_indexes(self) -> None:
        """Create indexes for common queries."""
        try:
            async with self.driver.session() as session:
                # Index on node IDs
                await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Agent) ON (n.id)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.id)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.name)")
                await session.run("CREATE INDEX IF NOT EXISTS FOR (n:Paper) ON (n.id)")

            self.logger.info("indexes_created")

        except Exception as e:
            self.logger.warning("index_creation_failed", error=str(e))


# Singleton instance
_graph_store: Neo4jGraphStore | None = None


def get_graph_store() -> Neo4jGraphStore:
    """
    Get the global graph store instance.

    Returns:
        Neo4jGraphStore instance
    """
    global _graph_store
    if _graph_store is None:
        _graph_store = Neo4jGraphStore()
    return _graph_store
