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

    async def _generate_research_content(self, agent: Agent, topic: str) -> dict[str, Any]:
        """
        Generate realistic research content using LLM.
        
        Args:
            agent: The agent conducting research
            topic: The research topic
            
        Returns:
            Dictionary containing all research components
        """
        from src.llm.client import get_ollama_client
        
        llm = get_ollama_client()
        
        # Generate specific research details
        prompt = f"""You are a research assistant helping to design a realistic research project on {topic}.

Generate the following components for a research project (provide each component on a separate line with clear labels):

1. TITLE: A specific, academic paper title (not just "Advances in {topic}")
2. RESEARCH_QUESTION: A specific research question
3. HYPOTHESIS: A testable hypothesis
4. METHODOLOGY: A specific experimental methodology (2-3 sentences)
5. CURRENT_STATE: Current state of research in this area (1-2 sentences)
6. METHODOLOGIES: Three specific methodologies used in the field (comma-separated)
7. FINDINGS: Three major findings from existing research (semicolon-separated)
8. GAPS: Two specific gaps in the literature (semicolon-separated)
9. FUTURE_DIRECTIONS: Two specific future research directions (semicolon-separated)
10. KEYWORDS: 3-4 relevant keywords (comma-separated)

Be specific and realistic. Avoid generic placeholders."""

        response = await llm.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.8,
        )
        
        content_text = response.get("content", "") if isinstance(response, dict) else response
        
        # Parse the response
        parsed = self._parse_research_content(content_text, topic)
        
        # Add experiment-specific content
        parsed.update({
            "results": {
                "accuracy": round(0.75 + random.random() * 0.20, 3),
                "precision": round(0.70 + random.random() * 0.25, 3),
                "training_time": round(random.uniform(10, 100), 1),
            },
            "analysis": f"The experimental results demonstrate the effectiveness of the proposed approach for {topic}. Key metrics show significant improvements over baseline methods.",
            "statistical_significance": round(random.uniform(0.001, 0.05), 3),
            "supports_hypothesis": random.random() > 0.2,  # 80% support
            "limitations": [
                "Limited to specific dataset configurations",
                f"Computational complexity may scale with {topic} complexity",
            ],
            "implications": [
                f"Potential for real-world applications in {topic}",
                "Opens new avenues for future research",
            ],
            "papers_reviewed": [
                f"Prior work on {topic} foundations",
                f"Recent advances in {topic} methods",
                f"Comparative study of {topic} approaches",
            ],
            "contradictions": [],
        })
        
        return parsed

    def _parse_research_content(self, llm_response: str, topic: str) -> dict[str, Any]:
        """Parse research content from LLM response."""
        lines = llm_response.strip().split('\n')
        
        # Default values in case parsing fails
        defaults = {
            "title": f"Novel Approaches to {topic.title()} Optimization",
            "research_question": f"How can we improve efficiency and performance in {topic} systems?",
            "hypothesis": f"A novel architecture can enhance {topic} performance",
            "methodology": f"We designed a controlled experiment comparing our approach against state-of-the-art {topic} methods using standard benchmarks",
            "current_state": f"Current {topic} research focuses on improving performance and scalability",
            "methodologies": ["Deep learning approaches", "Optimization techniques", "Ensemble methods"],
            "findings": [
                f"Existing {topic} methods show promising results",
                "Recent techniques improve upon traditional approaches",
                "Performance varies significantly across different configurations",
            ],
            "gaps": [
                f"Limited research on scalability in {topic}",
                "Insufficient attention to computational efficiency",
            ],
            "future_directions": [
                f"Exploring novel architectures for {topic}",
                "Investigating cross-domain applications",
            ],
            "keywords": [topic, "machine learning", "optimization", "performance"],
        }
        
        # Try to parse LLM response
        parsed = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to extract labeled content
            if "TITLE:" in line:
                parsed["title"] = line.split("TITLE:", 1)[1].strip().strip('"')
            elif "RESEARCH_QUESTION:" in line:
                parsed["research_question"] = line.split("RESEARCH_QUESTION:", 1)[1].strip()
            elif "HYPOTHESIS:" in line:
                parsed["hypothesis"] = line.split("HYPOTHESIS:", 1)[1].strip()
            elif "METHODOLOGY:" in line:
                parsed["methodology"] = line.split("METHODOLOGY:", 1)[1].strip()
            elif "CURRENT_STATE:" in line:
                parsed["current_state"] = line.split("CURRENT_STATE:", 1)[1].strip()
            elif "METHODOLOGIES:" in line:
                methods_str = line.split("METHODOLOGIES:", 1)[1].strip()
                parsed["methodologies"] = [m.strip() for m in methods_str.split(',')][:3]
            elif "FINDINGS:" in line:
                findings_str = line.split("FINDINGS:", 1)[1].strip()
                parsed["findings"] = [f.strip() for f in findings_str.split(';')][:3]
            elif "GAPS:" in line:
                gaps_str = line.split("GAPS:", 1)[1].strip()
                parsed["gaps"] = [g.strip() for g in gaps_str.split(';')][:2]
            elif "FUTURE_DIRECTIONS:" in line:
                dirs_str = line.split("FUTURE_DIRECTIONS:", 1)[1].strip()
                parsed["future_directions"] = [d.strip() for d in dirs_str.split(';')][:2]
            elif "KEYWORDS:" in line:
                kw_str = line.split("KEYWORDS:", 1)[1].strip()
                parsed["keywords"] = [k.strip() for k in kw_str.split(',')]
        
        # Merge parsed with defaults
        result = defaults.copy()
        result.update(parsed)
        
        return result

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
                    
                    # Generate realistic research content
                    research_content = await self._generate_research_content(agent, topic)
                    
                    # Simulate a literature review with realistic content
                    lit_review = LiteratureReview(
                        research_question=research_content["research_question"],
                        papers_reviewed=research_content["papers_reviewed"],
                        current_state=research_content["current_state"],
                        key_methodologies=research_content["methodologies"],
                        major_findings=research_content["findings"],
                        literature_gaps=research_content["gaps"],
                        contradictions=research_content["contradictions"],
                        future_directions=research_content["future_directions"],
                        timestamp=datetime.utcnow(),
                    )
                    
                    # Simulate an experiment with realistic content
                    experiment = ExperimentResult(
                        experiment_id=f"exp_{agent.agent_id}_{int(datetime.utcnow().timestamp())}",
                        hypothesis=research_content["hypothesis"],
                        methodology=research_content["methodology"],
                        results=research_content["results"],
                        analysis=research_content["analysis"],
                        statistical_significance=research_content["statistical_significance"],
                        supports_hypothesis=research_content["supports_hypothesis"],
                        limitations=research_content["limitations"],
                        implications=research_content["implications"],
                        status=ExperimentStatus.COMPLETED,
                        timestamp=datetime.utcnow(),
                    )
                    
                    # Write paper (every 3rd research activity)
                    if random.random() < 0.33:
                        paper = await research.write_paper(
                            title=research_content["title"],
                            research_question=research_content["research_question"],
                            literature_review=lit_review,
                            experiments=[experiment],
                            keywords=research_content["keywords"],
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
