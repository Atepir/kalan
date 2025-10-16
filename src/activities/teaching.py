"""
Teaching activities for agents.

This module implements teaching workflows including student assessment,
lesson creation, and feedback provision.
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


class StudentLevel(str, Enum):
    """Student knowledge level."""

    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class StudentAssessment:
    """Assessment of a student's knowledge."""

    student_id: str
    topic: str
    level: StudentLevel
    has_prerequisites: list[str]
    missing_prerequisites: list[str]
    starting_point: str
    recommended_pace: str  # slow, moderate, fast
    timestamp: datetime


@dataclass
class TeachingSession:
    """Record of a teaching session."""

    session_id: str
    teacher_id: str
    student_id: str
    topic: str
    explanation: str
    examples: list[str]
    exercises: list[str]
    student_questions: list[str]
    understanding_check: dict[str, any]
    duration_minutes: int
    timestamp: datetime


@dataclass
class FeedbackResult:
    """Feedback on student work."""

    what_correct: list[str]
    misconceptions: list[str]
    missing_points: list[str]
    understanding_score: float  # 0-100
    specific_feedback: str
    next_steps: list[str]


class TeachingActivity:
    """
    Manages teaching activities for agents.

    Handles student assessment, lesson creation, and providing feedback.
    """

    def __init__(self, agent: Agent):
        """
        Initialize teaching activity manager.

        Args:
            agent: The agent performing teaching activities
        """
        self.agent = agent
        self.llm = get_ollama_client()
        self.metrics = MetricsCollector()
        self.logger = get_logger(__name__, agent_id=str(agent.agent_id))

    async def assess_student(
        self,
        student: Agent,
        topic: str,
    ) -> StudentAssessment:
        """
        Assess a student's knowledge level and readiness.

        Args:
            student: The student to assess
            topic: Topic they want to learn

        Returns:
            Assessment of student's current level and needs
        """
        self.logger.info(
            "assessing_student",
            student_id=str(student.agent_id),
            topic=topic,
        )

        # Gather student background
        student_background = self._build_student_background(student)

        # Get student's questions about the topic
        student_questions = await self._get_student_questions(student, topic)

        # Generate assessment prompt
        prompt = PromptTemplates.assess_student_knowledge(
            student_background=student_background,
            topic=topic,
            student_questions=student_questions,
        )

        # Get LLM assessment
        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )

        assessment = self._parse_student_assessment(response, student, topic)

        self.logger.info(
            "student_assessment_complete",
            student_id=str(student.agent_id),
            level=assessment.level.value,
        )

        return assessment

    async def create_lesson(
        self,
        student: Agent,
        topic: str,
        student_level: StudentLevel,
        learning_goal: str,
    ) -> TeachingSession:
        """
        Create and deliver a teaching session.

        Args:
            student: The student to teach
            topic: Topic to teach
            student_level: Student's current level
            learning_goal: What the student should learn

        Returns:
            Record of the teaching session
        """
        start_time = datetime.utcnow()
        session_id = f"session_{int(start_time.timestamp())}"

        self.logger.info(
            "creating_lesson",
            session_id=session_id,
            student_id=str(student.agent_id),
            topic=topic,
        )

        # Generate explanation
        prompt = PromptTemplates.create_explanation(
            topic=topic,
            student_level=student_level.value,
            learning_goal=learning_goal,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.8,
        )

        # Parse lesson components
        explanation, examples, exercises = self._parse_lesson_content(response)

        # Simulate understanding check (in real system, student would respond)
        understanding_check = {
            "completed": True,
            "score": 0.75,  # Placeholder
        }

        duration = int((datetime.utcnow() - start_time).total_seconds() / 60)

        session = TeachingSession(
            session_id=session_id,
            teacher_id=str(self.agent.agent_id),
            student_id=str(student.agent_id),
            topic=topic,
            explanation=explanation,
            examples=examples,
            exercises=exercises,
            student_questions=[],
            understanding_check=understanding_check,
            duration_minutes=max(duration, 1),
            timestamp=datetime.utcnow(),
        )

        # Update teacher's reputation
        await self._record_teaching_session(session)

        # Track metrics
        self.metrics.track_activity(
            agent_id=str(self.agent.agent_id),
            activity_type="teaching",
            activity_name="create_lesson",
            outcome="success",
            details={
                "topic": topic,
                "student_level": student_level.value,
                "duration_minutes": session.duration_minutes,
            },
        )

        self.logger.info(
            "lesson_complete",
            session_id=session_id,
            duration_minutes=session.duration_minutes,
        )

        return session

    async def provide_feedback(
        self,
        student: Agent,
        concept: str,
        student_explanation: str,
    ) -> FeedbackResult:
        """
        Provide feedback on student's understanding.

        Args:
            student: The student
            concept: Concept being explained
            student_explanation: Student's explanation attempt

        Returns:
            Detailed feedback on their understanding
        """
        self.logger.info(
            "providing_feedback",
            student_id=str(student.agent_id),
            concept=concept,
        )

        prompt = PromptTemplates.verify_student_understanding(
            concept=concept,
            student_explanation=student_explanation,
        )

        response = await self.llm.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )

        feedback = self._parse_feedback(response)

        # Update reputation based on feedback quality
        self.agent.reputation.record_student_outcome(
            success=feedback.understanding_score > 70.0
        )

        self.logger.info(
            "feedback_provided",
            student_id=str(student.agent_id),
            understanding_score=feedback.understanding_score,
        )

        return feedback

    def _build_student_background(self, student: Agent) -> str:
        """Build description of student's background."""
        topics = list(student.knowledge.topics.keys())[:10]
        return f"""
Stage: {student.stage.value}
Known topics: {', '.join(topics) if topics else 'New to research'}
Learning goals: {', '.join(student.goals[:3]) if student.goals else 'Exploring'}
        """.strip()

    async def _get_student_questions(
        self, student: Agent, topic: str
    ) -> list[str]:
        """Get questions the student has about the topic."""
        # TODO: In real system, query student's recorded questions
        # For now, return generic questions based on their level
        return [
            f"What is {topic}?",
            f"Why is {topic} important?",
            f"How do I get started with {topic}?",
        ]

    def _parse_student_assessment(
        self,
        response: str,
        student: Agent,
        topic: str,
    ) -> StudentAssessment:
        """Parse LLM assessment response."""
        # Simple parsing - in production would be more sophisticated
        level = StudentLevel.BEGINNER

        if "novice" in response.lower():
            level = StudentLevel.NOVICE
        elif "advanced" in response.lower():
            level = StudentLevel.ADVANCED
        elif "intermediate" in response.lower():
            level = StudentLevel.INTERMEDIATE

        return StudentAssessment(
            student_id=str(student.agent_id),
            topic=topic,
            level=level,
            has_prerequisites=[],
            missing_prerequisites=[],
            starting_point="Begin with fundamentals",
            recommended_pace="moderate",
            timestamp=datetime.utcnow(),
        )

    def _parse_lesson_content(
        self, response: str
    ) -> tuple[str, list[str], list[str]]:
        """Parse lesson content from LLM response."""
        # Simple parsing - extract explanation, examples, exercises
        explanation = response
        examples = []
        exercises = []

        # TODO: More sophisticated parsing based on response structure
        return explanation, examples, exercises

    def _parse_feedback(self, response: str) -> FeedbackResult:
        """Parse feedback from LLM response."""
        # TODO: Parse structured feedback
        return FeedbackResult(
            what_correct=["Demonstrates basic understanding"],
            misconceptions=[],
            missing_points=["Could elaborate more on key concepts"],
            understanding_score=75.0,
            specific_feedback=response,
            next_steps=["Practice with more examples"],
        )

    async def _record_teaching_session(self, session: TeachingSession) -> None:
        """Record teaching session in database."""
        # TODO: Store in database
        # Update agent's experience and reputation
        pass


