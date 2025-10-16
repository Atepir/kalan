"""
Research activities for agents.

This module implements research workflows including literature review,
hypothesis generation, and experiment execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.llm import PromptTemplates, get_ollama_client
from src.storage.state_store import get_state_store
from src.utils.config import get_settings
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


@dataclass
class ResearchPaper:
    """A complete research paper."""

    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    introduction: str
    methodology: str
    results: str
    discussion: str
    conclusion: str
    references: list[str]
    keywords: list[str]
    timestamp: datetime
    experiment_ids: list[str]


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
        self.logger = get_logger(__name__, agent_id=str(agent.agent_id))

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

        # Extract content from response dict
        response_text = response if isinstance(response, str) else response.get("content", "")
        review = self._parse_literature_review(response_text, research_question, papers)

        # Track metrics
        self.metrics.track_activity(
            agent_id=str(self.agent.agent_id),
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

        # Extract content from response dict
        response_text = response if isinstance(response, str) else response.get("content", "")
        hypotheses = self._parse_hypotheses(response_text)

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
                agent_id=str(self.agent.agent_id),
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

    async def write_paper(
        self,
        title: str,
        research_question: str,
        literature_review: LiteratureReview,
        experiments: list[ExperimentResult],
        keywords: list[str] | None = None,
    ) -> ResearchPaper:
        """
        Write a research paper based on completed research.

        Args:
            title: Paper title
            research_question: Research question addressed
            literature_review: Literature review results
            experiments: List of experiments conducted
            keywords: Optional keywords

        Returns:
            Complete research paper
        """
        paper_id = f"paper_{self.agent.agent_id}_{int(datetime.utcnow().timestamp())}"
        
        self.logger.info(
            "writing_paper",
            paper_id=paper_id,
            title=title,
            num_experiments=len(experiments),
        )

        try:
            # Generate abstract
            abstract = await self._generate_abstract(
                title=title,
                research_question=research_question,
                experiments=experiments,
            )

            # Generate introduction
            introduction = await self._generate_introduction(
                research_question=research_question,
                literature_review=literature_review,
            )

            # Generate methodology section
            methodology = await self._generate_methodology(experiments)

            # Generate results section
            results = await self._generate_results(experiments)

            # Generate discussion
            discussion = await self._generate_discussion(
                research_question=research_question,
                experiments=experiments,
                literature_review=literature_review,
            )

            # Generate conclusion
            conclusion = await self._generate_conclusion(
                research_question=research_question,
                experiments=experiments,
            )

            # Compile references
            references = literature_review.papers_reviewed + [
                f"Experiment {exp.experiment_id}" for exp in experiments
            ]

            # Create paper
            paper = ResearchPaper(
                paper_id=paper_id,
                title=title,
                authors=[self.agent.name],
                abstract=abstract,
                introduction=introduction,
                methodology=methodology,
                results=results,
                discussion=discussion,
                conclusion=conclusion,
                references=references,
                keywords=keywords or ["machine learning", "research"],
                timestamp=datetime.utcnow(),
                experiment_ids=[exp.experiment_id for exp in experiments],
            )

            # Record paper authorship
            self.agent.papers_authored.append(paper_id)
            
            # Update agent's research reputation
            self.agent.reputation.record_publication(
                impact_factor=1.0,
            )

            # Add experience
            self.agent.add_experience(
                activity_type="research",
                description=f"Published paper: {title}",
                outcome="success",
                metadata={
                    "paper_id": paper_id,
                    "num_experiments": len(experiments),
                    "num_references": len(references),
                },
            )

            # Track metrics
            self.metrics.record_activity(
                activity_type="write_paper",
                duration_seconds=0.0,  # Not tracking duration for now
                success=True,
                agent_id=str(self.agent.agent_id),
                metadata={
                    "paper_id": paper_id,
                    "num_experiments": len(experiments),
                    "title": title,
                },
            )

            # Save paper to database and filesystem
            await self._save_paper_to_storage(paper)

            self.logger.info(
                "paper_written",
                paper_id=paper_id,
                title=title,
            )

            return paper

        except Exception as e:
            self.logger.error(
                "paper_writing_failed",
                paper_id=paper_id,
                error=str(e),
            )
            raise ValueError(f"Failed to write paper: {e}") from e

    async def _save_paper_to_storage(self, paper: ResearchPaper) -> None:
        """
        Save paper to both database and filesystem.

        Args:
            paper: Research paper to save
        """
        try:
            # Get configuration
            settings = get_settings()
            
            # Get state store singleton
            state_store = get_state_store()
            
            # Compile full paper content
            full_content = f"""# {paper.title}

**Authors:** {', '.join(paper.authors)}
**Keywords:** {', '.join(paper.keywords)}
**Date:** {paper.timestamp.strftime('%Y-%m-%d')}

## Abstract
{paper.abstract}

## Introduction
{paper.introduction}

## Methodology
{paper.methodology}

## Results
{paper.results}

## Discussion
{paper.discussion}

## Conclusion
{paper.conclusion}

