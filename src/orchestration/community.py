"""
Community management for agent coordination.

Manages the lifecycle of agents in the research community,
including registration, tracking, and coordination.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.agent import Agent, AgentStage
from src.orchestration.events import (
    EventType,
    emit_agent_created,
    emit_agent_promoted,
    get_event_bus,
)
from src.storage.state_store import get_state_store
from src.utils.logging import get_logger
from src.utils.metrics import record_metric

logger = get_logger(__name__)


@dataclass
class AgentStatus:
    """Status information for an agent in the community."""

    agent_id: UUID
    name: str
    stage: AgentStage
    specialization: str
    active: bool
    last_activity: datetime
    papers_read: int
    papers_reviewed: int
    experiments_run: int
    students_taught: int
    reputation_score: float
    knowledge_depth: float


class Community:
    """
    Manages the community of agents.

    Provides centralized coordination for agent lifecycle,
    status tracking, and community-wide operations.
    """

    def __init__(self):
        """Initialize community manager."""
        self.active_agents: dict[UUID, Agent] = {}
        self.agent_tasks: dict[UUID, asyncio.Task] = {}
        self.state_store = get_state_store()
        self.event_bus = get_event_bus()
        self.logger = get_logger(__name__)
        self._lock = asyncio.Lock()

    async def register_agent(self, agent: Agent) -> None:
        """
        Register a new agent in the community.

        Args:
            agent: Agent to register
        """
        async with self._lock:
            if UUID(agent.agent_id) in self.active_agents:
                self.logger.warning(
                    "agent_already_registered",
                    agent_id=agent.agent_id,
                )
                return

            # Add to active agents
            self.active_agents[UUID(agent.agent_id)] = agent

            # Save to persistent storage
            await self.state_store.save_agent(agent)

            self.logger.info(
                "agent_registered",
                agent_id=agent.agent_id,
                name=agent.name,
                stage=agent.stage.value,
            )

            # Record metric
            record_metric("agents.registered", 1, {"stage": agent.stage.value})

            # Emit event
            await emit_agent_created(
                UUID(agent.agent_id),
                {
                    "name": agent.name,
                    "stage": agent.stage.value,
                    "specialization": agent.specialization,
                },
            )

    async def unregister_agent(self, agent_id: UUID) -> None:
        """
        Unregister an agent from the community.

        Args:
            agent_id: ID of agent to unregister
        """
        async with self._lock:
            if agent_id not in self.active_agents:
                self.logger.warning(
                    "agent_not_found",
                    agent_id=str(agent_id),
                )
                return

            # Cancel any running tasks
            if agent_id in self.agent_tasks:
                task = self.agent_tasks[agent_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.agent_tasks[agent_id]

            # Remove from active agents
            agent = self.active_agents.pop(agent_id)

            self.logger.info(
                "agent_unregistered",
                agent_id=str(agent_id),
                name=agent.name,
            )

            # Record metric
            record_metric("agents.unregistered", 1, {"stage": agent.stage.value})

    async def load_agents_from_database(self) -> int:
        """
        Load all agents from the database into active memory.
        
        Returns:
            Number of agents loaded
        """
        self.logger.info("loading_agents_from_database")
        
        # Get list of agents from database
        agent_records = await self.state_store.list_agents(limit=1000)
        
        loaded_count = 0
        for record in agent_records:
            try:
                # Load full agent object
                agent_id = UUID(record["id"])
                agent = await self.state_store.load_agent(agent_id)
                
                if agent:
                    # Add to active agents without emitting events or saving
                    # (they're already in the database)
                    self.active_agents[UUID(agent.agent_id)] = agent
                    loaded_count += 1
                    
            except Exception as e:
                self.logger.error(
                    "failed_to_load_agent",
                    agent_id=record["id"],
                    error=str(e),
                )
        
        self.logger.info(
            "agents_loaded_from_database",
            count=loaded_count,
        )
        
        return loaded_count

    async def get_agent(self, agent_id: UUID) -> Agent | None:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent if found, None otherwise
        """
        return self.active_agents.get(agent_id)

    async def list_agents(
        self,
        stage: AgentStage | None = None,
        specialization: str | None = None,
        active_only: bool = True,
    ) -> list[Agent]:
        """
        List agents with optional filtering.

        Args:
            stage: Filter by developmental stage
            specialization: Filter by specialization
            active_only: Only return active agents

        Returns:
            List of agents
        """
        agents = list(self.active_agents.values()) if active_only else []

        # Load from database if not filtering by active only
        if not active_only:
            # TODO: Load from state store with filters
            pass

        # Apply filters
        if stage:
            agents = [a for a in agents if a.stage == stage]

        if specialization:
            agents = [
                a
                for a in agents
                if a.specialization.lower() == specialization.lower()
            ]

        return agents

    async def get_agent_status(self, agent_id: UUID) -> AgentStatus | None:
        """
        Get detailed status for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Agent status if found
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Get activity counts from event history
        event_history = self.event_bus.get_event_history(
            source_agent_id=agent_id,
            limit=1000,
        )

        papers_read = sum(1 for e in event_history if e.event_type == EventType.PAPER_READ)
        papers_reviewed = sum(
            1 for e in event_history if e.event_type == EventType.REVIEW_SUBMITTED
        )
        experiments_run = sum(
            1 for e in event_history if e.event_type == EventType.EXPERIMENT_COMPLETED
        )
        students_taught = sum(
            1 for e in event_history if e.event_type == EventType.TEACHING_SESSION_COMPLETED
        )

        # Get last activity timestamp
        last_activity = (
            max(e.timestamp for e in event_history)
            if event_history
            else agent.created_at
        )

        return AgentStatus(
            agent_id=UUID(agent.agent_id),
            name=agent.name,
            stage=agent.stage,
            specialization=agent.specialization or "",
            active=True,
            last_activity=last_activity,
            papers_read=papers_read,
            papers_reviewed=papers_reviewed,
            experiments_run=experiments_run,
            students_taught=students_taught,
            reputation_score=agent.reputation.overall,
            knowledge_depth=agent.knowledge.get_average_depth(),
        )

    async def promote_agent(self, agent_id: UUID) -> bool:
        """
        Attempt to promote an agent to the next stage.

        Args:
            agent_id: Agent ID

        Returns:
            True if promotion successful
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            self.logger.warning("agent_not_found_for_promotion", agent_id=str(agent_id))
            return False

        old_stage = agent.stage

        # Check if agent can be promoted
        readiness = agent.assess_readiness_for_promotion()
        if not readiness["ready"]:
            self.logger.info(
                "agent_not_ready_for_promotion",
                agent_id=str(agent_id),
                stage=agent.stage.value,
                missing=readiness["missing_requirements"],
            )
            return False

        # Promote agent
        new_stage = AgentStage(readiness["next_stage"])
        agent.promote(new_stage)

        # Save updated agent
        await self.state_store.update_agent_stage(UUID(agent.agent_id), new_stage)

        self.logger.info(
            "agent_promoted",
            agent_id=str(agent_id),
            old_stage=old_stage.value,
            new_stage=new_stage.value,
        )

        # Record metric
        record_metric(
            "agents.promoted",
            1,
            {"old_stage": old_stage.value, "new_stage": new_stage.value},
        )

        # Emit event
        await emit_agent_promoted(agent_id, old_stage.value, new_stage.value)

        return True

    async def get_community_stats(self) -> dict[str, Any]:
        """
        Get community-wide statistics.

        Returns:
            Statistics dictionary
        """
        agents = list(self.active_agents.values())

        # Count by stage
        stage_counts = {}
        for stage in AgentStage:
            count = sum(1 for a in agents if a.stage == stage)
            stage_counts[stage.value] = count

        # Count by specialization
        specialization_counts: dict[str, int] = {}
        for agent in agents:
            spec = agent.specialization
            specialization_counts[spec] = specialization_counts.get(spec, 0) + 1

        # Get event statistics
        event_stats = self.event_bus.get_statistics()

        return {
            "total_agents": len(agents),
            "active_agents": len(self.active_agents),
            "agents_by_stage": stage_counts,
            "agents_by_specialization": specialization_counts,
            "avg_reputation": (
                sum(a.reputation.overall for a in agents) / len(agents) if agents else 0.0
            ),
            "event_stats": event_stats,
        }

    async def start_agent_activity(
        self,
        agent_id: UUID,
        activity_coro: Any,
    ) -> None:
        """
        Start an asynchronous activity for an agent.

        Args:
            agent_id: Agent ID
            activity_coro: Coroutine to execute
        """
        # Cancel existing task if any
        if agent_id in self.agent_tasks:
            old_task = self.agent_tasks[agent_id]
            if not old_task.done():
                old_task.cancel()
                try:
                    await old_task
                except asyncio.CancelledError:
                    pass

        # Start new task
        task = asyncio.create_task(activity_coro)
        self.agent_tasks[agent_id] = task

        self.logger.info(
            "agent_activity_started",
            agent_id=str(agent_id),
        )

    async def stop_agent_activity(self, agent_id: UUID) -> None:
        """
        Stop an agent's current activity.

        Args:
            agent_id: Agent ID
        """
        if agent_id not in self.agent_tasks:
            return

        task = self.agent_tasks[agent_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        del self.agent_tasks[agent_id]

        self.logger.info(
            "agent_activity_stopped",
            agent_id=str(agent_id),
        )

    async def shutdown(self) -> None:
        """Shutdown the community, stopping all agent activities."""
        self.logger.info("shutting_down_community")

        # Cancel all tasks
        for agent_id in list(self.agent_tasks.keys()):
            await self.stop_agent_activity(agent_id)

        # Clear active agents
        self.active_agents.clear()

        self.logger.info("community_shutdown_complete")


# Global community singleton
_community: Community | None = None


def get_community() -> Community:
    """
    Get the global community instance.

    Returns:
        Community instance
    """
    global _community
    if _community is None:
        _community = Community()
    return _community
