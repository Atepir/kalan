"""
Stage progression and evolution logic.

This module defines the criteria and mechanisms for agents to progress through
developmental stages in the research collective.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.core.agent import AgentStage


@dataclass(frozen=True)
class PromotionCriteria:
    """Criteria required for promotion to the next stage."""

    current_stage: AgentStage
    next_stage: AgentStage
    min_papers_read: int
    min_knowledge_depth: float  # 0-1 scale
    min_confidence: float  # 0-1 scale
    min_students_taught: int
    min_publications: int
    min_reputation: float  # 0-100 scale
    min_time_in_stage_days: int
    requires_mentor_approval: bool

    @classmethod
    def get_criteria_for_stage(cls, stage: AgentStage) -> Optional[PromotionCriteria]:
        """Get promotion criteria for moving from the given stage to the next."""
        criteria_map = {
            AgentStage.APPRENTICE: cls(
                current_stage=AgentStage.APPRENTICE,
                next_stage=AgentStage.PRACTITIONER,
                min_papers_read=5,
                min_knowledge_depth=0.65,
                min_confidence=0.60,
                min_students_taught=0,
                min_publications=0,
                min_reputation=0.0,
                min_time_in_stage_days=7,
                requires_mentor_approval=True,
            ),
            AgentStage.PRACTITIONER: cls(
                current_stage=AgentStage.PRACTITIONER,
                next_stage=AgentStage.TEACHER,
                min_papers_read=15,
                min_knowledge_depth=0.75,
                min_confidence=0.70,
                min_students_taught=3,
                min_publications=0,
                min_reputation=55.0,
                min_time_in_stage_days=14,
                requires_mentor_approval=False,
            ),
            AgentStage.TEACHER: cls(
                current_stage=AgentStage.TEACHER,
                next_stage=AgentStage.RESEARCHER,
                min_papers_read=30,
                min_knowledge_depth=0.80,
                min_confidence=0.75,
                min_students_taught=5,
                min_publications=2,
                min_reputation=65.0,
                min_time_in_stage_days=21,
                requires_mentor_approval=False,
            ),
            AgentStage.RESEARCHER: cls(
                current_stage=AgentStage.RESEARCHER,
                next_stage=AgentStage.EXPERT,
                min_papers_read=50,
                min_knowledge_depth=0.85,
                min_confidence=0.80,
                min_students_taught=10,
                min_publications=10,
                min_reputation=80.0,
                min_time_in_stage_days=30,
                requires_mentor_approval=False,
            ),
        }
        return criteria_map.get(stage)


class PromotionEvaluation(BaseModel):
    """Result of evaluating an agent for promotion."""

    model_config = ConfigDict(frozen=True)

    agent_id: str
    current_stage: AgentStage
    next_stage: Optional[AgentStage]
    is_eligible: bool
    criteria_met: dict[str, bool]
    missing_requirements: list[str]
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    evaluator_notes: str = ""


class StagePromotion:
    """Service for evaluating and executing agent stage promotions."""

    @staticmethod
    def evaluate_promotion_eligibility(agent: Agent) -> PromotionEvaluation:  # type: ignore[name-defined]
        """
        Evaluate whether an agent is eligible for promotion.

        Args:
            agent: The agent to evaluate

        Returns:
            PromotionEvaluation with detailed results
        """
        from src.core.agent import Agent

        # Get criteria for current stage
        criteria = PromotionCriteria.get_criteria_for_stage(agent.stage)

        if criteria is None:
            # Agent is already at highest stage
            return PromotionEvaluation(
                agent_id=agent.agent_id,
                current_stage=agent.stage,
                next_stage=None,
                is_eligible=False,
                criteria_met={},
                missing_requirements=["Already at highest stage (Expert)"],
                evaluator_notes="Agent has reached the pinnacle of development.",
            )

        criteria_met: dict[str, bool] = {}
        missing: list[str] = []

        # Check each criterion
        # 1. Papers read
        papers_ok = len(agent.papers_read) >= criteria.min_papers_read
        criteria_met["papers_read"] = papers_ok
        if not papers_ok:
            missing.append(
                f"Read {criteria.min_papers_read - len(agent.papers_read)} more papers "
                f"(current: {len(agent.papers_read)}, required: {criteria.min_papers_read})"
            )

        # 2. Knowledge depth
        avg_depth = agent.knowledge.get_average_depth()
        depth_ok = avg_depth >= criteria.min_knowledge_depth
        criteria_met["knowledge_depth"] = depth_ok
        if not depth_ok:
            missing.append(
                f"Increase average knowledge depth to {criteria.min_knowledge_depth:.2f} "
                f"(current: {avg_depth:.2f})"
            )

        # 3. Confidence
        avg_confidence = agent.knowledge.get_average_confidence()
        confidence_ok = avg_confidence >= criteria.min_confidence
        criteria_met["confidence"] = confidence_ok
        if not confidence_ok:
            missing.append(
                f"Increase average confidence to {criteria.min_confidence:.2f} "
                f"(current: {avg_confidence:.2f})"
            )

        # 4. Students taught
        successful_students = sum(
            1 for s in agent.students if not s.is_active and s.student_progress >= 70.0
        )
        teaching_ok = successful_students >= criteria.min_students_taught
        criteria_met["students_taught"] = teaching_ok
        if not teaching_ok and criteria.min_students_taught > 0:
            missing.append(
                f"Successfully teach {criteria.min_students_taught - successful_students} more students "
                f"(current: {successful_students}, required: {criteria.min_students_taught})"
            )

        # 5. Publications
        pub_ok = len(agent.papers_authored) >= criteria.min_publications
        criteria_met["publications"] = pub_ok
        if not pub_ok and criteria.min_publications > 0:
            missing.append(
                f"Publish {criteria.min_publications - len(agent.papers_authored)} more papers "
                f"(current: {len(agent.papers_authored)}, required: {criteria.min_publications})"
            )

        # 6. Reputation
        rep_ok = agent.reputation.overall >= criteria.min_reputation
        criteria_met["reputation"] = rep_ok
        if not rep_ok and criteria.min_reputation > 0:
            missing.append(
                f"Increase overall reputation to {criteria.min_reputation:.1f} "
                f"(current: {agent.reputation.overall:.1f})"
            )

        # 7. Time in stage
        days_in_stage = (datetime.utcnow() - agent.created_at).days
        time_ok = days_in_stage >= criteria.min_time_in_stage_days
        criteria_met["time_in_stage"] = time_ok
        if not time_ok:
            missing.append(
                f"Wait {criteria.min_time_in_stage_days - days_in_stage} more days "
                f"(current: {days_in_stage}, required: {criteria.min_time_in_stage_days})"
            )

        # 8. Mentor approval (if required)
        if criteria.requires_mentor_approval:
            # Check if agent has an active mentor who can approve
            has_mentor = len(agent.get_active_mentors()) > 0
            criteria_met["mentor_approval"] = has_mentor
            if not has_mentor:
                missing.append("Obtain mentor approval for promotion")

        is_eligible = all(criteria_met.values())

        return PromotionEvaluation(
            agent_id=agent.agent_id,
            current_stage=agent.stage,
            next_stage=criteria.next_stage,
            is_eligible=is_eligible,
            criteria_met=criteria_met,
            missing_requirements=missing,
            evaluator_notes=(
                "All criteria met! Ready for promotion."
                if is_eligible
                else f"Missing {len(missing)} requirement(s) for promotion."
            ),
        )

    @staticmethod
    def execute_promotion(agent: Agent, evaluation: PromotionEvaluation) -> bool:  # type: ignore[name-defined]
        """
        Execute a promotion if eligible.

        Args:
            agent: The agent to promote
            evaluation: Previous evaluation result

        Returns:
            True if promotion was executed, False otherwise
        """
        if not evaluation.is_eligible or evaluation.next_stage is None:
            return False

        # Promote the agent
        agent.promote(evaluation.next_stage)

        # Log the promotion
        agent.add_experience(
            activity_type="promotion",
            description=f"Promoted from {evaluation.current_stage.value} to {evaluation.next_stage.value}",
            outcome="success",
            metadata={
                "previous_stage": evaluation.current_stage.value,
                "new_stage": evaluation.next_stage.value,
                "evaluation_timestamp": evaluation.evaluation_timestamp.isoformat(),
                "criteria_met": evaluation.criteria_met,
            },
        )

        return True

    @staticmethod
    def check_and_promote(agent: Agent) -> tuple[bool, PromotionEvaluation]:  # type: ignore[name-defined]
        """
        Convenience method to check eligibility and promote if ready.

        Args:
            agent: The agent to evaluate and potentially promote

        Returns:
            Tuple of (was_promoted, evaluation_result)
        """
        evaluation = StagePromotion.evaluate_promotion_eligibility(agent)
        was_promoted = StagePromotion.execute_promotion(agent, evaluation)
        return was_promoted, evaluation

    @staticmethod
    def get_promotion_progress(agent: Agent) -> dict[str, float]:  # type: ignore[name-defined]
        """
        Get progress towards promotion for each criterion (0-100 scale).

        Args:
            agent: The agent to evaluate

        Returns:
            Dictionary mapping criterion names to progress percentages
        """
        criteria = PromotionCriteria.get_criteria_for_stage(agent.stage)

        if criteria is None:
            return {}

        progress: dict[str, float] = {}

        # Papers read
        if criteria.min_papers_read > 0:
            progress["papers_read"] = min(
                100.0, (len(agent.papers_read) / criteria.min_papers_read) * 100
            )

        # Knowledge depth
        if criteria.min_knowledge_depth > 0:
            avg_depth = agent.knowledge.get_average_depth()
            progress["knowledge_depth"] = min(100.0, (avg_depth / criteria.min_knowledge_depth) * 100)

        # Confidence
        if criteria.min_confidence > 0:
            avg_confidence = agent.knowledge.get_average_confidence()
            progress["confidence"] = min(100.0, (avg_confidence / criteria.min_confidence) * 100)

        # Students taught
        if criteria.min_students_taught > 0:
            successful_students = sum(
                1 for s in agent.students if not s.is_active and s.student_progress >= 70.0
            )
            progress["students_taught"] = min(
                100.0, (successful_students / criteria.min_students_taught) * 100
            )

        # Publications
        if criteria.min_publications > 0:
            progress["publications"] = min(
                100.0, (len(agent.papers_authored) / criteria.min_publications) * 100
            )

        # Reputation
        if criteria.min_reputation > 0:
            progress["reputation"] = min(100.0, (agent.reputation.overall / criteria.min_reputation) * 100)

        # Time in stage
        days_in_stage = (datetime.utcnow() - agent.created_at).days
        progress["time_in_stage"] = min(
            100.0, (days_in_stage / criteria.min_time_in_stage_days) * 100
        )

        return progress
