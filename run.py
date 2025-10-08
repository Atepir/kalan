"""
Master run script for the Research Collective.

Orchestrates the complete workflow:
1. Infrastructure startup (Docker)
2. Database initialization
3. Knowledge graph seeding
4. Agent community seeding
5. Simulation execution
6. Analysis and reporting
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logging import get_logger

logger = get_logger(__name__)


class MasterRunner:
    """Orchestrates the complete Research Collective workflow."""

    def __init__(
        self,
        skip_docker: bool = False,
        skip_seed: bool = False,
        simulation_steps: int = 50,
        simulation_duration: float = 0.5,
    ):
        """
        Initialize master runner.

        Args:
            skip_docker: Skip Docker infrastructure check
            skip_seed: Skip data seeding (use existing data)
            simulation_steps: Number of simulation steps
            simulation_duration: Duration of each step in seconds
        """
        self.skip_docker = skip_docker
        self.skip_seed = skip_seed
        self.simulation_steps = simulation_steps
        self.simulation_duration = simulation_duration
        self.logger = get_logger(__name__)

    def print_banner(self, text: str) -> None:
        """Print a banner with text."""
        print("\n" + "=" * 80)
        print(f" {text}")
        print("=" * 80 + "\n")

    def check_docker(self) -> bool:
        """
        Check if Docker services are running.

        Returns:
            True if all services are up
        """
        if self.skip_docker:
            self.logger.info("Skipping Docker check")
            return True

        self.print_banner("Checking Docker Infrastructure")

        try:
            import subprocess

            # Check if docker-compose is available
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                print("❌ docker-compose not found")
                print("   Please install Docker and Docker Compose")
                return False

            print(f"✅ Docker Compose: {result.stdout.strip()}")

            # Check if services are running
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "postgres" not in result.stdout:
                print("⚠️  PostgreSQL not running")
                print("   Starting Docker services...")
                start_result = subprocess.run(
                    ["docker-compose", "up", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if start_result.returncode != 0:
                    print(f"❌ Failed to start services: {start_result.stderr}")
                    return False
                print("✅ Docker services started")
                print("   Waiting 10 seconds for services to be ready...")
                time.sleep(10)
            else:
                print("✅ Docker services are running")

            return True

        except subprocess.TimeoutExpired:
            print("❌ Docker command timed out")
            return False
        except FileNotFoundError:
            print("❌ docker-compose not found in PATH")
            return False
        except Exception as e:
            print(f"❌ Error checking Docker: {e}")
            return False

    async def seed_knowledge(self) -> bool:
        """
        Seed knowledge graph.

        Returns:
            True if successful
        """
        if self.skip_seed:
            self.logger.info("Skipping knowledge seeding")
            return True

        self.print_banner("Seeding Knowledge Graph")

        try:
            # Import and run seed_knowledge
            from scripts.seed_knowledge import main as seed_knowledge_main

            await seed_knowledge_main()
            return True

        except Exception as e:
            self.logger.error("knowledge_seeding_failed", error=str(e))
            print(f"❌ Knowledge seeding failed: {e}")
            return False

    async def seed_agents(self) -> bool:
        """
        Seed agent community.

        Returns:
            True if successful
        """
        if self.skip_seed:
            self.logger.info("Skipping agent seeding")
            return True

        self.print_banner("Seeding Agent Community")

        try:
            # Import and run seed_agents
            from scripts.seed_agents import main as seed_agents_main

            await seed_agents_main()
            return True

        except Exception as e:
            self.logger.error("agent_seeding_failed", error=str(e))
            print(f"❌ Agent seeding failed: {e}")
            return False

    async def run_simulation(self) -> bool:
        """
        Run multi-agent simulation.

        Returns:
            True if successful
        """
        self.print_banner(f"Running Simulation ({self.simulation_steps} steps)")

        try:
            from scripts.run_simulation import Simulation, SimulationConfig

            # Configure simulation
            config = SimulationConfig(
                num_steps=self.simulation_steps,
                step_duration=self.simulation_duration,
                learning_probability=0.7,
                teaching_probability=0.3,
                research_probability=0.4,
                collaboration_probability=0.2,
                promotion_check_interval=10,
                save_interval=20,
                enable_workflows=False,  # Simplified for initial run
            )

            simulation = Simulation(config)

            # Initialize
            await simulation.initialize()

            # Run
            results = await simulation.run()

            # Print summary
            print("\n" + "=" * 80)
            print(" SIMULATION RESULTS")
            print("=" * 80)
            print(f"\n✅ Completed {results['steps_completed']} steps")
            print(f"   Duration: {results['duration']:.2f} seconds")
            print("\nActivity Statistics:")
            for key, value in results["activity_stats"].items():
                print(f"   {key}: {value}")
            print("\nCommunity Statistics:")
            print(f"   Total agents: {results['community_stats']['total_agents']}")
            print(f"   Active agents: {results['community_stats']['active_agents']}")
            print(
                f"   Average reputation: {results['community_stats']['avg_reputation']:.2f}"
            )
            print("\nAgents by stage:")
            for stage, count in results["community_stats"]["agents_by_stage"].items():
                print(f"   {stage}: {count}")
            print()

            # Cleanup
            await simulation.cleanup()

            return True

        except Exception as e:
            self.logger.error("simulation_failed", error=str(e))
            print(f"❌ Simulation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def analyze_community(self) -> bool:
        """
        Analyze community and generate report.

        Returns:
            True if successful
        """
        self.print_banner("Analyzing Community")

        try:
            from datetime import datetime

            from scripts.analyze_community import CommunityAnalyzer

            analyzer = CommunityAnalyzer()

            # Connect to storage
            await analyzer.state_store.connect()
            await analyzer.graph_store.connect()

            # Generate report
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_path = Path("reports") / f"community_report_{timestamp}.txt"

            report = await analyzer.generate_report(output_path=report_path)

            # Print report
            print(report)

            print(f"\n✅ Report saved to: {report_path}")

            # Cleanup
            await analyzer.state_store.disconnect()
            await analyzer.graph_store.disconnect()

            return True

        except Exception as e:
            self.logger.error("analysis_failed", error=str(e))
            print(f"❌ Analysis failed: {e}")
            return False

    async def run(self) -> bool:
        """
        Run the complete workflow.

        Returns:
            True if all steps successful
        """
        self.print_banner("Research Collective - Master Runner")

        print("Configuration:")
        print(f"  Skip Docker check: {self.skip_docker}")
        print(f"  Skip data seeding: {self.skip_seed}")
        print(f"  Simulation steps: {self.simulation_steps}")
        print(f"  Step duration: {self.simulation_duration}s")
        print()

        # Step 1: Check Docker
        if not self.check_docker():
            print("\n❌ Docker infrastructure check failed")
            print("   Please ensure Docker is running and services are up")
            return False

        # Step 2: Seed knowledge graph
        if not await self.seed_knowledge():
            print("\n❌ Knowledge seeding failed")
            return False

        # Step 3: Seed agents
        if not await self.seed_agents():
            print("\n❌ Agent seeding failed")
            return False

        # Step 4: Run simulation
        if not await self.run_simulation():
            print("\n❌ Simulation failed")
            return False

        # Step 5: Analyze and report
        if not await self.analyze_community():
            print("\n❌ Analysis failed")
            return False

        # Success!
        self.print_banner("✅ All Steps Completed Successfully!")

        print("Summary:")
        print("  1. ✅ Docker infrastructure checked")
        print("  2. ✅ Knowledge graph seeded")
        print("  3. ✅ Agent community seeded")
        print("  4. ✅ Simulation completed")
        print("  5. ✅ Community analysis generated")
        print()
        print("Next steps:")
        print("  - Review the generated report in reports/")
        print("  - Read documentation in docs/ folder")
        print("  - Adjust simulation parameters and run again")
        print("  - Explore the Neo4j browser at http://localhost:7474")
        print("  - Query PostgreSQL for agent states")
        print()

        return True


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Master runner for Research Collective"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker infrastructure check",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip data seeding (use existing data)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of simulation steps (default: 50)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.5,
        help="Duration of each step in seconds (default: 0.5)",
    )

    args = parser.parse_args()

    runner = MasterRunner(
        skip_docker=args.skip_docker,
        skip_seed=args.skip_seed,
        simulation_steps=args.steps,
        simulation_duration=args.duration,
    )

    try:
        success = await runner.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
