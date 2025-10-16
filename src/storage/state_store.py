"""
State storage using PostgreSQL.

This module provides persistent storage for agent state, papers,
experiments, and other structured data.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

from src.core.agent import Agent, AgentStage
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AgentStateStore(ABC):
    """Abstract interface for agent state storage."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def save_agent(self, agent: Agent) -> None:
        """Save agent state to database."""
        pass

    @abstractmethod
    async def load_agent(self, agent_id: UUID) -> Agent | None:
        """Load agent state from database."""
        pass

    @abstractmethod
    async def update_agent_stage(self, agent_id: UUID, new_stage: AgentStage) -> None:
        """Update agent's stage."""
        pass

    @abstractmethod
    async def list_agents(
        self, stage: AgentStage | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List agents, optionally filtered by stage."""
        pass

    @abstractmethod
    async def save_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save paper to database."""
        pass

    @abstractmethod
    async def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        """Retrieve paper from database."""
        pass

    @abstractmethod
    async def save_experiment(
        self,
        experiment_id: str,
        agent_id: UUID,
        hypothesis: str,
        results: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save experiment results."""
        pass

    @abstractmethod
    async def get_agent_experiments(
        self, agent_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get experiments by agent."""
        pass


class PostgresStateStore(AgentStateStore):
    """
    PostgreSQL implementation of agent state storage.

    Uses asyncpg for async database operations.
    """

    def __init__(self):
        """Initialize PostgreSQL state store."""
        self.settings = get_settings()
        self.pool: asyncpg.Pool | None = None
        self.logger = get_logger(__name__)

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        if self.pool is not None:
            # Check if pool is still usable
            try:
                async with self.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                self.logger.info("postgres_connection_already_established")
                return
            except Exception:
                # Pool is stale, close it and reconnect
                self.logger.warning("postgres_pool_stale_reconnecting")
                await self.pool.close()
                self.pool = None

        try:
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                ssl=False,  # Disable SSL for local Docker connections
                server_settings={'jit': 'off'}
            )
            self.logger.info("postgres_connection_established")
        except Exception as e:
            self.logger.error("postgres_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self.logger.info("postgres_connection_closed")

    async def save_agent(self, agent: Agent) -> None:
        """
        Save agent state to database.

        Args:
            agent: Agent to save
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                # Save agent core data
                await conn.execute(
                    """
                    INSERT INTO agents (
                        agent_id, name, stage, specialization,
                        reputation_teaching, reputation_research,
                        reputation_review, reputation_collaboration,
                        created_at, last_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        stage = EXCLUDED.stage,
                        specialization = EXCLUDED.specialization,
                        reputation_teaching = EXCLUDED.reputation_teaching,
                        reputation_research = EXCLUDED.reputation_research,
                        reputation_review = EXCLUDED.reputation_review,
                        reputation_collaboration = EXCLUDED.reputation_collaboration,
                        last_active = EXCLUDED.last_active
                    """,
                    agent.agent_id,
                    agent.name,
                    agent.stage.value,
                    agent.specialization or "",
                    agent.reputation.teaching,
                    agent.reputation.research,
                    agent.reputation.review,
                    agent.reputation.collaboration,
                    agent.created_at,
                    datetime.utcnow(),
                )

                # Save knowledge topics
                for topic_name, topic_knowledge in agent.knowledge.topics.items():
                    await conn.execute(
                        """
                        INSERT INTO knowledge_topics (
                            topic_id, agent_id, name, depth_score, breadth_score, confidence,
                            last_accessed, validated, validation_count
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (agent_id, name) DO UPDATE SET
                            depth_score = EXCLUDED.depth_score,
                            breadth_score = EXCLUDED.breadth_score,
                            confidence = EXCLUDED.confidence,
                            last_accessed = EXCLUDED.last_accessed,
                            validated = EXCLUDED.validated,
                            validation_count = EXCLUDED.validation_count
                        """,
                        topic_knowledge.topic_id,
                        agent.agent_id,
                        topic_name,
                        topic_knowledge.depth_score,
                        topic_knowledge.breadth_score,
                        topic_knowledge.confidence,
                        topic_knowledge.last_accessed,
                        topic_knowledge.validated,
                        topic_knowledge.validation_count,
                    )

            self.logger.info("agent_saved", agent_id=agent.agent_id)

        except Exception as e:
            self.logger.error("agent_save_failed", agent_id=agent.agent_id, error=str(e))
            # If connection error, try to reconnect
            if "connection" in str(e).lower():
                self.logger.warning("connection_error_reconnecting")
                self.pool = None
                await self.connect()
            raise

    async def load_agent(self, agent_id: UUID) -> Agent | None:
        """
        Load agent state from database.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                # Load agent core data
                row = await conn.fetchrow(
                    """
                    SELECT agent_id, name, stage, specialization,
                           reputation_teaching, reputation_research,
                           reputation_review, reputation_collaboration,
                           created_at
                    FROM agents
                    WHERE agent_id = $1
                    """,
                    agent_id,
                )

                if not row:
                    return None

                # Reconstruct Agent object from database row
                from src.core.reputation import ReputationScore
                
                # Reconstruct reputation
                reputation = ReputationScore(
                    teaching=row["reputation_teaching"] or 0.0,
                    research=row["reputation_research"] or 0.0,
                    review=row["reputation_review"] or 0.0,
                    collaboration=row["reputation_collaboration"] or 0.0,
                )
                
                # Create agent with minimal data
                # Knowledge graph and other complex state will be empty initially
                agent = Agent(
                    agent_id=str(row["agent_id"]),
                    name=row["name"],
                    stage=AgentStage(row["stage"]),
                    specialization=row["specialization"],
                    created_at=row["created_at"],
                    reputation=reputation,
                )

                self.logger.info("agent_loaded", agent_id=str(agent_id))
                return agent

        except Exception as e:
            self.logger.error("agent_load_failed", agent_id=str(agent_id), error=str(e))
            raise

    async def update_agent_stage(self, agent_id: UUID, new_stage: AgentStage) -> None:
        """
        Update agent's developmental stage.

        Args:
            agent_id: Agent identifier
            new_stage: New stage
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE agents
                    SET stage = $1, updated_at = $2
                    WHERE id = $3
                    """,
                    new_stage.value,
                    datetime.utcnow(),
                    agent_id,
                )

            self.logger.info(
                "agent_stage_updated",
                agent_id=str(agent_id),
                new_stage=new_stage.value,
            )

        except Exception as e:
            self.logger.error(
                "agent_stage_update_failed",
                agent_id=str(agent_id),
                error=str(e),
            )
            raise

    async def list_agents(
        self, stage: AgentStage | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List agents, optionally filtered by stage.

        Args:
            stage: Optional stage filter
            limit: Maximum number of agents to return

        Returns:
            List of agent records
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                if stage:
                    rows = await conn.fetch(
                        """
                        SELECT agent_id, name, stage, specialization, created_at
                        FROM agents
                        WHERE stage = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        stage.value,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT agent_id, name, stage, specialization, created_at
                        FROM agents
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )

                agents = []
                for row in rows:
                    agents.append({
                        "id": str(row["agent_id"]),
                        "name": row["name"],
                        "stage": row["stage"],
                        "specialization": row["specialization"],
                        "created_at": row["created_at"].isoformat(),
                    })

                return agents

        except Exception as e:
            self.logger.error("list_agents_failed", error=str(e))
            raise

    async def save_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Save paper to database.

        Args:
            paper_id: Paper identifier (e.g., arXiv ID)
            title: Paper title
            abstract: Paper abstract
            content: Optional full content
            metadata: Optional metadata (authors, venue, etc.)
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO papers (
                        paper_id, title, abstract, content, metadata,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (paper_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        abstract = EXCLUDED.abstract,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata
                    """,
                    paper_id,
                    title,
                    abstract,
                    content,
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow(),
                )

            self.logger.info("paper_saved", paper_id=paper_id)

        except Exception as e:
            self.logger.error("paper_save_failed", paper_id=paper_id, error=str(e))
            raise

    async def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        """
        Retrieve paper from database.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper data or None if not found
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT paper_id, title, abstract, content, metadata, created_at
                    FROM papers
                    WHERE paper_id = $1
                    """,
                    paper_id,
                )

                if not row:
                    return None

                return {
                    "paper_id": row["paper_id"],
                    "title": row["title"],
                    "abstract": row["abstract"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"].isoformat(),
                }

        except Exception as e:
            self.logger.error("paper_load_failed", paper_id=paper_id, error=str(e))
            raise

    async def save_experiment(
        self,
        experiment_id: str,
        agent_id: UUID,
        hypothesis: str,
        results: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Save experiment results.

        Args:
            experiment_id: Experiment identifier
            agent_id: Agent who conducted experiment
            hypothesis: Hypothesis being tested
            results: Experiment results
            metadata: Optional metadata
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO experiments (
                        experiment_id, agent_id, hypothesis, results,
                        metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (experiment_id) DO UPDATE SET
                        hypothesis = EXCLUDED.hypothesis,
                        results = EXCLUDED.results,
                        metadata = EXCLUDED.metadata
                    """,
                    experiment_id,
                    agent_id,
                    hypothesis,
                    json.dumps(results),
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow(),
                )

            self.logger.info(
                "experiment_saved",
                experiment_id=experiment_id,
                agent_id=str(agent_id),
            )

        except Exception as e:
            self.logger.error(
                "experiment_save_failed",
                experiment_id=experiment_id,
                error=str(e),
            )
            raise

    async def get_agent_experiments(
        self, agent_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get experiments conducted by an agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of experiments

        Returns:
            List of experiments
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT experiment_id, hypothesis, results, metadata, created_at
                    FROM experiments
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    agent_id,
                    limit,
                )

                experiments = []
                for row in rows:
                    experiments.append({
                        "experiment_id": row["experiment_id"],
                        "hypothesis": row["hypothesis"],
                        "results": json.loads(row["results"]),
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "created_at": row["created_at"].isoformat(),
                    })

                return experiments

        except Exception as e:
            self.logger.error(
                "get_experiments_failed",
                agent_id=str(agent_id),
                error=str(e),
            )
            raise


# Singleton instance
_state_store: PostgresStateStore | None = None


def get_state_store() -> PostgresStateStore:
    """
    Get the global state store instance.

    Returns:
        PostgresStateStore instance
    """
    global _state_store
    if _state_store is None:
        _state_store = PostgresStateStore()
    return _state_store
