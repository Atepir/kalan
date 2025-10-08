"""
Research activities for agents.

This module implements research workflows including literature review,
hypothesis generation, and experiment execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from src.llm import PromptTemplates, get_ollama_client
from src.utils.logging import get_logger
from src.utils.metrics import MetricsCollector

if TYPE_CHECKING:
    from src.core.agent import Agent

logger = get_logger(__name__)


class HypothesisStatus(str, Enum):
    """Status of a research hypothesis."""

    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class ExperimentStatus(str, Enum):
    """Status of an experiment."""

    DESIGNED = "designed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LiteratureReview:
    """Result of literature review."""

    research_question: str
    papers_reviewed: list[str]
    current_state: str
    key_methodologies: list[str]
    major_findings: list[str]
    literature_gaps: list[str]
    contradictions: list[str]
    future_directions: list[str]
    timestamp: datetime


@dataclass
class HypothesisEvaluation:
    """Evaluation of a research hypothesis."""

    hypothesis: str
    rationale: str
    test_method: str
    required_resources: list[str]
    feasibility: str  # high, medium, low
    estimated_duration_weeks: int
    status: HypothesisStatus


@dataclass
class ExperimentResult:
    """Result of an experiment."""

    experiment_id: str
    hypothesis: str
    methodology: str
    results: dict[str, Any]
    analysis: str
    statistical_significance: float | None
    supports_hypothesis: bool
    limitations: list[str]
    implications: list[str]
    status: ExperimentStatus
    timestamp: datetime


class ResearchActivity:
    """
    Manages research activities for agents.

    Handles literature review, hypothesis generation, and experiment execution.
    """

    def __init__(self, agent: Agent):
        """
        Initialize research activity manager.

        Args:
            agent: The agent performing research activities
        """
        self.agent = agent
        self.llm = get_ollama_client()
        self.metrics = MetricsCollector()
        self.logger = get_logger(__name__, agent_id=str(agent.id))

    async def review_literature(
        self,
        research_question: str,
        papers: list[dict[str, str]],
    ) -> LiteratureReview:
        """
        Conduct a literature review.

        Args:
            research_question: The research question to explore
            papers: List of papers with 'title' and 'abstract' keys

        Returns:
            Literature review results
        """
        self.logger.info(
            "starting_literature_review",
            research_question=research_question,
            num_papers=len(papers),
        )

        prompt = PromptTemplates.literature_review(
            research_question=research_question,
            papers=papers,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        review = self._parse_literature_review(response, research_question, papers)

        # Track metrics
        self.metrics.track_activity(
            agent_id=str(self.agent.id),
            activity_type="research",
            activity_name="literature_review",
            outcome="success",
            details={
                "num_papers": len(papers),
                "num_gaps": len(review.literature_gaps),
            },
        )

        self.logger.info(
            "literature_review_complete",
            num_gaps=len(review.literature_gaps),
        )

        return review

    async def generate_hypothesis(
        self,
        research_area: str,
        background_knowledge: str,
        literature_gaps: list[str],
        num_hypotheses: int = 3,
    ) -> list[HypothesisEvaluation]:
        """
        Generate research hypotheses.

        Args:
            research_area: Area of research
            background_knowledge: Relevant background
            literature_gaps: Gaps identified in literature
            num_hypotheses: Number of hypotheses to generate

        Returns:
            List of evaluated hypotheses
        """
        self.logger.info(
            "generating_hypotheses",
            research_area=research_area,
            num_gaps=len(literature_gaps),
        )

        prompt = PromptTemplates.hypothesis_generation(
            research_area=research_area,
            background_knowledge=background_knowledge,
            literature_gaps=literature_gaps,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.8,
        )

        hypotheses = self._parse_hypotheses(response)

        self.logger.info(
            "hypotheses_generated",
            num_hypotheses=len(hypotheses),
        )

        return hypotheses[:num_hypotheses]

    async def conduct_experiment(
        self,
        hypothesis: str,
        methodology: str,
        code: str | None = None,
        available_resources: list[str] | None = None,
    ) -> ExperimentResult:
        """
        Execute a research experiment.

        Args:
            hypothesis: Hypothesis to test
            methodology: Experimental methodology
            code: Optional code to execute
            available_resources: Available resources/tools

        Returns:
            Experiment results and analysis
        """
        experiment_id = f"exp_{int(datetime.utcnow().timestamp())}"

        self.logger.info(
            "starting_experiment",
            experiment_id=experiment_id,
            hypothesis=hypothesis,
        )

        try:
            # If code provided, execute it
            results = {}
            if code:
                results = await self._execute_experiment_code(code)
            else:
                # Simulated results for design-only experiments
                results = {"status": "designed", "awaiting_execution": True}

            # Analyze results
            analysis_prompt = PromptTemplates.results_analysis(
                hypothesis=hypothesis,
                results=results,
                methodology=methodology,
            )

            analysis_response = await self.llm.generate(
                prompt=analysis_prompt,
                max_tokens=1500,
                temperature=0.7,
            )

            # Parse analysis
            analysis_data = self._parse_experiment_analysis(analysis_response)

            result = ExperimentResult(
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                methodology=methodology,
                results=results,
                analysis=analysis_data["summary"],
                statistical_significance=analysis_data.get("significance"),
                supports_hypothesis=analysis_data["supports_hypothesis"],
                limitations=analysis_data["limitations"],
                implications=analysis_data["implications"],
                status=ExperimentStatus.COMPLETED,
                timestamp=datetime.utcnow(),
            )

            # Update agent's research reputation
            self.agent.reputation.record_publication(
                citation_count=0,  # New experiment
                impact_factor=1.0,
            )

            # Track metrics
            self.metrics.track_activity(
                agent_id=str(self.agent.id),
                activity_type="research",
                activity_name="conduct_experiment",
                outcome="success",
                details={
                    "experiment_id": experiment_id,
                    "supports_hypothesis": result.supports_hypothesis,
                },
            )

            self.logger.info(
                "experiment_complete",
                experiment_id=experiment_id,
                supports_hypothesis=result.supports_hypothesis,
            )

            return result

        except Exception as e:
            self.logger.error(
                "experiment_failed",
                experiment_id=experiment_id,
                error=str(e),
            )

            return ExperimentResult(
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                methodology=methodology,
                results={"error": str(e)},
                analysis=f"Experiment failed: {e}",
                statistical_significance=None,
                supports_hypothesis=False,
                limitations=["Experiment execution failed"],
                implications=[],
                status=ExperimentStatus.FAILED,
                timestamp=datetime.utcnow(),
            )

    async def design_experiment(
        self,
        hypothesis: str,
        available_resources: list[str],
        constraints: list[str],
    ) -> dict[str, Any]:
        """
        Design an experiment without executing it.

        Args:
            hypothesis: Hypothesis to test
            available_resources: Available resources
            constraints: Experimental constraints

        Returns:
            Experiment design
        """
        self.logger.info(
            "designing_experiment",
            hypothesis=hypothesis,
        )

        prompt = PromptTemplates.experiment_design(
            hypothesis=hypothesis,
            available_resources=available_resources,
            constraints=constraints,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7,
        )

        design = self._parse_experiment_design(response)

        self.logger.info("experiment_design_complete")

        return design

    def _parse_literature_review(
        self,
        response: str,
        research_question: str,
        papers: list[dict[str, str]],
    ) -> LiteratureReview:
        """Parse literature review from LLM response."""
        # Simple parsing - production would be more sophisticated
        paper_ids = [p.get("id", p["title"]) for p in papers]

        return LiteratureReview(
            research_question=research_question,
            papers_reviewed=paper_ids,
            current_state="Active research area with multiple approaches",
            key_methodologies=["Various methodologies identified"],
            major_findings=["Multiple significant findings"],
            literature_gaps=["Gap 1", "Gap 2"],
            contradictions=[],
            future_directions=["Further research needed"],
            timestamp=datetime.utcnow(),
        )

    def _parse_hypotheses(self, response: str) -> list[HypothesisEvaluation]:
        """Parse hypotheses from LLM response."""
        # TODO: Parse structured hypothesis format from response
        # For now, return placeholder
        return [
            HypothesisEvaluation(
                hypothesis="Generated hypothesis based on gaps",
                rationale="Addresses identified gap in literature",
                test_method="Experimental validation",
                required_resources=["Computing resources", "Data"],
                feasibility="medium",
                estimated_duration_weeks=4,
                status=HypothesisStatus.PROPOSED,
            )
        ]

    async def _execute_experiment_code(self, code: str) -> dict[str, Any]:
        """Execute experiment code in sandbox."""
        # TODO: Integrate with experiment sandbox MCP server
        # For now, return simulated results
        return {
            "executed": True,
            "output": "Experiment completed successfully",
            "metrics": {"accuracy": 0.85, "f1_score": 0.82},
        }

    def _parse_experiment_analysis(self, response: str) -> dict[str, Any]:
        """Parse experiment analysis from LLM response."""
        # TODO: Parse structured analysis
        return {
            "summary": response[:500],
            "significance": 0.05,
            "supports_hypothesis": True,
            "limitations": ["Limited sample size"],
            "implications": ["Suggests further research"],
        }

    def _parse_experiment_design(self, response: str) -> dict[str, Any]:
        """Parse experiment design from LLM response."""
        return {
            "methodology": response,
            "variables": [],
            "controls": [],
            "data_collection": "To be specified",
            "analysis_plan": "Statistical analysis",
        }


# Convenience functions

async def review_literature(
    agent: Agent,
    research_question: str,
    papers: list[dict[str, str]],
) -> LiteratureReview:
    """
    Convenience function for literature review.

    Args:
        agent: Agent conducting review
        research_question: Research question
        papers: Papers to review

    Returns:
        Literature review results
    """
    activity = ResearchActivity(agent)
    return await activity.review_literature(research_question, papers)


async def generate_hypothesis(
    agent: Agent,
    research_area: str,
    background_knowledge: str,
    literature_gaps: list[str],
) -> list[HypothesisEvaluation]:
    """
    Convenience function for hypothesis generation.

    Args:
        agent: Agent generating hypotheses
        research_area: Research area
        background_knowledge: Background knowledge
        literature_gaps: Literature gaps

    Returns:
        List of hypotheses
    """
    activity = ResearchActivity(agent)
    return await activity.generate_hypothesis(
        research_area, background_knowledge, literature_gaps
    )


async def conduct_experiment(
    agent: Agent,
    hypothesis: str,
    methodology: str,
    code: str | None = None,
) -> ExperimentResult:
    """
    Convenience function for conducting experiments.

    Args:
        agent: Agent conducting experiment
        hypothesis: Hypothesis to test
        methodology: Experimental methodology
        code: Optional code to execute

    Returns:
        Experiment results
    """
    activity = ResearchActivity(agent)
    return await activity.conduct_experiment(hypothesis, methodology, code)
