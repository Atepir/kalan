"""
Metrics collection and observability.

Tracks activity metrics, performance statistics, and system health.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Iterator, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ActivityMetric:
    """Represents metrics for a specific activity."""

    activity_type: str
    count: int = 0
    total_duration_seconds: float = 0.0
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    last_recorded: Optional[datetime] = None

    @property
    def average_duration(self) -> float:
        """Calculate average duration."""
        return self.total_duration_seconds / self.count if self.count > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0


@dataclass
class AgentMetrics:
    """Metrics specific to an agent."""

    agent_id: str
    activities: dict[str, ActivityMetric] = field(default_factory=dict)
    papers_read: int = 0
    papers_authored: int = 0
    teaching_sessions: int = 0
    experiments_run: int = 0
    total_experience: int = 0
    promotion_count: int = 0
    current_stage: str = "apprentice"
    reputation_score: float = 50.0
    last_active: Optional[datetime] = None


class MetricsCollector:
    """
    Global metrics collector for the research collective.

    Thread-safe collection of metrics across all agents and activities.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._lock = Lock()
        self._global_metrics: dict[str, ActivityMetric] = {}
        self._agent_metrics: dict[str, AgentMetrics] = {}
        self._community_stats: dict[str, Any] = {
            "total_agents": 0,
            "active_agents": 0,
            "total_papers_read": 0,
            "total_papers_authored": 0,
            "total_experiments": 0,
            "average_reputation": 0.0,
        }

    def record_activity(
        self,
        activity_type: str,
        duration_seconds: float,
        success: bool,
        agent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Record an activity with its metrics.

        Args:
            activity_type: Type of activity (learning, teaching, research, etc.)
            duration_seconds: How long the activity took
            success: Whether the activity succeeded
            agent_id: Optional agent ID for agent-specific tracking
            metadata: Additional metadata to log
        """
        with self._lock:
            # Update global metrics
            if activity_type not in self._global_metrics:
                self._global_metrics[activity_type] = ActivityMetric(activity_type=activity_type)

            metric = self._global_metrics[activity_type]
            metric.count += 1
            metric.total_duration_seconds += duration_seconds
            metric.last_recorded = datetime.utcnow()

            if metric.min_duration is None or duration_seconds < metric.min_duration:
                metric.min_duration = duration_seconds

            if metric.max_duration is None or duration_seconds > metric.max_duration:
                metric.max_duration = duration_seconds

            if success:
                metric.success_count += 1
            else:
                metric.failure_count += 1

            # Update agent-specific metrics if agent_id provided
            if agent_id:
                if agent_id not in self._agent_metrics:
                    self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

                agent_metric = self._agent_metrics[agent_id]
                if activity_type not in agent_metric.activities:
                    agent_metric.activities[activity_type] = ActivityMetric(activity_type=activity_type)

                agent_activity = agent_metric.activities[activity_type]
                agent_activity.count += 1
                agent_activity.total_duration_seconds += duration_seconds
                agent_activity.last_recorded = datetime.utcnow()

                if success:
                    agent_activity.success_count += 1
                else:
                    agent_activity.failure_count += 1

                agent_metric.last_active = datetime.utcnow()

        # Log the activity
        logger.info(
            "activity_recorded",
            activity_type=activity_type,
            duration=duration_seconds,
            success=success,
            agent_id=agent_id,
            **(metadata or {}),
        )

    def update_agent_state(
        self,
        agent_id: str,
        stage: Optional[str] = None,
        reputation: Optional[float] = None,
        total_experience: Optional[int] = None,
        papers_read: Optional[int] = None,
        papers_authored: Optional[int] = None,
    ) -> None:
        """Update agent state metrics."""
        with self._lock:
            if agent_id not in self._agent_metrics:
                self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

            agent_metric = self._agent_metrics[agent_id]

            if stage is not None:
                if agent_metric.current_stage != stage:
                    agent_metric.promotion_count += 1
                agent_metric.current_stage = stage

            if reputation is not None:
                agent_metric.reputation_score = reputation

            if total_experience is not None:
                agent_metric.total_experience = total_experience

            if papers_read is not None:
                agent_metric.papers_read = papers_read

            if papers_authored is not None:
                agent_metric.papers_authored = papers_authored

            agent_metric.last_active = datetime.utcnow()

    def get_activity_metrics(self, activity_type: Optional[str] = None) -> dict[str, Any]:
        """Get metrics for a specific activity or all activities."""
        with self._lock:
            if activity_type:
                metric = self._global_metrics.get(activity_type)
                if not metric:
                    return {}
                return {
                    "activity_type": metric.activity_type,
                    "count": metric.count,
                    "average_duration": metric.average_duration,
                    "min_duration": metric.min_duration,
                    "max_duration": metric.max_duration,
                    "success_rate": metric.success_rate,
                    "last_recorded": metric.last_recorded.isoformat() if metric.last_recorded else None,
                }
            else:
                return {
                    activity: {
                        "count": m.count,
                        "average_duration": m.average_duration,
                        "success_rate": m.success_rate,
                    }
                    for activity, m in self._global_metrics.items()
                }

    def get_agent_metrics(self, agent_id: str) -> dict[str, Any]:
        """Get all metrics for a specific agent."""
        with self._lock:
            agent_metric = self._agent_metrics.get(agent_id)
            if not agent_metric:
                return {"error": "Agent not found"}

            return {
                "agent_id": agent_metric.agent_id,
                "current_stage": agent_metric.current_stage,
                "reputation_score": agent_metric.reputation_score,
                "total_experience": agent_metric.total_experience,
                "papers_read": agent_metric.papers_read,
                "papers_authored": agent_metric.papers_authored,
                "teaching_sessions": agent_metric.teaching_sessions,
                "experiments_run": agent_metric.experiments_run,
                "promotion_count": agent_metric.promotion_count,
                "activities": {
                    activity: {
                        "count": m.count,
                        "average_duration": m.average_duration,
                        "success_rate": m.success_rate,
                    }
                    for activity, m in agent_metric.activities.items()
                },
                "last_active": agent_metric.last_active.isoformat() if agent_metric.last_active else None,
            }

    def get_community_summary(self) -> dict[str, Any]:
        """Get summary statistics for the entire community."""
        with self._lock:
            total_agents = len(self._agent_metrics)
            active_agents = sum(
                1
                for m in self._agent_metrics.values()
                if m.last_active and (datetime.utcnow() - m.last_active).days < 1
            )

            stage_distribution = defaultdict(int)
            for m in self._agent_metrics.values():
                stage_distribution[m.current_stage] += 1

            total_papers_read = sum(m.papers_read for m in self._agent_metrics.values())
            total_papers_authored = sum(m.papers_authored for m in self._agent_metrics.values())

            avg_reputation = (
                sum(m.reputation_score for m in self._agent_metrics.values()) / total_agents
                if total_agents > 0
                else 0.0
            )

            return {
                "total_agents": total_agents,
                "active_agents_24h": active_agents,
                "stage_distribution": dict(stage_distribution),
                "total_papers_read": total_papers_read,
                "total_papers_authored": total_papers_authored,
                "average_reputation": avg_reputation,
                "activity_summary": self.get_activity_metrics(),
            }

    def reset_metrics(self) -> None:
        """Reset all collected metrics (useful for testing)."""
        with self._lock:
            self._global_metrics.clear()
            self._agent_metrics.clear()
            self._community_stats.clear()

    def export_metrics(self) -> dict[str, Any]:
        """Export all metrics for external monitoring systems."""
        with self._lock:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "global_metrics": {
                    activity: {
                        "count": m.count,
                        "total_duration": m.total_duration_seconds,
                        "average_duration": m.average_duration,
                        "success_rate": m.success_rate,
                    }
                    for activity, m in self._global_metrics.items()
                },
                "agent_count": len(self._agent_metrics),
                "community_summary": self.get_community_summary(),
            }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_metric(
    metric_name: str,
    value: float = 1.0,
    metadata: Optional[dict[str, Any]] = None,
    agent_id: Optional[str] = None,
) -> None:
    """
    Record a metric value.

    Args:
        metric_name: Name of the metric to record
        value: Value to record (default 1.0 for counters)
        metadata: Optional metadata dictionary
        agent_id: Optional agent ID for agent-specific tracking
    """
    collector = get_metrics_collector()
    collector.record_activity(
        activity_type=metric_name,
        duration_seconds=value,
        success=True,
        agent_id=agent_id,
        metadata=metadata,
    )


@contextmanager
def track_activity(
    activity_type: str,
    agent_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Iterator[dict[str, Any]]:
    """
    Context manager for tracking activity duration and success.

    Usage:
        ```python
        with track_activity("learning", agent_id="agent_123") as ctx:
            # Do learning activity
            ctx["paper_id"] = "arxiv:1234"
            # ... work ...
            ctx["success"] = True  # Set to False on failure
        ```
    """
    start_time = time.time()
    context: dict[str, Any] = {"success": True}

    try:
        yield context
    except Exception as e:
        context["success"] = False
        context["error"] = str(e)
        raise
    finally:
        duration = time.time() - start_time
        success = context.get("success", False)

        metrics_metadata = metadata.copy() if metadata else {}
        metrics_metadata.update(context)

        collector = get_metrics_collector()
        collector.record_activity(
            activity_type=activity_type,
            duration_seconds=duration,
            success=success,
            agent_id=agent_id,
            metadata=metrics_metadata,
        )
