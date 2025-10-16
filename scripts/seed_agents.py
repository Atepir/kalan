"""
Seed initial agents into the community.

Creates a diverse set of agents across all developmental stages
to bootstrap the research collective.
"""

import asyncio
from pathlib import Path
from uuid import uuid4

import yaml

from src.core.agent import Agent, AgentStage
from src.orchestration.community import get_community
from src.storage.state_store import get_state_store
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def load_agent_templates() -> list[dict]:
    """
    Load agent templates from YAML configuration.

    Returns:
        List of agent template dictionaries
    """
    config_path = Path("config/agent_templates.yaml")

    if not config_path.exists():
        logger.warning(f"Agent templates file not found: {config_path}")
        return []

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return data.get("agents", [])


async def create_agent_from_template(template: dict) -> Agent:
    """
    Create an agent from a template.

    Args:
        template: Agent template dictionary

    Returns:
        Created Agent instance
    """
    agent = Agent(
        name=template["name"],
        stage=AgentStage(template["stage"]),
        specialization=template["specialization"],
    )

    # Set capabilities based on stage (important: agents created at higher stages need proper capabilities)
    stage_configs = {
        AgentStage.APPRENTICE: {
            "can_teach": False,
            "can_conduct_research": False,
            "can_review_papers": False,
            "requires_mentor": True,
        },
        AgentStage.PRACTITIONER: {
            "can_teach": False,
            "can_conduct_research": False,
            "can_review_papers": False,
            "requires_mentor": True,
        },
        AgentStage.TEACHER: {
            "can_teach": True,
            "can_conduct_research": True,
            "can_review_papers": False,
            "requires_mentor": False,
        },
        AgentStage.RESEARCHER: {
            "can_teach": True,
            "can_conduct_research": True,
            "can_review_papers": True,
            "requires_mentor": False,
        },
        AgentStage.EXPERT: {
            "can_teach": True,
            "can_conduct_research": True,
            "can_review_papers": True,
            "requires_mentor": False,
        },
    }
    
    config = stage_configs.get(agent.stage, {})
    for key, value in config.items():
        setattr(agent, key, value)

    # Add initial knowledge if specified
    initial_knowledge = template.get("knowledge", [])
    for topic_data in initial_knowledge:
        # Normalize depth to 0-1 range (divide by 5 if it's in 1-5 scale)
        depth = topic_data.get("depth", 0.1)
        if depth > 1.0:
            depth = depth / 5.0  # Convert 1-5 scale to 0.2-1.0
        
        agent.knowledge.add_topic(
            name=topic_data["name"],
            depth_score=min(depth, 1.0),  # Ensure it's <= 1.0
            confidence=topic_data.get("confidence", 0.5),
        )

    # Set initial reputation if specified
    if "reputation" in template:
        rep_data = template["reputation"]
        # Note: ReputationScore doesn't have a 'score' field, it has dimensions
        # Set initial values for reputation dimensions if provided
        if "teaching" in rep_data:
            agent.reputation.teaching = rep_data["teaching"]
        if "research" in rep_data:
            agent.reputation.research = rep_data["research"]
        agent.reputation.teaching_sessions = rep_data.get("teaching_count", 0)
        agent.reputation.reviews_completed = rep_data.get("review_count", 0)
        agent.reputation.papers_published = rep_data.get("papers_published", 0)

    return agent


async def seed_agents(num_agents: int | None = None) -> list[Agent]:
    """
    Seed agents into the community.

    Args:
        num_agents: Number of agents to create (None = all from templates)

    Returns:
        List of created agents
    """
    logger.info("seeding_agents_started", num_agents=num_agents)

    community = get_community()
    state_store = get_state_store()

    # Connect to state store
    await state_store.connect()

    # Load templates
    templates = await load_agent_templates()

    if not templates:
        logger.error("no_agent_templates_found")
        return []

    # Limit number if specified
    if num_agents:
        templates = templates[:num_agents]

    # Create and register agents
    created_agents = []

    for template in templates:
        try:
            agent = await create_agent_from_template(template)

            # Register with community
            await community.register_agent(agent)

            created_agents.append(agent)

            logger.info(
                "agent_created",
                agent_id=str(agent.agent_id),
                name=agent.name,
                stage=agent.stage.value,
                specialization=agent.specialization,
            )

        except Exception as e:
            logger.error(
                "failed_to_create_agent",
                name=template.get("name", "unknown"),
                error=str(e),
            )

    logger.info(
        "seeding_agents_completed",
        total_created=len(created_agents),
    )

    return created_agents


