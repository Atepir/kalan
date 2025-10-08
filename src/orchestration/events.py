"""
Event system for agent communication and coordination.

Provides event-driven architecture for agent interactions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine
from uuid import UUID, uuid4

from src.utils.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """Types of events in the system."""

    # Agent lifecycle
    AGENT_CREATED = "agent_created"
    AGENT_PROMOTED = "agent_promoted"
    AGENT_DELETED = "agent_deleted"

    # Learning events
    PAPER_READ = "paper_read"
    CONCEPT_LEARNED = "concept_learned"
    HELP_REQUESTED = "help_requested"
    HELP_RECEIVED = "help_received"

    # Teaching events
    TEACHING_SESSION_STARTED = "teaching_session_started"
    TEACHING_SESSION_COMPLETED = "teaching_session_completed"
    STUDENT_ASSESSED = "student_assessed"

    # Research events
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"
    PAPER_SUBMITTED = "paper_submitted"

    # Review events
    REVIEW_REQUESTED = "review_requested"
    REVIEW_SUBMITTED = "review_submitted"

    # Collaboration events
    COLLABORATION_PROPOSED = "collaboration_proposed"
    COLLABORATION_ACCEPTED = "collaboration_accepted"
    COLLABORATION_COMPLETED = "collaboration_completed"

    # System events
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_STOPPED = "simulation_stopped"


@dataclass
class Event:
    """Event in the system."""

    event_id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.AGENT_CREATED
    source_agent_id: UUID | None = None
    target_agent_id: UUID | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Event bus for publish-subscribe event handling.

    Allows agents and system components to subscribe to events
    and publish events for others to handle.
    """

    def __init__(self):
        """Initialize event bus."""
        self.handlers: dict[EventType, list[EventHandler]] = {}
        self.event_history: list[Event] = []
        self.logger = get_logger(__name__)
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)

        self.logger.info(
            "event_subscription_added",
            event_type=event_type.value,
            handler=handler.__name__,
        )

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                self.logger.info(
                    "event_subscription_removed",
                    event_type=event_type.value,
                    handler=handler.__name__,
                )
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        async with self._lock:
            self.event_history.append(event)

        self.logger.info(
            "event_published",
            event_id=str(event.event_id),
            event_type=event.event_type.value,
            source=str(event.source_agent_id) if event.source_agent_id else None,
        )

        # Get handlers for this event type
        handlers = self.handlers.get(event.event_type, [])

        if not handlers:
            self.logger.debug(
                "no_handlers_for_event",
                event_type=event.event_type.value,
            )
            return

        # Execute all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any handler failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "event_handler_failed",
                    event_type=event.event_type.value,
                    handler=handlers[i].__name__,
                    error=str(result),
                )

        # Mark event as processed
        event.processed = True

    async def publish_and_wait(self, event: Event) -> None:
        """
        Publish an event and wait for all handlers to complete.

        Args:
            event: Event to publish
        """
        await self.publish(event)

    def get_event_history(
        self,
        event_type: EventType | None = None,
        source_agent_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        Get event history with optional filtering.

        Args:
            event_type: Filter by event type
            source_agent_id: Filter by source agent
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        events = self.event_history

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source_agent_id:
            events = [e for e in events if e.source_agent_id == source_agent_id]

        # Return most recent events
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        self.logger.info("event_history_cleared")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_events": len(self.event_history),
            "processed_events": sum(1 for e in self.event_history if e.processed),
            "event_types": {},
            "subscribers": {
                event_type.value: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
        }

        # Count events by type
        for event in self.event_history:
            event_type = event.event_type.value
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1

        return stats


# Global event bus singleton
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns:
        EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Convenience functions for common events

async def emit_agent_created(agent_id: UUID, agent_data: dict[str, Any]) -> None:
    """Emit agent created event."""
    event_bus = get_event_bus()
    event = Event(
        event_type=EventType.AGENT_CREATED,
        source_agent_id=agent_id,
        data=agent_data,
    )
    await event_bus.publish(event)


async def emit_agent_promoted(agent_id: UUID, old_stage: str, new_stage: str) -> None:
    """Emit agent promoted event."""
    event_bus = get_event_bus()
    event = Event(
        event_type=EventType.AGENT_PROMOTED,
        source_agent_id=agent_id,
        data={"old_stage": old_stage, "new_stage": new_stage},
    )
    await event_bus.publish(event)


async def emit_paper_read(agent_id: UUID, paper_id: str, comprehension_level: str) -> None:
    """Emit paper read event."""
    event_bus = get_event_bus()
    event = Event(
        event_type=EventType.PAPER_READ,
        source_agent_id=agent_id,
        data={"paper_id": paper_id, "comprehension_level": comprehension_level},
    )
    await event_bus.publish(event)


async def emit_help_requested(student_id: UUID, topic: str, mentor_id: UUID | None = None) -> None:
    """Emit help requested event."""
    event_bus = get_event_bus()
    event = Event(
        event_type=EventType.HELP_REQUESTED,
        source_agent_id=student_id,
        target_agent_id=mentor_id,
        data={"topic": topic},
    )
    await event_bus.publish(event)


async def emit_experiment_completed(
    agent_id: UUID, experiment_id: str, success: bool
) -> None:
    """Emit experiment completed event."""
    event_bus = get_event_bus()
    event = Event(
        event_type=EventType.EXPERIMENT_COMPLETED,
        source_agent_id=agent_id,
        data={"experiment_id": experiment_id, "success": success},
    )
    await event_bus.publish(event)
