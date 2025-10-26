"""
Test script to verify the improved research content generation.
"""

import asyncio
from datetime import datetime

from src.core.agent import Agent, AgentStage
from src.core.knowledge import KnowledgeGraph
from src.core.reputation import ReputationScore
from scripts.run_simulation import Simulation, SimulationConfig


async def test_research_content_generation():
    """Test the research content generation."""
    
    print("=" * 80)
    print("Testing Improved Research Content Generation")
    print("=" * 80)
    
    # Create a simulation instance
    config = SimulationConfig(
        num_steps=1,
        step_duration=0.5,
        enable_workflows=False,
    )
    sim = Simulation(config)
    
    # Create a test agent
    agent = Agent(
        name="Dr. Test Researcher",
        stage=AgentStage.RESEARCHER,
        specialization="machine learning",
        knowledge=KnowledgeGraph(),
        reputation=ReputationScore(),
        can_conduct_research=True,
    )
    
    print(f"\n✓ Created test agent: {agent.name}")
    
    # Test generating research content for different topics
    topics = ["neural networks", "reinforcement learning", "transfer learning"]
    
    for topic in topics:
        print(f"\n{'='*80}")
        print(f"Generating research content for: {topic}")
        print('='*80)
        
        try:
            content = await sim._generate_research_content(agent, topic)
            
            print(f"\n✓ Title: {content['title']}")
            print(f"\n✓ Research Question: {content['research_question']}")
            print(f"\n✓ Hypothesis: {content['hypothesis']}")
            print(f"\n✓ Keywords: {', '.join(content['keywords'])}")
            print(f"\n✓ Current State: {content['current_state']}")
            print(f"\n✓ Methodologies: {', '.join(content['methodologies'])}")
            print(f"\n✓ Gaps: {'; '.join(content['gaps'])}")
            print(f"\n✓ Methodology: {content['methodology'][:150]}...")
            
        except Exception as e:
            print(f"\n❌ Error generating content for {topic}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_research_content_generation())
    exit(0 if success else 1)
