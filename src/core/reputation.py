"""
Reputation and assessment systems.

This module implements multi-dimensional reputation tracking for agents,
measuring their contributions to teaching, research, review, and collaboration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class ReputationScore(BaseModel):
    """
    Multi-dimensional reputation tracking for an agent.

    Tracks reputation across different activities:
    - Teaching: Quality of mentorship and instruction
    - Research: Quality and impact of research outputs
    - Review: Quality of peer reviews provided
    - Collaboration: Effectiveness as a collaborator
    """

    model_config = ConfigDict(frozen=False)

    # Individual reputation dimensions (0-100 scale)
    teaching: float = Field(default=50.0, ge=0.0, le=100.0)
    research: float = Field(default=50.0, ge=0.0, le=100.0)
    review: float = Field(default=50.0, ge=0.0, le=100.0)
    collaboration: float = Field(default=50.0, ge=0.0, le=100.0)

    # Activity counts
    teaching_sessions: int = 0
    papers_published: int = 0
    reviews_completed: int = 0
    collaborations: int = 0

    # Impact metrics
    citation_count: int = 0
    h_index: int = 0
    student_success_rate: float = 0.0  # % of students who progressed
    review_helpfulness: float = 0.0  # Avg rating of reviews

    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def overall(self) -> float:
        """Calculate overall reputation as weighted average."""
        return (
            self.teaching * 0.25
            + self.research * 0.35
            + self.review * 0.20
            + self.collaboration * 0.20
        )

    def update_teaching_reputation(self, delta: float, reason: str = "") -> None:
        """Update teaching reputation with bounds checking."""
        self.teaching = max(0.0, min(100.0, self.teaching + delta))
        self.teaching_sessions += 1
        self.last_updated = datetime.utcnow()

    def update_research_reputation(self, delta: float, reason: str = "") -> None:
        """Update research reputation with bounds checking."""
        self.research = max(0.0, min(100.0, self.research + delta))
        self.last_updated = datetime.utcnow()

    def update_review_reputation(self, delta: float, reason: str = "") -> None:
        """Update review reputation with bounds checking."""
        self.review = max(0.0, min(100.0, self.review + delta))
        self.reviews_completed += 1
        self.last_updated = datetime.utcnow()

    def update_collaboration_reputation(self, delta: float, reason: str = "") -> None:
        """Update collaboration reputation with bounds checking."""
        self.collaboration = max(0.0, min(100.0, self.collaboration + delta))
        self.collaborations += 1
        self.last_updated = datetime.utcnow()

    def record_publication(self, impact_factor: float = 1.0) -> None:
        """Record a new publication and update research reputation."""
        self.papers_published += 1
        # Base increase plus bonus for high-impact publications
        delta = 2.0 + (impact_factor * 3.0)
        self.update_research_reputation(delta, "publication")

    def record_citation(self) -> None:
        """Record a citation to agent's work."""
        self.citation_count += 1
        # Small reputation boost for citations
        self.update_research_reputation(0.5, "citation")

    def update_h_index(self, new_h_index: int) -> None:
        """Update h-index and adjust research reputation accordingly."""
        if new_h_index > self.h_index:
            delta = (new_h_index - self.h_index) * 5.0
            self.h_index = new_h_index
            self.update_research_reputation(delta, "h_index_increase")

    def record_student_outcome(self, success: bool) -> None:
        """Record outcome of a student's learning journey."""
        total_students = self.teaching_sessions
        if total_students == 0:
            self.student_success_rate = 1.0 if success else 0.0
        else:
            # Update running average
            old_successes = self.student_success_rate * total_students
            new_successes = old_successes + (1.0 if success else 0.0)
            self.student_success_rate = new_successes / (total_students + 1)

        # Update teaching reputation based on outcome
        delta = 5.0 if success else -2.0
        self.update_teaching_reputation(delta, "student_outcome")

    def record_review_feedback(self, helpfulness_rating: float) -> None:
        """
        Record feedback on a review's helpfulness.

        Args:
            helpfulness_rating: 0-5 scale rating of review quality
        """
        if self.reviews_completed == 0:
            self.review_helpfulness = helpfulness_rating
        else:
            # Update running average
            total = self.review_helpfulness * self.reviews_completed
            self.review_helpfulness = (total + helpfulness_rating) / (self.reviews_completed + 1)

        # Update review reputation based on rating
        # Convert 0-5 rating to delta (-5 to +5)
        normalized_rating = (helpfulness_rating - 2.5) * 2
        self.update_review_reputation(normalized_rating, "review_feedback")

    def get_reputation_breakdown(self) -> dict[str, Any]:
        """Get detailed breakdown of reputation scores."""
        return {
            "overall": self.overall,
            "dimensions": {
                "teaching": self.teaching,
                "research": self.research,
                "review": self.review,
                "collaboration": self.collaboration,
            },
            "activity_counts": {
                "teaching_sessions": self.teaching_sessions,
                "papers_published": self.papers_published,
                "reviews_completed": self.reviews_completed,
                "collaborations": self.collaborations,
            },
            "impact_metrics": {
                "citation_count": self.citation_count,
                "h_index": self.h_index,
                "student_success_rate": self.student_success_rate,
                "review_helpfulness": self.review_helpfulness,
            },
            "last_updated": self.last_updated.isoformat(),
        }

    def compare_to(self, other: ReputationScore) -> dict[str, float]:
        """Compare this reputation to another agent's."""
        return {
            "overall_diff": self.overall - other.overall,
            "teaching_diff": self.teaching - other.teaching,
            "research_diff": self.research - other.research,
            "review_diff": self.review - other.review,
            "collaboration_diff": self.collaboration - other.collaboration,
        }

    def is_qualified_for(self, activity: str, threshold: float = 60.0) -> bool:
        """Check if agent is qualified for an activity based on reputation."""
        score_map = {
            "teaching": self.teaching,
            "research": self.research,
            "review": self.review,
            "collaboration": self.collaboration,
        }
        return score_map.get(activity, 0.0) >= threshold

    def __repr__(self) -> str:
        """String representation of reputation score."""
        return (
            f"ReputationScore(overall={self.overall:.1f}, "
            f"teaching={self.teaching:.1f}, research={self.research:.1f}, "
            f"review={self.review:.1f}, collaboration={self.collaboration:.1f})"
        )
