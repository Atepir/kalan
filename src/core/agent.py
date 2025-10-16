"""
Agent state management module.

This module implements the core Agent class that manages individual agent identity,
knowledge state, developmental stage, reputation, and relationships within the
research collective.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from src.core.knowledge import KnowledgeGraph
from src.core.reputation import ReputationScore


class AgentStage(str, Enum):
    """Developmental stages for agents in the research collective."""

    APPRENTICE = "apprentice"  # Learning fundamentals
    PRACTITIONER = "practitioner"  # Applying knowledge
    TEACHER = "teacher"  # Educating others
    RESEARCHER = "researcher"  # Conducting original research
    EXPERT = "expert"  # Community leadership


class AgentGoal(BaseModel):
    """Represents an agent's goal with tracking information."""

    model_config = ConfigDict(frozen=False)

    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    target_metric: str  # e.g., "papers_read", "students_taught"
    target_value: float
    current_value: float = 0.0
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    priority: int = Field(default=5, ge=1, le=10)

    @property
    def progress(self) -> float:
        """Calculate goal progress as a percentage."""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    @property
    def is_completed(self) -> bool:
        """Check if goal is completed."""
        return self.current_value >= self.target_value

    def update_progress(self, value: float) -> None:
        """Update goal progress and mark as completed if target is reached."""
        self.current_value = value
        if self.is_completed and not self.completed_at:
            self.completed_at = datetime.utcnow()


class ExperienceLog(BaseModel):
    """Log entry for agent experiences and activities."""

    model_config = ConfigDict(frozen=True)

    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    activity_type: str  # "learning", "teaching", "research", "review"
    description: str
    outcome: str  # "success", "partial", "failure"
    confidence_change: Optional[float] = None
    knowledge_gained: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MentorshipRelation(BaseModel):
    """Represents a mentor-student relationship."""

    model_config = ConfigDict(frozen=False)

    relation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mentor_id: str
    student_id: str
    topics: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    sessions_count: int = 0
    student_progress: float = 0.0  # 0-100 scale
    mentor_rating: Optional[float] = None  # 0-5 scale
    is_active: bool = True

    def end_mentorship(self, rating: float) -> None:
        """End the mentorship relationship with a rating."""
        self.is_active = False
        self.ended_at = datetime.utcnow()
        self.mentor_rating = rating