## References
{chr(10).join(f'{i+1}. {ref}' for i, ref in enumerate(paper.references))}
"""
            
            # Save to database
            await state_store.save_paper(
                paper_id=paper.paper_id,
                title=paper.title,
                abstract=paper.abstract,
                content=full_content,
                metadata={
                    "authors": paper.authors,
                    "keywords": paper.keywords,
                    "timestamp": paper.timestamp.isoformat(),
                    "experiment_ids": paper.experiment_ids,
                },
            )
            
            # Save to filesystem
            papers_dir = settings.papers_dir
            papers_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as markdown
            paper_file = papers_dir / f"{paper.paper_id}.md"
            paper_file.write_text(full_content, encoding='utf-8')
            
            # Save as JSON for structured access
            paper_json_file = papers_dir / f"{paper.paper_id}.json"
            paper_data = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "introduction": paper.introduction,
                "methodology": paper.methodology,
                "results": paper.results,
                "discussion": paper.discussion,
                "conclusion": paper.conclusion,
                "references": paper.references,
                "keywords": paper.keywords,
                "timestamp": paper.timestamp.isoformat(),
                "experiment_ids": paper.experiment_ids,
            }
            paper_json_file.write_text(json.dumps(paper_data, indent=2), encoding='utf-8')
            
            self.logger.info(
                "paper_saved_to_storage",
                paper_id=paper.paper_id,
                markdown_path=str(paper_file),
                json_path=str(paper_json_file),
            )
            
        except Exception as e:
            self.logger.error(
                "paper_save_to_storage_failed",
                paper_id=paper.paper_id,
                error=str(e),
            )
            # Don't raise - paper creation succeeded, storage is secondary
            
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

    async def _generate_abstract(
        self,
        title: str,
        research_question: str,
        experiments: list[ExperimentResult],
    ) -> str:
        """Generate paper abstract."""
        # Summarize experiments
        exp_summary = " ".join([
            f"We conducted {len(experiments)} experiments to test our hypothesis."
        ])
        
        prompt = f"""Write a concise academic abstract (150-200 words) for a research paper titled "{title}".

Research Question: {research_question}

Experiments: {exp_summary}

The abstract should include:
1. Brief background and motivation
2. Research question and objectives
3. Methodology overview
4. Key findings
5. Implications

Write in a formal academic tone."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=300,
            temperature=0.7,
        )
        
        return response["content"].strip()

    async def _generate_introduction(
        self,
        research_question: str,
        literature_review: LiteratureReview,
    ) -> str:
        """Generate introduction section."""
        prompt = f"""Write an introduction section for a research paper.

Research Question: {research_question}

Literature Context:
- Current State: {literature_review.current_state}
- Key Methodologies: {', '.join(literature_review.key_methodologies[:3])}
- Literature Gaps: {', '.join(literature_review.literature_gaps[:3])}

The introduction should:
1. Establish the research context and importance
2. Review relevant prior work
3. Identify gaps in existing research
4. State the research question clearly
5. Outline the paper structure

Write 2-3 paragraphs in a formal academic tone."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        
        return response["content"].strip()

    async def _generate_methodology(
        self,
        experiments: list[ExperimentResult],
    ) -> str:
        """Generate methodology section."""
        methods = "\n".join([
            f"- Experiment {i+1}: {exp.methodology}"
            for i, exp in enumerate(experiments)
        ])
        
        prompt = f"""Write a methodology section describing the following experimental approaches:

{methods}

The methodology section should:
1. Describe the overall experimental design
2. Explain each methodology in detail
3. Justify the choice of methods
4. Describe data collection and analysis procedures

Write 2-3 paragraphs in a formal academic tone."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.7,
        )
        
        return response["content"].strip()

    async def _generate_results(
        self,
        experiments: list[ExperimentResult],
    ) -> str:
        """Generate results section."""
        results_summary = []
        for i, exp in enumerate(experiments):
            support = "supported" if exp.supports_hypothesis else "did not support"
            results_summary.append(
                f"Experiment {i+1} {support} the hypothesis (p < {exp.statistical_significance or 0.05})."
            )
        
        prompt = f"""Write a results section presenting the following experimental findings:

{' '.join(results_summary)}

For each experiment, provide:
1. Clear presentation of findings
2. Statistical analysis results
3. Key observations
4. Tables or figures descriptions (if applicable)

Write in a formal academic tone, presenting results objectively without interpretation."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=600,
            temperature=0.7,
        )
        
        return response["content"].strip()

    async def _generate_discussion(
        self,
        research_question: str,
        experiments: list[ExperimentResult],
        literature_review: LiteratureReview,
    ) -> str:
        """Generate discussion section."""
        findings = " ".join([exp.analysis[:200] for exp in experiments[:2]])
        
        prompt = f"""Write a discussion section for a research paper.

Research Question: {research_question}

Key Findings: {findings}

Literature Context: {literature_review.current_state}

The discussion should:
1. Interpret the results in context of the research question
2. Compare findings with prior work
3. Discuss implications and significance
4. Address limitations
5. Suggest future research directions

Write 2-3 paragraphs in a formal academic tone."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=700,
            temperature=0.7,
        )
        
        return response["content"].strip()

    async def _generate_conclusion(
        self,
        research_question: str,
        experiments: list[ExperimentResult],
    ) -> str:
        """Generate conclusion section."""
        prompt = f"""Write a conclusion section for a research paper.

Research Question: {research_question}

Number of Experiments: {len(experiments)}

The conclusion should:
1. Summarize the main findings
2. Restate how the research question was addressed
3. Highlight the contribution to the field
4. Provide closing thoughts

Write 1-2 paragraphs in a formal academic tone."""

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=400,
            temperature=0.7,
        )
        
        return response["content"].strip()

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


async def write_paper(
    agent: Agent,
    title: str,
    research_question: str,
    literature_review: LiteratureReview,
    experiments: list[ExperimentResult],
    keywords: list[str] | None = None,
) -> ResearchPaper:
    """
    Convenience function for writing a research paper.

    Args:
        agent: Agent writing the paper
        title: Paper title
        research_question: Research question addressed
        literature_review: Literature review results
        experiments: List of experiments conducted
        keywords: Optional keywords

    Returns:
        Complete research paper
    """
    activity = ResearchActivity(agent)
    return await activity.write_paper(
        title, research_question, literature_review, experiments, keywords
    )