# Convenience functions

async def assess_student(
    teacher: Agent,
    student: Agent,
    topic: str,
) -> StudentAssessment:
    """
    Convenience function for assessing a student.

    Args:
        teacher: Teaching agent
        student: Student to assess
        topic: Topic to assess on

    Returns:
        Student assessment
    """
    activity = TeachingActivity(teacher)
    return await activity.assess_student(student, topic)


async def create_lesson(
    teacher: Agent,
    student: Agent,
    topic: str,
    student_level: StudentLevel,
    learning_goal: str,
) -> TeachingSession:
    """
    Convenience function for creating a lesson.

    Args:
        teacher: Teaching agent
        student: Student to teach
        topic: Topic to teach
        student_level: Student's level
        learning_goal: Learning objective

    Returns:
        Teaching session record
    """
    activity = TeachingActivity(teacher)
    return await activity.create_lesson(student, topic, student_level, learning_goal)


async def provide_feedback(
    teacher: Agent,
    student: Agent,
    concept: str,
    student_explanation: str,
) -> FeedbackResult:
    """
    Convenience function for providing feedback.

    Args:
        teacher: Teaching agent
        student: Student
        concept: Concept being explained
        student_explanation: Student's explanation

    Returns:
        Feedback result
    """
    activity = TeachingActivity(teacher)
    return await activity.provide_feedback(student, concept, student_explanation)
