"""
Learning activities for agents.

This module implements learning workflows including paper reading,
comprehension assessment, and mentor interaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from src.llm import LLMTools, PromptTemplates, get_ollama_client
from src.utils.logging import get_logger
from src.utils.metrics import MetricsCollector

if TYPE_CHECKING:
    from src.core.agent import Agent

logger = get_logger(__name__)


class ComprehensionLevel(str, Enum):
    """Level of comprehension after reading."""

    CONFUSED = "confused"  # <30% understanding
    PARTIAL = "partial"  # 30-60% understanding
    GOOD = "good"  # 60-85% understanding
    EXCELLENT = "excellent"  # >85% understanding


@dataclass
class PaperReadingResult:
    """Result of reading a paper."""

    paper_id: str
    paper_title: str
    summary: str
    key_concepts: list[str]
    questions: list[str]
    confidence: float  # 0-100
    comprehension_level: ComprehensionLevel
    reading_time_minutes: int
    timestamp: datetime


@dataclass
class MentorHelpRequest:
    """Request for mentor help."""

    topic: str
    question: str
    context: str
    current_understanding: str
    urgency: str  # low, medium, high


@dataclass
class MentorResponse:
    """Response from mentor."""

    explanation: str
    examples: list[str]
    additional_resources: list[str]
    follow_up_suggestions: list[str]
    timestamp: datetime


class LearningActivity:
    """
    Manages learning activities for agents.

    Handles paper reading, comprehension assessment, and mentor interactions.
    """

    def __init__(self, agent: Agent):
        """
        Initialize learning activity manager.

        Args:
            agent: The agent performing learning activities
        """
        self.agent = agent
        self.llm = get_ollama_client()
        self.metrics = MetricsCollector()
        self.logger = get_logger(__name__, agent_id=str(agent.agent_id))

    async def read_paper(
        self,
        paper_id: str,
        paper_title: str,
        paper_abstract: str,
        full_content: str | None = None,
    ) -> PaperReadingResult:
        """
        Read and comprehend a research paper.

        Args:
            paper_id: Unique identifier for the paper
            paper_title: Title of the paper
            paper_abstract: Abstract text
            full_content: Optional full paper content

        Returns:
            Result containing comprehension assessment

        Raises:
            ValueError: If paper cannot be processed
        """
        start_time = datetime.utcnow()
        self.logger.info(
            "starting_paper_reading",
            paper_id=paper_id,
            paper_title=paper_title,
        )

        try:
            # Build agent background context
            background = self._build_background_context()

            # Generate comprehension prompt
            prompt = PromptTemplates.paper_comprehension(
                paper_title=paper_title,
                paper_abstract=paper_abstract,
                agent_background=background,
            )

            # Get LLM analysis
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
            )

            # Parse response
            summary, concepts, questions, confidence = self._parse_comprehension_response(
                response
            )

            # Determine comprehension level
            comprehension_level = self._assess_comprehension_level(confidence)

            # Calculate reading time
            reading_time = int((datetime.utcnow() - start_time).total_seconds() / 60)

            result = PaperReadingResult(
                paper_id=paper_id,
                paper_title=paper_title,
                summary=summary,
                key_concepts=concepts,
                questions=questions,
                confidence=confidence,
                comprehension_level=comprehension_level,
                reading_time_minutes=max(reading_time, 1),
                timestamp=datetime.utcnow(),
            )

            # Update agent's knowledge
            await self._update_knowledge_from_paper(result)

            # Track metrics
            self.metrics.track_activity(
                agent_id=str(self.agent.agent_id),
                activity_type="learning",
                activity_name="read_paper",
                outcome="success",
                details={
                    "paper_id": paper_id,
                    "comprehension_level": comprehension_level.value,
                    "confidence": confidence,
                },
            )

            self.logger.info(
                "paper_reading_complete",
                paper_id=paper_id,
                comprehension_level=comprehension_level.value,
                confidence=confidence,
            )

            return result

        except Exception as e:
            self.logger.error(
                "paper_reading_failed",
                paper_id=paper_id,
                error=str(e),
            )
            self.metrics.track_activity(
                agent_id=str(self.agent.agent_id),
                activity_type="learning",
                activity_name="read_paper",
                outcome="error",
                details={"error": str(e)},
            )
            raise ValueError(f"Failed to read paper: {e}") from e

    async def assess_comprehension(
        self,
        topic: str,
        learning_materials: list[str],
        time_spent_hours: float,
    ) -> dict[str, any]:
        """
        Perform self-assessment after learning session.

        Args:
            topic: Topic studied
            learning_materials: List of materials used
            time_spent_hours: Total time spent learning

        Returns:
            Assessment results including mastery level and next steps
        """
        self.logger.info(
            "starting_self_assessment",
            topic=topic,
            time_spent_hours=time_spent_hours,
        )

        prompt = PromptTemplates.self_assessment(
            topic=topic,
            learning_materials=learning_materials,
            time_spent_hours=time_spent_hours,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )

        assessment = self._parse_self_assessment(response)

        self.logger.info(
            "self_assessment_complete",
            topic=topic,
            mastery=assessment.get("mastery", 0),
        )

        return assessment

    async def seek_mentor_help(
        self,
        topic: str,
        question: str,
        context: str = "",
        urgency: str = "medium",
    ) -> MentorResponse | None:
        """
        Request help from a mentor.

        Args:
            topic: Topic needing help with
            question: Specific question
            context: Additional context
            urgency: Priority level (low/medium/high)

        Returns:
            Mentor's response if mentor available, None otherwise
        """
        self.logger.info(
            "seeking_mentor_help",
            topic=topic,
            urgency=urgency,
        )

        # Get current understanding from knowledge graph
        current_understanding = self._get_topic_understanding(topic)

        # Create help request
        request = MentorHelpRequest(
            topic=topic,
            question=question,
            context=context,
            current_understanding=current_understanding,
            urgency=urgency,
        )

        # Find available mentor
        mentor = await self._find_available_mentor(topic)
        if not mentor:
            self.logger.warning(
                "no_mentor_available",
                topic=topic,
            )
            return None

        # Generate mentor explanation prompt
        prompt = PromptTemplates.concept_explanation_request(
            concept=topic,
            context=context,
            current_understanding=current_understanding,
        )

        # Get mentor's explanation (simulated via LLM for now)
        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1200,
            temperature=0.8,
        )

        mentor_response = self._parse_mentor_response(response)

        # Record mentorship interaction
        await self._record_mentorship_interaction(
            mentor=mentor,
            request=request,
            response=mentor_response,
        )

        self.logger.info(
            "mentor_help_received",
            topic=topic,
            mentor_id=str(mentor.agent_id),
        )

        return mentor_response

    def _build_background_context(self) -> str:
        """Build context about agent's background and knowledge."""
        topics = list(self.agent.knowledge.topics.keys())[:10]
        return f"""
Stage: {self.agent.stage.value}
Known topics: {', '.join(topics) if topics else 'No prior knowledge'}
Research interests: {', '.join(self.agent.goals[:3]) if self.agent.goals else 'Exploring'}
        """.strip()

    def _parse_comprehension_response(
        self, response: str
    ) -> tuple[str, list[str], list[str], float]:
        """Parse LLM response for comprehension assessment."""
        summary = ""
        concepts = []
        questions = []
        confidence = 50.0

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
                current_section = "summary"
            elif line.startswith("KEY CONCEPTS:"):
                concepts_str = line.replace("KEY CONCEPTS:", "").strip()
                concepts = [c.strip() for c in concepts_str.split(",")]
                current_section = "concepts"
            elif line.startswith("QUESTIONS:"):
                current_section = "questions"
            elif line.startswith("CONFIDENCE:"):
                conf_str = line.replace("CONFIDENCE:", "").strip().rstrip("%")
                try:
                    confidence = float(conf_str)
                except ValueError:
                    confidence = 50.0
                current_section = None
            elif current_section == "questions" and line and line[0].isdigit():
                # Question line like "1. What is..."
                question = line.split(".", 1)[-1].strip()
                if question:
                    questions.append(question)

        return summary, concepts, questions, confidence

    def _assess_comprehension_level(self, confidence: float) -> ComprehensionLevel:
        """Determine comprehension level from confidence score."""
        if confidence < 30:
            return ComprehensionLevel.CONFUSED
        elif confidence < 60:
            return ComprehensionLevel.PARTIAL
        elif confidence < 85:
            return ComprehensionLevel.GOOD
        else:
            return ComprehensionLevel.EXCELLENT

    async def _update_knowledge_from_paper(self, result: PaperReadingResult) -> None:
        """Update agent's knowledge graph based on paper reading."""
        for concept in result.key_concepts:
            # Normalize confidence to 0-1 scale
            confidence_delta = result.confidence / 100.0
            depth_delta = 0.1 * confidence_delta  # Modest depth increase

            self.agent.knowledge.update_topic_knowledge(
                topic=concept,
                depth_change=depth_delta,
                confidence_change=confidence_delta,
                source_type="paper",
                source_id=result.paper_id,
            )

    def _parse_self_assessment(self, response: str) -> dict[str, any]:
        """Parse self-assessment response."""
        return {
            "key_learnings": [],
            "unclear_concepts": [],
            "can_teach": False,
            "next_steps": [],
            "mastery": 50.0,
            "raw_response": response,
        }

    def _get_topic_understanding(self, topic: str) -> str:
        """Get agent's current understanding of a topic."""
        if topic in self.agent.knowledge.topics:
            topic_knowledge = self.agent.knowledge.topics[topic]
            return f"Depth: {topic_knowledge.depth:.2f}, Confidence: {topic_knowledge.confidence:.2f}"
        return "No prior knowledge of this topic"

    async def _find_available_mentor(self, topic: str) -> Agent | None:
        """Find an available mentor for the topic."""
        # TODO: Implement actual mentor matching via orchestration layer
        # For now, return None (will be implemented with matchmaking)
        return None

    def _parse_mentor_response(self, response: str) -> MentorResponse:
        """Parse mentor's explanation response."""
        return MentorResponse(
            explanation=response,
            examples=[],
            additional_resources=[],
            follow_up_suggestions=[],
            timestamp=datetime.utcnow(),
        )

    async def _record_mentorship_interaction(
        self,
        mentor: Agent,
        request: MentorHelpRequest,
        response: MentorResponse,
    ) -> None:
        """Record mentorship interaction for both parties."""
        # TODO: Store in database and update experience logs
        pass


