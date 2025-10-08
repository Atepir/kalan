"""
Mentor-student matchmaking system.

Uses knowledge graphs to find optimal mentor-student pairings
based on expertise, stage, and learning needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.core.agent import Agent, DevelopmentalStage
from src.orchestration.community import Community, get_community
from src.storage.graph_store import get_graph_store
from src.utils.logging import get_logger
from src.utils.metrics import record_metric

logger = get_logger(__name__)


@dataclass
class MentorshipMatch:
    """A potential mentor-student match."""

    mentor_id: UUID
    student_id: UUID
    compatibility_score: float
    shared_topics: list[str]
    mentor_expertise_level: int
    student_current_level: int
    reasoning: str


@dataclass
class MatchingCriteria:
    """Criteria for matching mentors with students."""

    topic: str | None = None
    min_expertise_gap: int = 1  # Minimum gap in knowledge depth
    max_expertise_gap: int = 3  # Maximum gap (avoid too large)
    require_specialization_match: bool = False
    min_mentor_reputation: float = 0.5


class Matchmaker:
    """
    Matches students with mentors based on knowledge and needs.

    Uses the knowledge graph to find mentors with relevant expertise
    and appropriate stage/reputation for teaching.
    """

    def __init__(self):
        """Initialize matchmaker."""
        self.community = get_community()
        self.graph_store = get_graph_store()
        self.logger = get_logger(__name__)

    async def find_mentor_for_student(
        self,
        student: Agent,
        topic: str,
        criteria: MatchingCriteria | None = None,
    ) -> MentorshipMatch | None:
        """
        Find the best mentor for a student on a specific topic.

        Args:
            student: The student agent
            topic: Topic the student needs help with
            criteria: Optional matching criteria

        Returns:
            Best mentor match if found
        """
        if criteria is None:
            criteria = MatchingCriteria(topic=topic)

        # Get all potential mentors (must be Teacher or higher)
        eligible_stages = [
            DevelopmentalStage.TEACHER,
            DevelopmentalStage.RESEARCHER,
            DevelopmentalStage.EXPERT,
        ]

        potential_mentors = []
        for stage in eligible_stages:
            mentors = await self.community.list_agents(stage=stage, active_only=True)
            potential_mentors.extend(mentors)

        if not potential_mentors:
            self.logger.info("no_potential_mentors_found")
            return None

        # Score each potential mentor
        matches = []
        for mentor in potential_mentors:
            match = await self._evaluate_mentor_match(
                mentor, student, topic, criteria
            )
            if match:
                matches.append(match)

        if not matches:
            self.logger.info(
                "no_suitable_mentors_found",
                student_id=str(student.id),
                topic=topic,
            )
            return None

        # Sort by compatibility score
        matches.sort(key=lambda m: m.compatibility_score, reverse=True)

        best_match = matches[0]

        self.logger.info(
            "mentor_match_found",
            student_id=str(student.id),
            mentor_id=str(best_match.mentor_id),
            topic=topic,
            score=best_match.compatibility_score,
        )

        record_metric(
            "matchmaking.mentor_found",
            1,
            {"student_stage": student.stage.value},
        )

        return best_match

    async def _evaluate_mentor_match(
        self,
        mentor: Agent,
        student: Agent,
        topic: str,
        criteria: MatchingCriteria,
    ) -> MentorshipMatch | None:
        """
        Evaluate how well a mentor matches a student's needs.

        Args:
            mentor: Potential mentor
            student: Student
            topic: Topic to learn
            criteria: Matching criteria

        Returns:
            Match evaluation or None if unsuitable
        """
        # Check reputation threshold
        if mentor.reputation.score < criteria.min_mentor_reputation:
            return None

        # Check specialization if required
        if criteria.require_specialization_match:
            if mentor.specialization != student.specialization:
                return None

        # Get mentor's knowledge of topic
        mentor_knowledge = mentor.knowledge.get_topic_knowledge(topic)
        mentor_depth = mentor_knowledge.depth if mentor_knowledge else 0

        # Get student's knowledge of topic
        student_knowledge = student.knowledge.get_topic_knowledge(topic)
        student_depth = student_knowledge.depth if student_knowledge else 0

        # Calculate expertise gap
        expertise_gap = mentor_depth - student_depth

        # Check if gap is appropriate
        if expertise_gap < criteria.min_expertise_gap:
            return None
        if expertise_gap > criteria.max_expertise_gap:
            return None

        # Find shared topics using knowledge graph
        shared_topics = await self._find_shared_topics(mentor.id, student.id)

        # Calculate compatibility score
        score = self._calculate_compatibility_score(
            mentor=mentor,
            student=student,
            expertise_gap=expertise_gap,
            shared_topics=shared_topics,
        )

        # Generate reasoning
        reasoning = (
            f"Mentor has depth {mentor_depth} on '{topic}' vs student's {student_depth}. "
            f"Expertise gap of {expertise_gap} is optimal for learning. "
            f"Reputation score: {mentor.reputation.score:.2f}. "
            f"Shared topics: {len(shared_topics)}."
        )

        return MentorshipMatch(
            mentor_id=mentor.id,
            student_id=student.id,
            compatibility_score=score,
            shared_topics=shared_topics,
            mentor_expertise_level=mentor_depth,
            student_current_level=student_depth,
            reasoning=reasoning,
        )

    async def _find_shared_topics(
        self, mentor_id: UUID, student_id: UUID
    ) -> list[str]:
        """
        Find topics that both mentor and student know.

        Args:
            mentor_id: Mentor agent ID
            student_id: Student agent ID

        Returns:
            List of shared topic names
        """
        # Query graph for concepts known by both agents
        query = """
        MATCH (mentor:Agent {id: $mentor_id})-[:KNOWS]->(c:Concept)<-[:KNOWS]-(student:Agent {id: $student_id})
        RETURN c.name as topic
        LIMIT 20
        """

        try:
            results = await self.graph_store.query(
                query,
                parameters={
                    "mentor_id": str(mentor_id),
                    "student_id": str(student_id),
                },
            )
            return [record["topic"] for record in results]
        except Exception as e:
            self.logger.error(
                "failed_to_find_shared_topics",
                mentor_id=str(mentor_id),
                student_id=str(student_id),
                error=str(e),
            )
            return []

    def _calculate_compatibility_score(
        self,
        mentor: Agent,
        student: Agent,
        expertise_gap: int,
        shared_topics: list[str],
    ) -> float:
        """
        Calculate compatibility score between mentor and student.

        Args:
            mentor: Mentor agent
            student: Student agent
            expertise_gap: Difference in knowledge depth
            shared_topics: Topics both know

        Returns:
            Compatibility score (0-1)
        """
        score = 0.0

        # Expertise gap score (ideal is 1-2 levels)
        if expertise_gap == 1:
            score += 0.4
        elif expertise_gap == 2:
            score += 0.3
        else:
            score += 0.2

        # Shared topics score
        shared_topic_score = min(len(shared_topics) * 0.05, 0.3)
        score += shared_topic_score

        # Reputation score (0-0.2 based on mentor reputation)
        reputation_score = min(mentor.reputation.score / 5.0, 0.2)
        score += reputation_score

        # Teaching experience score (from metrics)
        teaching_count = mentor.reputation.teaching_count
        teaching_score = min(teaching_count * 0.02, 0.1)
        score += teaching_score

        return min(score, 1.0)

    async def find_collaboration_partners(
        self,
        agent: Agent,
        topic: str,
        max_partners: int = 3,
    ) -> list[Agent]:
        """
        Find potential collaboration partners for research.

        Args:
            agent: The agent looking for collaborators
            topic: Research topic
            max_partners: Maximum number of partners to return

        Returns:
            List of potential partner agents
        """
        # Get agents at similar stages
        same_stage_agents = await self.community.list_agents(
            stage=agent.stage,
            active_only=True,
        )

        # Filter out the requesting agent
        candidates = [a for a in same_stage_agents if a.id != agent.id]

        if not candidates:
            return []

        # Score candidates based on topic knowledge
        scored_candidates = []
        for candidate in candidates:
            knowledge = candidate.knowledge.get_topic_knowledge(topic)
            depth = knowledge.depth if knowledge else 0

            # Prefer similar knowledge levels
            agent_knowledge = agent.knowledge.get_topic_knowledge(topic)
            agent_depth = agent_knowledge.depth if agent_knowledge else 0

            # Score higher for similar depth (collaboration works best between peers)
            depth_diff = abs(depth - agent_depth)
            score = max(0, 1.0 - (depth_diff * 0.2))

            # Boost score based on reputation
            score += candidate.reputation.score * 0.1

            scored_candidates.append((candidate, score))

        # Sort by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top partners
        partners = [c[0] for c in scored_candidates[:max_partners]]

        self.logger.info(
            "collaboration_partners_found",
            agent_id=str(agent.id),
            topic=topic,
            num_partners=len(partners),
        )

        return partners

    async def find_reviewers_for_paper(
        self,
        paper_id: str,
        topics: list[str],
        exclude_agent_ids: list[UUID] | None = None,
        num_reviewers: int = 3,
    ) -> list[Agent]:
        """
        Find suitable peer reviewers for a paper.

        Args:
            paper_id: Paper ID
            topics: Topics covered in the paper
            exclude_agent_ids: Agent IDs to exclude (e.g., authors)
            num_reviewers: Number of reviewers needed

        Returns:
            List of reviewer agents
        """
        if exclude_agent_ids is None:
            exclude_agent_ids = []

        # Get agents at Researcher or Expert stages
        researchers = await self.community.list_agents(
            stage=DevelopmentalStage.RESEARCHER,
            active_only=True,
        )
        experts = await self.community.list_agents(
            stage=DevelopmentalStage.EXPERT,
            active_only=True,
        )

        candidates = researchers + experts

        # Filter excluded agents
        candidates = [c for c in candidates if c.id not in exclude_agent_ids]

        if not candidates:
            self.logger.warning("no_reviewer_candidates_found", paper_id=paper_id)
            return []

        # Score candidates based on topic expertise
        scored_candidates = []
        for candidate in candidates:
            score = 0.0

            # Calculate average depth across all paper topics
            depths = []
            for topic in topics:
                knowledge = candidate.knowledge.get_topic_knowledge(topic)
                if knowledge:
                    depths.append(knowledge.depth)

            if depths:
                avg_depth = sum(depths) / len(depths)
                score += avg_depth * 0.4

            # Add reputation score
            score += candidate.reputation.score * 0.3

            # Boost for review experience
            score += min(candidate.reputation.review_count * 0.03, 0.3)

            scored_candidates.append((candidate, score))

        # Sort by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top reviewers
        reviewers = [c[0] for c in scored_candidates[:num_reviewers]]

        self.logger.info(
            "reviewers_found",
            paper_id=paper_id,
            num_reviewers=len(reviewers),
        )

        record_metric("matchmaking.reviewers_assigned", len(reviewers))

        return reviewers

    async def get_matchmaking_stats(self) -> dict[str, Any]:
        """
        Get matchmaking statistics.

        Returns:
            Statistics dictionary
        """
        # Get all active mentorships from graph
        query = """
        MATCH (mentor:Agent)-[r:MENTORS]->(student:Agent)
        RETURN count(r) as active_mentorships
        """

        try:
            results = await self.graph_store.query(query)
            active_mentorships = results[0]["active_mentorships"] if results else 0
        except Exception:
            active_mentorships = 0

        return {
            "active_mentorships": active_mentorships,
            # Add more stats as needed
        }
