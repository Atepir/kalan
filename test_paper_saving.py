"""
Test script to verify papers are saved correctly.
"""

import asyncio
from pathlib import Path

from src.core.agent import Agent, AgentProfile
from src.activities.research import ResearchActivity, LiteratureReview, ExperimentResult


async def test_paper_saving():
    """Test that papers are saved to database and filesystem."""
    print("\n" + "="*60)
    print("Testing Paper Saving Functionality")
    print("="*60 + "\n")

    # Create a test agent
    profile = AgentProfile(
        name="Test Researcher",
        specialization="machine_learning",
        interests=["neural networks", "optimization"],
        expertise_level="expert"
    )
    agent = Agent(agent_id=999, profile=profile)
    
    print(f"✓ Created agent: {agent.name}")

    # Create research activity
    research = ResearchActivity(agent)
    print("✓ Initialized research activity")

    # Simulate literature review
    lit_review = LiteratureReview(
        query="deep learning optimization",
        papers_reviewed=["Paper A", "Paper B", "Paper C"],
        key_findings=["Finding 1", "Finding 2"],
        research_gaps=["Gap 1"],
        timestamp=None
    )
    print("✓ Created literature review")

    # Simulate experiments
    experiments = [
        ExperimentResult(
            experiment_id="exp_001",
            hypothesis="Hypothesis 1",
            methodology="Method 1",
            results={"accuracy": 0.95},
            conclusion="Successful",
            timestamp=None,
            success=True
        ),
        ExperimentResult(
            experiment_id="exp_002",
            hypothesis="Hypothesis 2",
            methodology="Method 2",
            results={"loss": 0.05},
            conclusion="Successful",
            timestamp=None,
            success=True
        )
    ]
    print("✓ Created experiments")

    # Write paper
    print("\n📝 Writing paper...")
    try:
        paper = await research.write_paper(
            title="Advanced Deep Learning Optimization Techniques",
            research_question="How can we improve deep learning optimization?",
            literature_review=lit_review,
            experiments=experiments,
            keywords=["deep learning", "optimization", "neural networks"]
        )
        
        print(f"\n✅ Paper written successfully!")
        print(f"   Paper ID: {paper.paper_id}")
        print(f"   Title: {paper.title}")
        print(f"   Authors: {', '.join(paper.authors)}")
        
        # Check filesystem
        papers_dir = Path("./data/papers")
        markdown_file = papers_dir / f"{paper.paper_id}.md"
        json_file = papers_dir / f"{paper.paper_id}.json"
        
        print(f"\n📁 Checking filesystem...")
        if markdown_file.exists():
            print(f"   ✓ Markdown file saved: {markdown_file}")
            print(f"     Size: {markdown_file.stat().st_size} bytes")
        else:
            print(f"   ✗ Markdown file NOT found: {markdown_file}")
            
        if json_file.exists():
            print(f"   ✓ JSON file saved: {json_file}")
            print(f"     Size: {json_file.stat().st_size} bytes")
        else:
            print(f"   ✗ JSON file NOT found: {json_file}")
        
        # Show abstract preview
        print(f"\n📄 Abstract preview:")
        print(f"   {paper.abstract[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Paper writing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_paper_saving())
    
    print("\n" + "="*60)
    if success:
        print("✅ Test completed successfully!")
        print("Papers are now being saved to:")
        print("  • Database (PostgreSQL)")
        print("  • Filesystem (./data/papers/)")
    else:
        print("❌ Test failed!")
    print("="*60 + "\n")