# Convenience functions for external use

async def read_paper(
    agent: Agent,
    paper_id: str,
    paper_title: str,
    paper_abstract: str,
) -> PaperReadingResult:
    """
    Convenience function for reading a paper.

    Args:
        agent: Agent reading the paper
        paper_id: Paper identifier
        paper_title: Paper title
        paper_abstract: Paper abstract

    Returns:
        Reading result with comprehension assessment
    """
    activity = LearningActivity(agent)
    return await activity.read_paper(paper_id, paper_title, paper_abstract)


async def assess_comprehension(
    agent: Agent,
    topic: str,
    learning_materials: list[str],
    time_spent_hours: float,
) -> dict[str, any]:
    """
    Convenience function for self-assessment.

    Args:
        agent: Agent performing assessment
        topic: Topic studied
        learning_materials: Materials used
        time_spent_hours: Time spent learning

    Returns:
        Assessment results
    """
    activity = LearningActivity(agent)
    return await activity.assess_comprehension(topic, learning_materials, time_spent_hours)


async def seek_mentor_help(
    agent: Agent,
    topic: str,
    question: str,
    context: str = "",
) -> MentorResponse | None:
    """
    Convenience function for seeking mentor help.

    Args:
        agent: Agent seeking help
        topic: Topic needing help with
        question: Specific question
        context: Additional context

    Returns:
        Mentor response if available
    """
    activity = LearningActivity(agent)
    return await activity.seek_mentor_help(topic, question, context)
