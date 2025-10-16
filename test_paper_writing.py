"""
Test script to verify paper writing functionality.
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


async def test_paper_writing():
    """Test the paper writing functionality."""
    
    print("=" * 80)
    print("Testing Paper Writing Functionality")
    print("=" * 80)
    
    # Create a researcher agent
    agent = Agent(
        name="Dr. Test Researcher",
        stage=AgentStage.RESEARCHER,
        specialization="machine learning",
        knowledge=KnowledgeGraph(),
        reputation=ReputationScore(),
        can_conduct_research=True,
        can_review_papers=True,
    )
    
    print(f"\n✓ Created agent: {agent.name} ({agent.stage.value})")
    
    # Create research activity
    research = ResearchActivity(agent)
    
    print("✓ Created research activity manager")
    
    # Simulate a literature review
    lit_review = LiteratureReview(
        research_question="How can we improve neural network training efficiency?",
        papers_reviewed=["paper1", "paper2", "paper3"],
        current_state="Active research area with multiple approaches",
        key_methodologies=["Gradient descent", "Adaptive learning rates"],
        major_findings=["Finding 1", "Finding 2"],
        literature_gaps=["Gap in understanding optimization dynamics"],
        contradictions=[],
        future_directions=["Explore novel optimization methods"],
        timestamp=datetime.utcnow(),
    )
    
    print("✓ Created literature review")
    
    # Simulate an experiment
    experiment = ExperimentResult(
        experiment_id=f"exp_{agent.agent_id}_001",
        hypothesis="Proposed adaptive learning rate method improves convergence",
        methodology="Experimental validation on benchmark datasets",
        results={"accuracy": 0.92, "convergence_speed": "improved"},
        analysis="Results show significant improvements in both accuracy and training time",
        statistical_significance=0.03,
        supports_hypothesis=True,
        limitations=["Limited to specific dataset types"],
        implications=["Can be applied to various neural network architectures"],
        status=ExperimentStatus.COMPLETED,
        timestamp=datetime.utcnow(),
    )
    
    print("✓ Created experiment results")
    
    # Write paper
    print("\n📝 Writing research paper...")
    
    try:
        paper = await research.write_paper(
            title="Improving Neural Network Training Efficiency with Adaptive Learning Rates",
            research_question="How can we improve neural network training efficiency?",
            literature_review=lit_review,
            experiments=[experiment],
            keywords=["neural networks", "machine learning", "optimization"],
        )
        
        print("\n" + "=" * 80)
        print("✅ PAPER SUCCESSFULLY WRITTEN!")
        print("=" * 80)
        print(f"\nPaper ID: {paper.paper_id}")
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors)}")
        print(f"Keywords: {', '.join(paper.keywords)}")
        print(f"References: {len(paper.references)}")
        print(f"Experiments: {len(paper.experiment_ids)}")
        
        print(f"\n--- Abstract ---")
        print(paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract)
        
        print(f"\n--- Introduction (excerpt) ---")
        print(paper.introduction[:200] + "..." if len(paper.introduction) > 200 else paper.introduction)
        
        print(f"\n--- Agent Statistics ---")
        print(f"Papers authored: {len(agent.papers_authored)}")
        print(f"Research reputation: {agent.reputation.research:.2f}")
        print(f"Overall reputation: {agent.reputation.overall:.2f}")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error writing paper: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_paper_writing())
    exit(0 if success else 1)