class Agent(BaseModel):
    """
    Core Agent class representing an individual in the research collective.

    An agent has:
    - Unique identity and developmental stage
    - Personal knowledge graph
    - Reputation across multiple dimensions
    - Goals and progress tracking
    - Mentorship relationships
    - Experience history
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    # Identity
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    stage: AgentStage
    specialization: Optional[str] = None  # e.g., "machine_learning", "physics"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    # Knowledge and Skills
    knowledge: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    available_tools: list[str] = Field(default_factory=list)
    max_concurrent_activities: int = Field(default=2, ge=1, le=10)

    # Reputation and Progress
    reputation: ReputationScore = Field(default_factory=ReputationScore)
    total_experience_points: int = 0
    promotion_count: int = 0

    # Goals and Planning
    current_goals: list[AgentGoal] = Field(default_factory=list)
    completed_goals: list[AgentGoal] = Field(default_factory=list)

    # Relationships
    mentors: list[MentorshipRelation] = Field(default_factory=list)
    students: list[MentorshipRelation] = Field(default_factory=list)

    # Activity Tracking
    experience_log: list[ExperienceLog] = Field(default_factory=list)
    papers_read: list[str] = Field(default_factory=list)
    papers_authored: list[str] = Field(default_factory=list)
    experiments_conducted: list[str] = Field(default_factory=list)

    # Configuration
    requires_mentor: bool = True
    can_teach: bool = False
    can_conduct_research: bool = False
    can_review_papers: bool = False

    @model_validator(mode='after')
    def set_capabilities_from_stage(self) -> 'Agent':
        """
        Automatically set agent capabilities based on their developmental stage.
        This ensures agents created at higher stages have the proper capabilities.
        """
        stage_configs = {
            AgentStage.APPRENTICE: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "requires_mentor": True,
                "max_concurrent_activities": 2,
            },
            AgentStage.PRACTITIONER: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "requires_mentor": True,
                "max_concurrent_activities": 4,
            },
            AgentStage.TEACHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": False,
                "requires_mentor": False,
                "max_concurrent_activities": 6,
            },
            AgentStage.RESEARCHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "requires_mentor": False,
                "max_concurrent_activities": 8,
            },
            AgentStage.EXPERT: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "requires_mentor": False,
                "max_concurrent_activities": 10,
            },
        }
        
        config = stage_configs.get(self.stage, {})
        for key, value in config.items():
            setattr(self, key, value)
        
        return self

    def add_experience(
        self,
        activity_type: str,
        description: str,
        outcome: str,
        confidence_change: Optional[float] = None,
        knowledge_gained: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ExperienceLog:
        """Add an experience log entry."""
        log_entry = ExperienceLog(
            activity_type=activity_type,
            description=description,
            outcome=outcome,
            confidence_change=confidence_change,
            knowledge_gained=knowledge_gained or [],
            metadata=metadata or {},
        )
        self.experience_log.append(log_entry)
        self.last_active = datetime.utcnow()

        # Award experience points based on outcome
        xp_map = {"success": 10, "partial": 5, "failure": 2}
        self.total_experience_points += xp_map.get(outcome, 0)

        return log_entry

    def add_goal(
        self,
        description: str,
        target_metric: str,
        target_value: float,
        deadline: Optional[datetime] = None,
        priority: int = 5,
    ) -> AgentGoal:
        """Create and add a new goal for the agent."""
        goal = AgentGoal(
            description=description,
            target_metric=target_metric,
            target_value=target_value,
            deadline=deadline,
            priority=priority,
        )
        self.current_goals.append(goal)
        return goal

    def update_goal_progress(self, goal_id: str, value: float) -> None:
        """Update progress on a specific goal."""
        for goal in self.current_goals:
            if goal.goal_id == goal_id:
                goal.update_progress(value)
                if goal.is_completed:
                    self.current_goals.remove(goal)
                    self.completed_goals.append(goal)
                break

    def get_active_mentors(self) -> list[MentorshipRelation]:
        """Get all active mentorship relationships where agent is a student."""
        return [m for m in self.mentors if m.is_active]

    def get_active_students(self) -> list[MentorshipRelation]:
        """Get all active mentorship relationships where agent is a mentor."""
        return [s for s in self.students if s.is_active]

    def add_mentor(self, mentor_id: str, topics: Optional[list[str]] = None) -> MentorshipRelation:
        """Add a new mentor relationship."""
        relation = MentorshipRelation(
            mentor_id=mentor_id,
            student_id=self.agent_id,
            topics=topics or [],
        )
        self.mentors.append(relation)
        return relation

    def add_student(self, student_id: str, topics: Optional[list[str]] = None) -> MentorshipRelation:
        """Add a new student relationship."""
        relation = MentorshipRelation(
            mentor_id=self.agent_id,
            student_id=student_id,
            topics=topics or [],
        )
        self.students.append(relation)
        return relation

    def can_accept_student(self, max_students: int = 3) -> bool:
        """Check if agent can accept more students based on stage and current load."""
        if not self.can_teach:
            return False
        active_students = len(self.get_active_students())
        return active_students < max_students

    def assess_readiness_for_promotion(self) -> dict[str, Any]:
        """
        Assess agent's readiness for promotion to next stage.

        Returns a dictionary with:
        - ready: bool
        - current_stage: str
        - next_stage: str
        - criteria_met: dict[str, bool]
        - missing_requirements: list[str]
        """
        from src.core.evolution import PromotionCriteria

        criteria = PromotionCriteria.get_criteria_for_stage(self.stage)
        if not criteria:
            return {
                "ready": False,
                "current_stage": self.stage.value,
                "next_stage": None,
                "criteria_met": {},
                "missing_requirements": ["Already at highest stage"],
            }

        criteria_met: dict[str, bool] = {}
        missing: list[str] = []

        # Check papers read
        papers_ok = len(self.papers_read) >= criteria.min_papers_read
        criteria_met["papers_read"] = papers_ok
        if not papers_ok:
            missing.append(
                f"Read {criteria.min_papers_read - len(self.papers_read)} more papers"
            )

        # Check knowledge depth
        avg_depth = self.knowledge.get_average_depth()
        depth_ok = avg_depth >= criteria.min_knowledge_depth
        criteria_met["knowledge_depth"] = depth_ok
        if not depth_ok:
            missing.append(
                f"Increase knowledge depth to {criteria.min_knowledge_depth} (current: {avg_depth:.2f})"
            )

        # Check teaching (if required)
        if criteria.min_students_taught > 0:
            successful_students = sum(
                1 for s in self.students if not s.is_active and s.student_progress >= 70
            )
            teaching_ok = successful_students >= criteria.min_students_taught
            criteria_met["students_taught"] = teaching_ok
            if not teaching_ok:
                missing.append(
                    f"Successfully teach {criteria.min_students_taught - successful_students} more students"
                )

        # Check publications (if required)
        if criteria.min_publications > 0:
            pub_ok = len(self.papers_authored) >= criteria.min_publications
            criteria_met["publications"] = pub_ok
            if not pub_ok:
                missing.append(
                    f"Publish {criteria.min_publications - len(self.papers_authored)} more papers"
                )

        # Check reputation (if required)
        if criteria.min_reputation > 0:
            rep_ok = self.reputation.overall >= criteria.min_reputation
            criteria_met["reputation"] = rep_ok
            if not rep_ok:
                missing.append(f"Increase reputation to {criteria.min_reputation}")

        ready = all(criteria_met.values())

        return {
            "ready": ready,
            "current_stage": self.stage.value,
            "next_stage": criteria.next_stage.value,
            "criteria_met": criteria_met,
            "missing_requirements": missing,
        }

    def promote(self, new_stage: AgentStage) -> None:
        """Promote agent to a new developmental stage with updated capabilities."""
        self.stage = new_stage
        self.promotion_count += 1

        # Update capabilities based on stage
        stage_configs = {
            AgentStage.APPRENTICE: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "max_concurrent_activities": 2,
                "requires_mentor": True,
            },
            AgentStage.PRACTITIONER: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "max_concurrent_activities": 4,
                "requires_mentor": True,
            },
            AgentStage.TEACHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": False,
                "max_concurrent_activities": 6,
                "requires_mentor": False,
            },
            AgentStage.RESEARCHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "max_concurrent_activities": 8,
                "requires_mentor": False,
            },
            AgentStage.EXPERT: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "max_concurrent_activities": 10,
                "requires_mentor": False,
            },
        }

        config = stage_configs.get(new_stage, {})
        for key, value in config.items():
            setattr(self, key, value)

        # Log promotion event
        self.add_experience(
            activity_type="promotion",
            description=f"Promoted to {new_stage.value}",
            outcome="success",
            metadata={"new_stage": new_stage.value, "promotion_number": self.promotion_count},
        )

    def get_recent_experience(self, limit: int = 10) -> list[ExperienceLog]:
        """Get most recent experience log entries."""
        return sorted(self.experience_log, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_experience_by_type(self, activity_type: str) -> list[ExperienceLog]:
        """Get all experience logs of a specific type."""
        return [log for log in self.experience_log if log.activity_type == activity_type]

    def calculate_learning_velocity(self, days: int = 30) -> float:
        """Calculate agent's learning velocity (papers read per day) over recent period."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_learning = [
            log
            for log in self.experience_log
            if log.activity_type == "learning" and log.timestamp >= cutoff
        ]
        return len(recent_learning) / days if days > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary for serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """Create agent from dictionary."""
        return cls.model_validate(data)

    def __repr__(self) -> str:
        """String representation of agent."""
        return (
            f"Agent(id={self.agent_id[:8]}, name={self.name}, "
            f"stage={self.stage.value}, reputation={self.reputation.overall:.2f})"
        )
