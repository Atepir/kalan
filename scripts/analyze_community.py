"""
Analyze community dynamics and generate reports.

Provides insights into agent development, knowledge diffusion,
collaboration patterns, and community health metrics.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.orchestration.community import get_community
from src.orchestration.events import EventType, get_event_bus
from src.storage.graph_store import get_graph_store
from src.storage.state_store import get_state_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CommunityAnalyzer:
    """Analyzes community dynamics and generates reports."""

    def __init__(self):
        """Initialize analyzer."""
        self.community = get_community()
        self.event_bus = get_event_bus()
        self.graph_store = get_graph_store()
        self.state_store = get_state_store()
        self.logger = get_logger(__name__)

    async def analyze_agent_progression(self) -> dict[str, Any]:
        """
        Analyze agent progression through developmental stages.

        Returns:
            Progression statistics
        """
        self.logger.info("analyzing_agent_progression")

        # Get promotion events
        promotion_events = self.event_bus.get_event_history(
            event_type=EventType.AGENT_PROMOTED,
            limit=1000,
        )

        # Count promotions by stage transition
        transitions: dict[str, int] = {}
        for event in promotion_events:
            old_stage = event.data.get("old_stage")
            new_stage = event.data.get("new_stage")
            key = f"{old_stage} → {new_stage}"
            transitions[key] = transitions.get(key, 0) + 1

        # Get current distribution
        community_stats = await self.community.get_community_stats()
        stage_distribution = community_stats["agents_by_stage"]

        return {
            "total_promotions": len(promotion_events),
            "transitions": transitions,
            "current_distribution": stage_distribution,
        }

    async def analyze_learning_patterns(self) -> dict[str, Any]:
        """
        Analyze learning patterns across the community.

        Returns:
            Learning statistics
        """
        self.logger.info("analyzing_learning_patterns")

        # Get paper reading events
        paper_events = self.event_bus.get_event_history(
            event_type=EventType.PAPER_READ,
            limit=1000,
        )

        # Count by comprehension level
        comprehension_levels: dict[str, int] = {}
        for event in paper_events:
            level = event.data.get("comprehension_level", "unknown")
            comprehension_levels[level] = comprehension_levels.get(level, 0) + 1

        # Get help request events
        help_events = self.event_bus.get_event_history(
            event_type=EventType.HELP_REQUESTED,
            limit=1000,
        )

        # Count unique learners
        unique_learners = set(e.source_agent_id for e in paper_events)

        return {
            "total_papers_read": len(paper_events),
            "comprehension_distribution": comprehension_levels,
            "help_requests": len(help_events),
            "active_learners": len(unique_learners),
            "help_rate": len(help_events) / len(paper_events)
            if paper_events
            else 0,
        }

    async def analyze_mentorship_network(self) -> dict[str, Any]:
        """
        Analyze mentorship relationships and effectiveness.

        Returns:
            Mentorship statistics
        """
        self.logger.info("analyzing_mentorship_network")

        # Query mentorship relationships from graph
        query = """
        MATCH (mentor:Agent)-[r:MENTORS]->(student:Agent)
        RETURN mentor.id as mentor_id, 
               mentor.name as mentor_name,
               student.id as student_id,
               student.name as student_name,
               r.sessions as sessions
        """

        try:
            mentorships = await self.graph_store.query(query)
        except Exception as e:
            self.logger.error("failed_to_query_mentorships", error=str(e))
            mentorships = []

        # Count mentors and students
        mentors = set(m["mentor_id"] for m in mentorships)
        students = set(m["student_id"] for m in mentorships)

        # Count total sessions
        total_sessions = sum(m.get("sessions", 0) for m in mentorships)

        # Get teaching events
        teaching_events = self.event_bus.get_event_history(
            event_type=EventType.TEACHING_SESSION_COMPLETED,
            limit=1000,
        )

        return {
            "active_mentorships": len(mentorships),
            "unique_mentors": len(mentors),
            "unique_students": len(students),
            "total_sessions": total_sessions,
            "recent_teaching_events": len(teaching_events),
        }

    async def analyze_research_productivity(self) -> dict[str, Any]:
        """
        Analyze research productivity and impact.

        Returns:
            Research statistics
        """
        self.logger.info("analyzing_research_productivity")

        # Get experiment events
        experiment_events = self.event_bus.get_event_history(
            event_type=EventType.EXPERIMENT_COMPLETED,
            limit=1000,
        )

        # Count successful vs failed
        successful = sum(
            1 for e in experiment_events if e.data.get("success", False)
        )
        failed = len(experiment_events) - successful

        # Get paper submission events
        paper_events = self.event_bus.get_event_history(
            event_type=EventType.PAPER_SUBMITTED,
            limit=1000,
        )

        # Get review events
        review_events = self.event_bus.get_event_history(
            event_type=EventType.REVIEW_SUBMITTED,
            limit=1000,
        )

        # Count unique researchers
        unique_researchers = set(e.source_agent_id for e in experiment_events)

        return {
            "total_experiments": len(experiment_events),
            "successful_experiments": successful,
            "failed_experiments": failed,
            "success_rate": successful / len(experiment_events)
            if experiment_events
            else 0,
            "papers_submitted": len(paper_events),
            "reviews_submitted": len(review_events),
            "active_researchers": len(unique_researchers),
        }

    async def analyze_collaboration_patterns(self) -> dict[str, Any]:
        """
        Analyze collaboration patterns and networks.

        Returns:
            Collaboration statistics
        """
        self.logger.info("analyzing_collaboration_patterns")

        # Get collaboration events
        proposed = self.event_bus.get_event_history(
            event_type=EventType.COLLABORATION_PROPOSED,
            limit=1000,
        )

        accepted = self.event_bus.get_event_history(
            event_type=EventType.COLLABORATION_ACCEPTED,
            limit=1000,
        )

        completed = self.event_bus.get_event_history(
            event_type=EventType.COLLABORATION_COMPLETED,
            limit=1000,
        )

        # Query collaboration graph
        query = """
        MATCH (a1:Agent)-[r:COLLABORATED_WITH]->(a2:Agent)
        RETURN count(r) as total_collaborations,
               count(DISTINCT a1.id) as unique_collaborators
        """

        try:
            results = await self.graph_store.query(query)
            graph_stats = results[0] if results else {}
        except Exception as e:
            self.logger.error("failed_to_query_collaborations", error=str(e))
            graph_stats = {}

        return {
            "proposed": len(proposed),
            "accepted": len(accepted),
            "completed": len(completed),
            "acceptance_rate": len(accepted) / len(proposed) if proposed else 0,
            "completion_rate": len(completed) / len(accepted) if accepted else 0,
            "total_collaborations": graph_stats.get("total_collaborations", 0),
            "unique_collaborators": graph_stats.get("unique_collaborators", 0),
        }

    async def analyze_knowledge_diffusion(self) -> dict[str, Any]:
        """
        Analyze how knowledge spreads through the community.

        Returns:
            Knowledge diffusion statistics
        """
        self.logger.info("analyzing_knowledge_diffusion")

        # Get concept learning events
        concept_events = self.event_bus.get_event_history(
            event_type=EventType.CONCEPT_LEARNED,
            limit=1000,
        )

        # Count concepts learned
        concepts_learned: dict[str, int] = {}
        for event in concept_events:
            concept = event.data.get("concept", "unknown")
            concepts_learned[concept] = concepts_learned.get(concept, 0) + 1

        # Query knowledge graph for most connected concepts
        query = """
        MATCH (c:Concept)<-[:KNOWS]-(a:Agent)
        RETURN c.name as concept, count(a) as agent_count
        ORDER BY agent_count DESC
        LIMIT 10
        """

        try:
            popular_concepts = await self.graph_store.query(query)
        except Exception as e:
            self.logger.error("failed_to_query_popular_concepts", error=str(e))
            popular_concepts = []

        # Query for knowledge depth distribution
        query = """
        MATCH (a:Agent)-[k:KNOWS]->(c:Concept)
        RETURN k.depth as depth, count(*) as count
        ORDER BY depth
        """

        try:
            depth_distribution = await self.graph_store.query(query)
        except Exception as e:
            self.logger.error("failed_to_query_depth_distribution", error=str(e))
            depth_distribution = []

        return {
            "total_learning_events": len(concept_events),
            "unique_concepts_learned": len(concepts_learned),
            "most_learned_concepts": dict(
                sorted(
                    concepts_learned.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ),
            "popular_concepts": [
                {"concept": r["concept"], "agents": r["agent_count"]}
                for r in popular_concepts
            ],
            "depth_distribution": [
                {"depth": r["depth"], "count": r["count"]}
                for r in depth_distribution
            ],
        }

    async def analyze_community_health(self) -> dict[str, Any]:
        """
        Analyze overall community health metrics.

        Returns:
            Health metrics
        """
        self.logger.info("analyzing_community_health")

        # Get community stats
        community_stats = await self.community.get_community_stats()

        # Calculate activity rate (events per agent)
        event_stats = self.event_bus.get_statistics()
        total_events = event_stats["total_events"]
        total_agents = community_stats["total_agents"]
        activity_rate = total_events / total_agents if total_agents > 0 else 0

        # Get agent statuses to check for inactive agents
        agents = await self.community.list_agents(active_only=True)
        inactive_agents = []

        for agent in agents:
            from uuid import UUID
            status = await self.community.get_agent_status(UUID(agent.agent_id))
            if status:
                # Check if agent has been inactive for too long
                inactivity = datetime.utcnow() - status.last_activity
                if inactivity > timedelta(hours=1):
                    inactive_agents.append(agent.agent_id)

        # Calculate diversity (by specialization)
        specializations = community_stats["agents_by_specialization"]
        diversity_score = len(specializations) / total_agents if total_agents > 0 else 0

        return {
            "total_agents": total_agents,
            "active_agents": community_stats["active_agents"],
            "average_reputation": community_stats["avg_reputation"],
            "activity_rate": activity_rate,
            "inactive_agents": len(inactive_agents),
            "specialization_diversity": diversity_score,
            "num_specializations": len(specializations),
        }

    async def generate_report(self, output_path: Path | None = None) -> str:
        """
        Generate comprehensive community analysis report.

        Args:
            output_path: Optional path to save report

        Returns:
            Report text
        """
        self.logger.info("generating_community_report")

        # Run all analyses
        progression = await self.analyze_agent_progression()
        learning = await self.analyze_learning_patterns()
        mentorship = await self.analyze_mentorship_network()
        research = await self.analyze_research_productivity()
        collaboration = await self.analyze_collaboration_patterns()
        knowledge = await self.analyze_knowledge_diffusion()
        health = await self.analyze_community_health()

        # Build report
        report_lines = [
            "=" * 80,
            "RESEARCH COLLECTIVE - COMMUNITY ANALYSIS REPORT",
            f"Generated: {datetime.utcnow().isoformat()}",
            "=" * 80,
            "",
            "## COMMUNITY HEALTH",
            f"Total Agents: {health['total_agents']}",
            f"Active Agents: {health['active_agents']}",
            f"Average Reputation: {health['average_reputation']:.2f}",
            f"Activity Rate: {health['activity_rate']:.2f} events/agent",
            f"Inactive Agents: {health['inactive_agents']}",
            f"Specialization Diversity: {health['specialization_diversity']:.2f}",
            f"Number of Specializations: {health['num_specializations']}",
            "",
            "## AGENT PROGRESSION",
            f"Total Promotions: {progression['total_promotions']}",
            "Stage Transitions:",
        ]

        for transition, count in progression["transitions"].items():
            report_lines.append(f"  {transition}: {count}")

        report_lines.extend(
            [
                "",
                "Current Distribution:",
            ]
        )

        for stage, count in progression["current_distribution"].items():
            report_lines.append(f"  {stage}: {count}")

        report_lines.extend(
            [
                "",
                "## LEARNING PATTERNS",
                f"Total Papers Read: {learning['total_papers_read']}",
                f"Active Learners: {learning['active_learners']}",
                f"Help Requests: {learning['help_requests']}",
                f"Help Rate: {learning['help_rate']:.2%}",
                "Comprehension Distribution:",
            ]
        )

        for level, count in learning["comprehension_distribution"].items():
            report_lines.append(f"  {level}: {count}")

        report_lines.extend(
            [
                "",
                "## MENTORSHIP NETWORK",
                f"Active Mentorships: {mentorship['active_mentorships']}",
                f"Unique Mentors: {mentorship['unique_mentors']}",
                f"Unique Students: {mentorship['unique_students']}",
                f"Total Sessions: {mentorship['total_sessions']}",
                f"Recent Teaching Events: {mentorship['recent_teaching_events']}",
                "",
                "## RESEARCH PRODUCTIVITY",
                f"Total Experiments: {research['total_experiments']}",
                f"Successful: {research['successful_experiments']}",
                f"Failed: {research['failed_experiments']}",
                f"Success Rate: {research['success_rate']:.2%}",
                f"Papers Submitted: {research['papers_submitted']}",
                f"Reviews Submitted: {research['reviews_submitted']}",
                f"Active Researchers: {research['active_researchers']}",
                "",
                "## COLLABORATION PATTERNS",
                f"Proposed: {collaboration['proposed']}",
                f"Accepted: {collaboration['accepted']}",
                f"Completed: {collaboration['completed']}",
                f"Acceptance Rate: {collaboration['acceptance_rate']:.2%}",
                f"Completion Rate: {collaboration['completion_rate']:.2%}",
                f"Total Collaborations: {collaboration['total_collaborations']}",
                f"Unique Collaborators: {collaboration['unique_collaborators']}",
                "",
                "## KNOWLEDGE DIFFUSION",
                f"Total Learning Events: {knowledge['total_learning_events']}",
                f"Unique Concepts Learned: {knowledge['unique_concepts_learned']}",
                "Most Learned Concepts:",
            ]
        )

        for concept, count in list(knowledge["most_learned_concepts"].items())[:5]:
            report_lines.append(f"  {concept}: {count}")

        report_lines.extend(["", "Popular Concepts:"])

        for item in knowledge["popular_concepts"][:5]:
            report_lines.append(f"  {item['concept']}: {item['agents']} agents")

        report_lines.extend(
            [
                "",
                "=" * 80,
            ]
        )

        report = "\n".join(report_lines)

        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            self.logger.info("report_saved", path=str(output_path))

        return report


async def main():
    """Main entry point."""
    logger.info("analysis_script_started")

    analyzer = CommunityAnalyzer()

    try:
        # Connect to storage
        await analyzer.state_store.connect()
        await analyzer.graph_store.connect()

        # Load agents from database into community
        logger.info("loading_agents_from_database")
        loaded_count = await analyzer.community.load_agents_from_database()
        logger.info("agents_loaded", count=loaded_count)

        # Generate report
        report = await analyzer.generate_report(
            output_path=Path("reports") / f"community_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        # Print report
        print(report)

        logger.info("analysis_script_completed")

    except Exception as e:
        logger.error("analysis_script_failed", error=str(e))
        raise
    finally:
        # Cleanup
        await analyzer.state_store.disconnect()
        await analyzer.graph_store.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
