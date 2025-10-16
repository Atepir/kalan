"""
Test script to verify agent research capabilities are properly set.
"""

import asyncio
from src.core.agent import Agent, AgentStage


async def test_agent_capabilities():
    """Test that agents have correct capabilities based on their stage."""
    
    print("Testing agent capability initialization...\n")
    
    stages = [
        AgentStage.APPRENTICE,
        AgentStage.PRACTITIONER,
        AgentStage.TEACHER,
        AgentStage.RESEARCHER,
        AgentStage.EXPERT,
    ]
    
    for stage in stages:
        agent = Agent(
            name=f"Test {stage.value}",
            stage=stage,
            specialization="testing",
        )
        
        print(f"{stage.value.upper()}:")
        print(f"  can_teach: {agent.can_teach}")
        print(f"  can_conduct_research: {agent.can_conduct_research}")
        print(f"  can_review_papers: {agent.can_review_papers}")
        print(f"  requires_mentor: {agent.requires_mentor}")
        print()


if __name__ == "__main__":
    asyncio.run(test_agent_capabilities())
