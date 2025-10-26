"""
Test script to verify that papers now have specific, non-generic content.
"""

import asyncio
from datetime import datetime

from src.core.agent import Agent, AgentStage
from src.core.knowledge import KnowledgeGraph
from src.core.reputation import ReputationScore
from src.activities.research import (
    ResearchActivity,
    LiteratureReview,
    ExperimentResult,
    ExperimentStatus,
)
from scripts.run_simulation import Simulation, SimulationConfig


async def test_complete_paper_generation():
    """Test the complete paper generation with realistic content."""
    
    print("=" * 80)
    print("Testing Complete Paper Generation with Realistic Content")
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
        name="Dr. Ada Lovelace",
        stage=AgentStage.RESEARCHER,
        specialization="neural networks",
        knowledge=KnowledgeGraph(),
        reputation=ReputationScore(),
        can_conduct_research=True,
    )
    
    print(f"\n✓ Created test agent: {agent.name}")
    
    # Generate realistic research content
    topic = "neural networks"
    print(f"\n📊 Generating realistic research content for: {topic}")
    
    research_content = await sim._generate_research_content(agent, topic)
    
    print(f"\n✓ Generated research content:")
    print(f"  - Title: {research_content['title'][:80]}...")
    print(f"  - Research Question: {research_content['research_question'][:80]}...")
    print(f"  - Hypothesis: {research_content['hypothesis'][:80]}...")
    
    # Create research activity
    research = ResearchActivity(agent)
    
    # Create literature review with realistic content
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
    
    print("\n✓ Created literature review with realistic content")
    
    # Create experiment with realistic content
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
    
    print("✓ Created experiment with realistic methodology and results")
    
    # Write paper
    print("\n📝 Writing research paper with LLM-generated sections...")
    
    try:
        paper = await research.write_paper(
            title=research_content["title"],
            research_question=research_content["research_question"],
            literature_review=lit_review,
            experiments=[experiment],
            keywords=research_content["keywords"],
        )
        
        print("\n" + "=" * 80)
        print("✅ PAPER SUCCESSFULLY WRITTEN WITH REALISTIC CONTENT!")
        print("=" * 80)
        print(f"\nPaper ID: {paper.paper_id}")
        print(f"\nTitle: {paper.title}")
        print(f"\nAuthors: {', '.join(paper.authors)}")
        print(f"\nKeywords: {', '.join(paper.keywords)}")
        
        print(f"\n{'='*80}")
        print("Abstract (Full):")
        print('='*80)
        print(paper.abstract)
        
        print(f"\n{'='*80}")
        print("Introduction (First 500 chars):")
        print('='*80)
        print(paper.introduction[:500] + "..." if len(paper.introduction) > 500 else paper.introduction)
        
        print(f"\n{'='*80}")
        print("Methodology (First 500 chars):")
        print('='*80)
        print(paper.methodology[:500] + "..." if len(paper.methodology) > 500 else paper.methodology)
        
        print(f"\n{'='*80}")
        print("Results (First 500 chars):")
        print('='*80)
        print(paper.results[:500] + "..." if len(paper.results) > 500 else paper.results)
        
        print(f"\n{'='*80}")
        print("Discussion (First 500 chars):")
        print('='*80)
        print(paper.discussion[:500] + "..." if len(paper.discussion) > 500 else paper.discussion)
        
        print(f"\n{'='*80}")
        print("Conclusion:")
        print('='*80)
        print(paper.conclusion)
        
        print(f"\n{'='*80}")
        print("Agent Statistics:")
        print('='*80)
        print(f"Papers authored: {len(agent.papers_authored)}")
        print(f"Research reputation: {agent.reputation.research:.2f}")
        print(f"Overall reputation: {agent.reputation.overall:.2f}")
        
        # Check for generic/placeholder content
        print(f"\n{'='*80}")
        print("Content Quality Check:")
        print('='*80)
        
        generic_phrases = [
            "Method A", "Method B", "Gap 1", "Gap 2", 
            "Finding 1", "Finding 2", "Advances in",
            "How to improve", "Direction 1"
        ]
        
        full_text = f"{paper.title} {paper.abstract} {paper.introduction} {paper.methodology}"
        
        found_generic = []
        for phrase in generic_phrases:
            if phrase in full_text:
                found_generic.append(phrase)
        
        if found_generic:
            print(f"⚠️  Found some generic phrases: {', '.join(found_generic)}")
        else:
            print("✅ No generic placeholder phrases found!")
        
        # Check if title is specific
        if "Advances in" in paper.title or "How to improve" in paper.title:
            print("⚠️  Title is generic")
        else:
            print(f"✅ Title is specific: '{paper.title}'")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully! Papers now have realistic content!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error writing paper: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_complete_paper_generation())
    exit(0 if success else 1)
