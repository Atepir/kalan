"""
Run multi-agent research simulation.

Orchestrates agent activities including learning, teaching,
research, and collaboration over multiple simulation steps.
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.agent import Agent, AgentStage
from src.orchestration.community import get_community
from src.orchestration.events import EventType, get_event_bus
from src.orchestration.matchmaking import Matchmaker
from src.storage.graph_store import get_graph_store
from src.storage.state_store import get_state_store
from src.storage.vector_store import get_vector_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SimulationConfig:
    """Configuration for simulation run."""

    def __init__(
        self,
        num_steps: int = 100,
        step_duration: float = 1.0,
        learning_probability: float = 0.7,
        teaching_probability: float = 0.3,
        research_probability: float = 0.4,
        collaboration_probability: float = 0.2,
        promotion_check_interval: int = 10,
        save_interval: int = 20,
        enable_workflows: bool = True,
    ):
        """
        Initialize simulation configuration.

        Args:
            num_steps: Number of simulation steps
            step_duration: Duration of each step in seconds
            learning_probability: Probability of learning activity per step
            teaching_probability: Probability of teaching activity per step
            research_probability: Probability of research activity per step
            collaboration_probability: Probability of collaboration per step
            promotion_check_interval: Steps between promotion checks
            save_interval: Steps between state saves
            enable_workflows: Whether to use LangGraph workflows
        """
        self.num_steps = num_steps
        self.step_duration = step_duration
        self.learning_probability = learning_probability
        self.teaching_probability = teaching_probability
        self.research_probability = research_probability
        self.collaboration_probability = collaboration_probability
        self.promotion_check_interval = promotion_check_interval
        self.save_interval = save_interval
        self.enable_workflows = enable_workflows


class Simulation:
    """
    Multi-agent research simulation.

    Coordinates agent activities over multiple time steps,
    managing learning, teaching, research, and collaboration.
    """

    def __init__(self, config: SimulationConfig | None = None):
        """
        Initialize simulation.

        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.community = get_community()
        self.event_bus = get_event_bus()
        self.matchmaker = Matchmaker()

        # Simulation state
        self.current_step = 0
        self.start_time: datetime | None = None
        self.running = False

        self.logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize simulation components."""
        self.logger.info("initializing_simulation")

        # Connect to storage
        state_store = get_state_store()
        await state_store.connect()

        graph_store = get_graph_store()
        await graph_store.connect()

        vector_store = get_vector_store()
        await vector_store.connect()

        # Load agents from database into community
        agents_loaded = await self.community.load_agents_from_database()
        self.logger.info("agents_loaded_into_community", count=agents_loaded)

        self.logger.info("simulation_initialized")

    async def step(self) -> dict[str, Any]:
        """
        Execute one simulation step.

        Returns:
            Step statistics
        """
        self.current_step += 1

        self.logger.info(
            "simulation_step_started",
            step=self.current_step,
        )

        stats = {
            "step": self.current_step,
            "learning_activities": 0,
            "teaching_activities": 0,
            "research_activities": 0,
            "papers_written": 0,
            "collaborations": 0,
            "promotions": 0,
        }

        # Get all active agents
        agents = await self.community.list_agents(active_only=True)

        if not agents:
            self.logger.warning("no_active_agents")
            return stats

        # Schedule activities based on stage
        tasks = []

        for agent in agents:
            # Apprentices and Practitioners primarily learn
            if agent.stage in [
                AgentStage.APPRENTICE,
                AgentStage.PRACTITIONER,
            ]:
                if random.random() < self.config.learning_probability:
                    tasks.append(self._learning_task(agent, stats))

            # Teachers teach and research
            if agent.stage == AgentStage.TEACHER:
                if random.random() < self.config.teaching_probability:
                    tasks.append(self._teaching_task(agent, stats))
                if random.random() < self.config.research_probability:
                    tasks.append(self._research_task(agent, stats))

            # Researchers and Experts focus on research
            if agent.stage in [
                AgentStage.RESEARCHER,
                AgentStage.EXPERT,
            ]:
                if random.random() < self.config.research_probability:
                    tasks.append(self._research_task(agent, stats))
                if random.random() < self.config.collaboration_probability:
                    tasks.append(self._collaboration_task(agent, stats))

        # Execute all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Check for promotions periodically
        if self.current_step % self.config.promotion_check_interval == 0:
            stats["promotions"] = await self._check_promotions()

        # Save state periodically
        if self.current_step % self.config.save_interval == 0:
            await self._save_state()

        # The stats dict already contains 'step', so don't pass it again
        self.logger.info(
            "simulation_step_completed",
            **stats,
        )

        return stats

    async def _learning_task(self, agent: Agent, stats: dict) -> None:
        """Execute learning task for agent."""
        try:
            # Pick a random topic to learn
            topics = ["machine learning", "deep learning", "optimization", "statistics"]
            topic = random.choice(topics)

            self.logger.debug(
                "agent_learning",
                agent_id=str(agent.agent_id),
                agent_name=agent.name,
                topic=topic,
            )

            # Use workflow or direct activity
            if self.config.enable_workflows:
                # Simulate with workflow (simplified)
                pass
            else:
                # Direct learning activity - read a paper
                try:
                    from pathlib import Path
                    import json
                    from src.activities.learning import LearningActivity
                    
                    # Get available papers
                    papers_dir = Path("data/papers")
                    paper_files = list(papers_dir.glob("*.json"))
                    
                    if paper_files:
                        # Pick a random paper that hasn't been read yet
                        unread_papers = [
                            p for p in paper_files 
                            if p.stem not in agent.papers_read
                        ]
                        
                        if not unread_papers:
                            # All papers read, pick any random one
                            unread_papers = paper_files
                        
                        paper_file = random.choice(unread_papers)
                        
                        # Load paper metadata
                        with open(paper_file, 'r') as f:
                            paper_data = json.load(f)
                        
                        # Create learning activity and read paper
                        learning = LearningActivity(agent)
                        result = await learning.read_paper(
                            paper_id=paper_data.get('paper_id', paper_file.stem),
                            paper_title=paper_data.get('title', 'Unknown Title'),
                            paper_abstract=paper_data.get('abstract', ''),
                        )
                        
                        self.logger.info(
                            "paper_read",
                            agent_id=str(agent.agent_id),
                            agent_name=agent.name,
                            paper_id=result.paper_id,
                            comprehension=result.comprehension_level.value,
                            confidence=result.confidence,
                        )
                        
                        stats["papers_read"] = stats.get("papers_read", 0) + 1
                        
                except Exception as inner_e:
                    self.logger.debug(
                        "learning_activity_skipped",
                        agent_id=str(agent.agent_id),
                        error=str(inner_e),
                    )

            stats["learning_activities"] += 1

        except Exception as e:
            self.logger.error(
                "learning_task_failed",
                agent_id=str(agent.agent_id),
                error=str(e),
            )

    async def _teaching_task(self, agent: Agent, stats: dict) -> None:
        """Execute teaching task for agent."""
        try:
            # Find a student who needs help
            students = await self.community.list_agents(
                stage=AgentStage.APPRENTICE,
                active_only=True,
            )

            if not students:
                return

            student = random.choice(students)
            topic = random.choice(["basics", "fundamentals", "intermediate"])

            self.logger.debug(
                "agent_teaching",
                teacher_id=str(agent.agent_id),
                teacher_name=agent.name,
                student_id=str(student.agent_id),
                student_name=student.name,
                topic=topic,
            )

            # Simulate teaching (simplified)
            # await self.teaching_activity.create_lesson(agent, student, topic)

            stats["teaching_activities"] += 1

        except Exception as e:
            self.logger.error(
                "teaching_task_failed",
                agent_id=str(agent.agent_id),
                error=str(e),
            )

    async def _research_task(self, agent: Agent, stats: dict) -> None:
        """Execute research task for agent."""
        try:
            # Pick a research topic
            topics = ["neural networks", "reinforcement learning", "transfer learning"]
            topic = random.choice(topics)

            self.logger.debug(
                "agent_researching",
                agent_id=str(agent.agent_id),
                agent_name=agent.name,
                topic=topic,
            )

            # Check if agent can conduct research
            if not agent.can_conduct_research:
                return

            # Use workflow or direct activity
            if self.config.enable_workflows:
                # Simulate with workflow (simplified)
                pass
            else:
                # Direct research activity - write a paper
                try:
                    from src.activities.research import (
                        ResearchActivity,
                        LiteratureReview,
                        ExperimentResult,
                        ExperimentStatus,
                    )
                    
                    # Create a research activity
                    research = ResearchActivity(agent)
                    
                    # Simulate a literature review
                    lit_review = LiteratureReview(
                        research_question=f"How to improve {topic}?",
                        papers_reviewed=["paper1", "paper2", "paper3"],
                        current_state="Active research area",
                        key_methodologies=["Method A", "Method B"],
                        major_findings=["Finding 1", "Finding 2"],
                        literature_gaps=["Gap 1"],
                        contradictions=[],
                        future_directions=["Direction 1"],
                        timestamp=datetime.utcnow(),
                    )
                    
                    # Simulate an experiment
                    experiment = ExperimentResult(
                        experiment_id=f"exp_{agent.agent_id}_{int(datetime.utcnow().timestamp())}",
                        hypothesis=f"Proposed improvement to {topic}",
                        methodology="Experimental validation",
                        results={"accuracy": 0.85},
                        analysis="Results show promising improvements",
                        statistical_significance=0.05,
                        supports_hypothesis=True,
                        limitations=["Limited dataset"],
                        implications=["Further research needed"],
                        status=ExperimentStatus.COMPLETED,
                        timestamp=datetime.utcnow(),
                    )
                    
                    # Write paper (every 3rd research activity)
                    if random.random() < 0.33:
                        paper = await research.write_paper(
                            title=f"Advances in {topic}",
                            research_question=f"How to improve {topic}?",
                            literature_review=lit_review,
                            experiments=[experiment],
                            keywords=[topic, "machine learning"],
                        )
                        
                        self.logger.info(
                            "paper_published",
                            agent_id=str(agent.agent_id),
                            agent_name=agent.name,
                            paper_id=paper.paper_id,
                            title=paper.title,
                        )
                        
                        stats["papers_written"] = stats.get("papers_written", 0) + 1
                    
                except Exception as inner_e:
                    self.logger.debug(
                        "research_activity_skipped",
                        agent_id=str(agent.agent_id),
                        error=str(inner_e),
                    )

            stats["research_activities"] += 1

        except Exception as e:
            self.logger.error(
                "research_task_failed",
                agent_id=str(agent.agent_id),
                error=str(e),
            )

    async def _collaboration_task(self, agent: Agent, stats: dict) -> None:
        """Execute collaboration task for agent."""
        try:
            # Find collaboration partners
            partners = await self.matchmaker.find_collaboration_partners(
                agent=agent,
                topic="research",
                max_partners=2,
            )

            if not partners:
                return

            self.logger.debug(
                "agent_collaborating",
                lead_id=str(agent.agent_id),
                lead_name=agent.name,
                num_partners=len(partners),
            )

            # Simulate collaboration (simplified)
            stats["collaborations"] += 1

        except Exception as e:
            self.logger.error(
                "collaboration_task_failed",
                agent_id=str(agent.agent_id),
                error=str(e),
            )

    async def _check_promotions(self) -> int:
        """Check all agents for possible promotions."""
        count = 0
        agents = await self.community.list_agents(active_only=True)

        for agent in agents:
            from uuid import UUID
            success = await self.community.promote_agent(UUID(agent.agent_id))
            if success:
                count += 1

        return count

    async def _save_state(self) -> None:
        """Save current simulation state."""
        self.logger.info("saving_simulation_state", step=self.current_step)

        # Save all agents
        agents = await self.community.list_agents(active_only=True)
        state_store = get_state_store()

        for agent in agents:
            await state_store.save_agent(agent)

        self.logger.info("simulation_state_saved", num_agents=len(agents))

    async def run(self) -> dict[str, Any]:
        """
        Run the complete simulation.

        Returns:
            Simulation results
        """
        self.logger.info(
            "simulation_run_started",
            num_steps=self.config.num_steps,
        )

        self.running = True
        self.start_time = datetime.utcnow()

        total_stats = {
            "total_learning": 0,
            "total_teaching": 0,
            "total_research": 0,
            "total_papers": 0,
            "total_collaborations": 0,
            "total_promotions": 0,
        }

        try:
            for _ in range(self.config.num_steps):
                if not self.running:
                    self.logger.info("simulation_stopped_early")
                    break

                # Execute step
                step_stats = await self.step()

                # Accumulate stats
                total_stats["total_learning"] += step_stats["learning_activities"]
                total_stats["total_teaching"] += step_stats["teaching_activities"]
                total_stats["total_research"] += step_stats["research_activities"]
                total_stats["total_papers"] += step_stats.get("papers_written", 0)
                total_stats["total_collaborations"] += step_stats["collaborations"]
                total_stats["total_promotions"] += step_stats["promotions"]

                # Wait for step duration
                await asyncio.sleep(self.config.step_duration)

        except Exception as e:
            self.logger.error("simulation_failed", error=str(e))
            raise
        finally:
            self.running = False

        # Final state save
        await self._save_state()

        # Get final community stats
        community_stats = await self.community.get_community_stats()

        results = {
            "steps_completed": self.current_step,
            "duration": (datetime.utcnow() - self.start_time).total_seconds()
            if self.start_time
            else 0,
            "activity_stats": total_stats,
            "community_stats": community_stats,
        }

        self.logger.info("simulation_run_completed", **results)

        return results

    async def stop(self) -> None:
        """Stop the simulation."""
        self.logger.info("stopping_simulation")
        self.running = False

    async def cleanup(self) -> None:
        """Cleanup simulation resources."""
        self.logger.info("cleaning_up_simulation")

        # Shutdown community
        await self.community.shutdown()

        # Disconnect storage
        state_store = get_state_store()
        await state_store.disconnect()

        graph_store = get_graph_store()
        await graph_store.disconnect()

        vector_store = get_vector_store()
        await vector_store.disconnect()


async def main():
    """Main entry point."""
    logger.info("simulation_script_started")

    # Configure simulation
    config = SimulationConfig(
        num_steps=50,
        step_duration=0.5,  # Fast simulation
        learning_probability=0.7,
        teaching_probability=0.3,
        research_probability=0.4,
        collaboration_probability=0.2,
        promotion_check_interval=10,
        save_interval=20,
        enable_workflows=False,  # Simplified for now
    )

    simulation = Simulation(config)

    try:
        # Initialize
        await simulation.initialize()

        # Run simulation
        results = await simulation.run()

        # Print results
        print("\n" + "=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"\nSteps completed: {results['steps_completed']}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print("\nActivity Statistics:")
        for key, value in results["activity_stats"].items():
            print(f"  {key}: {value}")
        print("\nCommunity Statistics:")
        print(f"  Total agents: {results['community_stats']['total_agents']}")
        print(f"  Active agents: {results['community_stats']['active_agents']}")
        print(
            f"  Average reputation: {results['community_stats']['avg_reputation']:.2f}"
        )
        print("\nAgents by stage:")
        for stage, count in results["community_stats"]["agents_by_stage"].items():
            print(f"  {stage}: {count}")
        print("\n" + "=" * 60 + "\n")

        logger.info("simulation_script_completed")

    except KeyboardInterrupt:
        logger.info("simulation_interrupted_by_user")
        await simulation.stop()
    except Exception as e:
        logger.error("simulation_script_failed", error=str(e))
        raise
    finally:
        await simulation.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
