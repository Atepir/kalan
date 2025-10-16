"""
Peer review activities for agents.

This module implements peer review workflows including paper evaluation,
revision suggestions, and review quality assessment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from src.llm import PromptTemplates, get_ollama_client
from src.utils.logging import get_logger
from src.utils.metrics import MetricsCollector

if TYPE_CHECKING:
    from src.core.agent import Agent

logger = get_logger(__name__)


class ReviewDecision(str, Enum):
    """Final review decision."""

    ACCEPT = "accept"
    MINOR_REVISION = "minor_revision"
    MAJOR_REVISION = "major_revision"
    REJECT = "reject"


class ReviewQuality(str, Enum):
    """Quality rating for a review."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"


@dataclass
class ReviewRecommendation:
    """Recommendation from a review."""

    decision: ReviewDecision
    confidence: float  # 0-1
    reasoning: str


@dataclass
class PeerReview:
    """Complete peer review of a paper."""

    review_id: str
    reviewer_id: str
    paper_id: str
    paper_title: str

    # Review dimensions (0-10 scale)
    novelty_score: float
    methodology_score: float
    results_score: float
    clarity_score: float
    contribution_score: float

    # Qualitative assessment
    strengths: list[str]
    weaknesses: list[str]
    detailed_comments: str
    revision_suggestions: list[str]

    # Final recommendation
    recommendation: ReviewRecommendation

    # Meta
    review_time_minutes: int
    timestamp: datetime


@dataclass
class RevisionSuggestion:
    """Specific suggestion for paper revision."""

    section: str
    issue: str
    suggested_change: str
    priority: str  # high, medium, low
    example_text: str | None = None