async def seed_default_agents() -> list[Agent]:
    """
    Seed a default set of agents if no templates are found.

    Returns:
        List of created agents
    """
    logger.info("seeding_default_agents")

    community = get_community()
    state_store = get_state_store()

    await state_store.connect()

    default_specs = [
        # Apprentices (5)
        ("Alice", "machine learning"),
        ("Bob", "natural language processing"),
        ("Carol", "computer vision"),
        ("Dave", "reinforcement learning"),
        ("Eve", "optimization"),
        # Practitioners (3)
        ("Frank", "deep learning"),
        ("Grace", "neural networks"),
        ("Hank", "transfer learning"),
        # Teachers (2)
        ("Ivy", "machine learning"),
        ("Jack", "statistics"),
        # Researchers (1)
        ("Karen", "meta-learning"),
    ]

    agents = []

    for i, (name, specialization) in enumerate(default_specs):
        # Determine stage based on index
        if i < 5:
            stage = AgentStage.APPRENTICE
        elif i < 8:
            stage = AgentStage.PRACTITIONER
        elif i < 10:
            stage = AgentStage.TEACHER
        else:
            stage = AgentStage.RESEARCHER

        agent = Agent(
            name=name,
            stage=stage,
            specialization=specialization,
        )

        # Set capabilities based on stage (important: agents created at higher stages need proper capabilities)
        stage_configs = {
            AgentStage.APPRENTICE: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "requires_mentor": True,
            },
            AgentStage.PRACTITIONER: {
                "can_teach": False,
                "can_conduct_research": False,
                "can_review_papers": False,
                "requires_mentor": True,
            },
            AgentStage.TEACHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": False,
                "requires_mentor": False,
            },
            AgentStage.RESEARCHER: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "requires_mentor": False,
            },
            AgentStage.EXPERT: {
                "can_teach": True,
                "can_conduct_research": True,
                "can_review_papers": True,
                "requires_mentor": False,
            },
        }
        
        config = stage_configs.get(stage, {})
        for key, value in config.items():
            setattr(agent, key, value)

        # Add some initial knowledge
        topics = [specialization, "python", "research methods"]
        for topic in topics:
            depth_score = 0.7 if stage in [AgentStage.TEACHER, AgentStage.RESEARCHER] else 0.3
            agent.knowledge.add_topic(topic, depth_score=depth_score, confidence=0.7)

        await community.register_agent(agent)
        agents.append(agent)

        logger.info(
            "default_agent_created",
            name=agent.name,
            stage=agent.stage.value,
            specialization=agent.specialization,
        )

    logger.info("default_agents_seeded", total=len(agents))

    return agents


async def print_agent_summary(agents: list[Agent]) -> None:
    """
    Print summary of seeded agents.

    Args:
        agents: List of agents
    """
    print("\n" + "=" * 60)
    print("SEEDED AGENTS SUMMARY")
    print("=" * 60)

    # Group by stage
    by_stage: dict[AgentStage, list[Agent]] = {}
    for agent in agents:
        if agent.stage not in by_stage:
            by_stage[agent.stage] = []
        by_stage[agent.stage].append(agent)

    # Print by stage
    for stage in AgentStage:
        if stage in by_stage:
            stage_agents = by_stage[stage]
            print(f"\n{stage.value.upper()} ({len(stage_agents)} agents):")
            for agent in stage_agents:
                topics = ", ".join(list(agent.knowledge.topics.keys())[:3])
                print(f"  - {agent.name} ({agent.specialization})")
                print(f"    Topics: {topics}")
                print(f"    Reputation: {agent.reputation.overall:.2f}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {len(agents)} agents")
    print("=" * 60 + "\n")


async def main():
    """Main entry point."""
    logger.info("seed_agents_script_started")

    try:
        # Try to load from templates
        agents = await seed_agents()

        # If no templates found, use defaults
        if not agents:
            logger.info("using_default_agents")
            agents = await seed_default_agents()

        # Print summary
        await print_agent_summary(agents)

        # Get community stats
        community = get_community()
        stats = await community.get_community_stats()

        print(f"\nCommunity Statistics:")
        print(f"  Total agents: {stats['total_agents']}")
        print(f"  Active agents: {stats['active_agents']}")
        print(f"  Average reputation: {stats['avg_reputation']:.2f}")
        print(f"\nAgents by stage:")
        for stage, count in stats['agents_by_stage'].items():
            print(f"  {stage}: {count}")

        logger.info("seed_agents_script_completed", total_agents=len(agents))

    except Exception as e:
        logger.error("seed_agents_script_failed", error=str(e))
        raise
    finally:
        # Cleanup
        community = get_community()
        await community.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
