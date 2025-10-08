"""
Orchestration layer for the Research Collective.

This package coordinates multi-agent activities including:
- Community management and agent coordination
- Mentor-student matchmaking
- Research workflows using LangGraph
- Event-driven communication
"""

from src.orchestration.community import Community, get_community
from src.orchestration.events import EventBus, Event, EventType
from src.orchestration.matchmaking import Matchmaker, MentorshipMatch
from src.orchestration.workflows import (
    ResearchWorkflow,
    LearningWorkflow,
    CollaborationWorkflow,
)

__all__ = [
    # Community
    "Community",
    "get_community",
    # Events
    "EventBus",
    "Event",
    "EventType",
    # Matchmaking
    "Matchmaker",
    "MentorshipMatch",
    # Workflows
    "ResearchWorkflow",
    "LearningWorkflow",
    "CollaborationWorkflow",
]