class ReviewActivity:
    """
    Manages peer review activities for agents.

    Handles paper evaluation, revision suggestions, and review quality.
    """

    def __init__(self, agent: Agent):
        """
        Initialize review activity manager.

        Args:
            agent: The agent performing review activities
        """
        self.agent = agent
        self.llm = get_ollama_client()
        self.metrics = MetricsCollector()
        self.logger = get_logger(__name__, agent_id=str(agent.agent_id))

    async def review_paper(
        self,
        paper_id: str,
        paper_title: str,
        paper_abstract: str,
        paper_content: str,
        review_criteria: dict[str, str] | None = None,
    ) -> PeerReview:
        """
        Conduct a peer review of a paper.

        Args:
            paper_id: Paper identifier
            paper_title: Paper title
            paper_abstract: Paper abstract
            paper_content: Full paper content
            review_criteria: Optional custom criteria

        Returns:
            Complete peer review
        """
        start_time = datetime.utcnow()
        review_id = f"review_{int(start_time.timestamp())}"

        self.logger.info(
            "starting_peer_review",
            review_id=review_id,
            paper_id=paper_id,
        )

        # Default criteria
        if review_criteria is None:
            review_criteria = {
                "novelty": "Is the work original and significant?",
                "methodology": "Are the methods sound?",
                "results": "Are findings well-supported?",
                "clarity": "Is the writing clear?",
                "contribution": "What is the impact?",
            }

        try:
            # Generate review prompt
            prompt = PromptTemplates.paper_review(
                paper_title=paper_title,
                paper_abstract=paper_abstract,
                paper_content=paper_content,
                review_criteria=review_criteria,
            )

            # Get comprehensive review
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
            )

            # Extract content from response dict
            response_text = response if isinstance(response, str) else response.get("content", "")
            
            # Parse review components
            review_data = self._parse_review_response(response_text)

            # Generate revision suggestions
            suggestions = await self._generate_revision_suggestions(
                paper_content, review_data["weaknesses"]
            )

            # Calculate review time
            review_time = int((datetime.utcnow() - start_time).total_seconds() / 60)

            review = PeerReview(
                review_id=review_id,
                reviewer_id=str(self.agent.agent_id),
                paper_id=paper_id,
                paper_title=paper_title,
                novelty_score=review_data["novelty_score"],
                methodology_score=review_data["methodology_score"],
                results_score=review_data["results_score"],
                clarity_score=review_data["clarity_score"],
                contribution_score=review_data["contribution_score"],
                strengths=review_data["strengths"],
                weaknesses=review_data["weaknesses"],
                detailed_comments=review_data["comments"],
                revision_suggestions=[s.suggested_change for s in suggestions],
                recommendation=review_data["recommendation"],
                review_time_minutes=max(review_time, 1),
                timestamp=datetime.utcnow(),
            )

            # Update reviewer's reputation
            self.agent.reputation.update_review_reputation(
                delta=3.0,  # Positive reputation for completing a review
                reason="completed_review"
            )
            self.agent.reputation.record_review_feedback(
                helpfulness_rating=0.8  # TODO: Get from meta-review
            )

            # Track metrics
            self.metrics.track_activity(
                agent_id=str(self.agent.agent_id),
                activity_type="review",
                activity_name="review_paper",
                outcome="success",
                details={
                    "paper_id": paper_id,
                    "decision": review.recommendation.decision.value,
                    "review_time_minutes": review_time,
                },
            )

            self.logger.info(
                "peer_review_complete",
                review_id=review_id,
                decision=review.recommendation.decision.value,
            )

            return review

        except Exception as e:
            self.logger.error(
                "peer_review_failed",
                review_id=review_id,
                error=str(e),
            )
            raise ValueError(f"Failed to complete review: {e}") from e

    async def suggest_revisions(
        self,
        paper_section: str,
        identified_issues: list[str],
    ) -> list[RevisionSuggestion]:
        """
        Generate specific revision suggestions.

        Args:
            paper_section: Section of paper needing revision
            identified_issues: Issues to address

        Returns:
            List of revision suggestions
        """
        self.logger.info(
            "generating_revision_suggestions",
            num_issues=len(identified_issues),
        )

        prompt = PromptTemplates.revision_suggestions(
            paper_section=paper_section,
            identified_issues=identified_issues,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1200,
            temperature=0.7,
        )

        suggestions = self._parse_revision_suggestions(response)

        self.logger.info(
            "revision_suggestions_generated",
            num_suggestions=len(suggestions),
        )

        return suggestions

    async def assess_review_quality(
        self,
        review: PeerReview,
    ) -> ReviewQuality:
        """
        Assess the quality of a review (meta-review).

        Args:
            review: Review to assess

        Returns:
            Quality rating
        """
        self.logger.info(
            "assessing_review_quality",
            review_id=review.review_id,
        )

        # Criteria for good reviews
        has_detailed_comments = len(review.detailed_comments) > 200
        has_specific_weaknesses = len(review.weaknesses) >= 2
        has_actionable_suggestions = len(review.revision_suggestions) >= 2
        balanced_scores = (
            max([
                review.novelty_score,
                review.methodology_score,
                review.results_score,
                review.clarity_score,
                review.contribution_score,
            ])
            - min([
                review.novelty_score,
                review.methodology_score,
                review.results_score,
                review.clarity_score,
                review.contribution_score,
            ])
        ) < 5.0  # Scores not too disparate

        quality_score = sum([
            has_detailed_comments,
            has_specific_weaknesses,
            has_actionable_suggestions,
            balanced_scores,
        ])

        if quality_score >= 4:
            quality = ReviewQuality.EXCELLENT
        elif quality_score == 3:
            quality = ReviewQuality.GOOD
        elif quality_score == 2:
            quality = ReviewQuality.ADEQUATE
        else:
            quality = ReviewQuality.POOR

        self.logger.info(
            "review_quality_assessed",
            review_id=review.review_id,
            quality=quality.value,
        )

        return quality

    def _parse_review_response(self, response: str) -> dict:
        """Parse structured review from LLM response."""
        # TODO: More sophisticated parsing
        # For now, extract basic components

        lines = response.split("\n")
        strengths = []
        weaknesses = []

        for line in lines:
            line = line.strip()
            if "strength" in line.lower() and ":" in line:
                strength = line.split(":", 1)[-1].strip()
                if strength:
                    strengths.append(strength)
            elif "weakness" in line.lower() and ":" in line:
                weakness = line.split(":", 1)[-1].strip()
                if weakness:
                    weaknesses.append(weakness)

        # Default scores if not parsed
        decision = ReviewDecision.MINOR_REVISION
        if "reject" in response.lower():
            decision = ReviewDecision.REJECT
        elif "accept" in response.lower():
            decision = ReviewDecision.ACCEPT

        return {
            "novelty_score": 7.0,
            "methodology_score": 7.5,
            "results_score": 7.0,
            "clarity_score": 8.0,
            "contribution_score": 7.0,
            "strengths": strengths if strengths else ["Paper addresses relevant topic"],
            "weaknesses": weaknesses if weaknesses else ["Could improve clarity"],
            "comments": response,
            "recommendation": ReviewRecommendation(
                decision=decision,
                confidence=0.75,
                reasoning="Based on overall assessment",
            ),
        }

    async def _generate_revision_suggestions(
        self,
        paper_content: str,
        weaknesses: list[str],
    ) -> list[RevisionSuggestion]:
        """Generate revision suggestions for identified weaknesses."""
        if not weaknesses:
            return []

        # Take first section of paper as sample
        paper_section = paper_content[:1000]

        suggestions_list = await self.suggest_revisions(paper_section, weaknesses)

        return suggestions_list

    def _parse_revision_suggestions(self, response: str) -> list[RevisionSuggestion]:
        """Parse revision suggestions from LLM response."""
        # TODO: More sophisticated parsing
        suggestions = []

        # Simple parsing - each numbered item is a suggestion
        lines = response.split("\n")
        current_suggestion = None

        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                if current_suggestion:
                    suggestions.append(current_suggestion)
                issue = line.split(".", 1)[-1].strip()
                current_suggestion = RevisionSuggestion(
                    section="general",
                    issue=issue,
                    suggested_change=issue,
                    priority="medium",
                )

        if current_suggestion:
            suggestions.append(current_suggestion)

        return suggestions if suggestions else [
            RevisionSuggestion(
                section="general",
                issue="General improvements needed",
                suggested_change="See detailed comments",
                priority="medium",
            )
        ]


# Convenience functions

async def review_paper(
    reviewer: Agent,
    paper_id: str,
    paper_title: str,
    paper_abstract: str,
    paper_content: str,
) -> PeerReview:
    """
    Convenience function for reviewing a paper.

    Args:
        reviewer: Reviewing agent
        paper_id: Paper identifier
        paper_title: Paper title
        paper_abstract: Paper abstract
        paper_content: Paper content

    Returns:
        Complete peer review
    """
    activity = ReviewActivity(reviewer)
    return await activity.review_paper(
        paper_id, paper_title, paper_abstract, paper_content
    )
