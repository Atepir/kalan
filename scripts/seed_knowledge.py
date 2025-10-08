"""
Seed knowledge graph with initial concepts and relationships.

Populates Neo4j with research topics, concepts, and their relationships
to bootstrap the knowledge base.
"""

import asyncio
from pathlib import Path
from typing import Any

import yaml

from src.storage.graph_store import get_graph_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def load_knowledge_templates() -> dict[str, Any]:
    """
    Load knowledge templates from YAML configuration.

    Returns:
        Dictionary with concepts and relationships
    """
    config_path = Path("config/knowledge_graph.yaml")

    if not config_path.exists():
        logger.warning(f"Knowledge templates file not found: {config_path}")
        return {}

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return data


async def create_concept_hierarchy(
    graph_store,
    concepts: list[dict],
) -> dict[str, str]:
    """
    Create concept nodes and hierarchy.

    Args:
        graph_store: Graph store instance
        concepts: List of concept dictionaries

    Returns:
        Mapping of concept names to node IDs
    """
    concept_ids = {}

    for concept_data in concepts:
        name = concept_data["name"]
        category = concept_data.get("category", "general")
        description = concept_data.get("description", "")
        difficulty = concept_data.get("difficulty", 1)

        # Create concept node
        node_id = await graph_store.create_node(
            "Concept",
            {
                "name": name,
                "category": category,
                "description": description,
                "difficulty": difficulty,
            },
        )

        concept_ids[name] = node_id

        logger.info(
            "concept_created",
            name=name,
            category=category,
            node_id=node_id,
        )

    return concept_ids


async def create_concept_relationships(
    graph_store,
    relationships: list[dict],
    concept_ids: dict[str, str],
) -> int:
    """
    Create relationships between concepts.

    Args:
        graph_store: Graph store instance
        relationships: List of relationship dictionaries
        concept_ids: Mapping of concept names to node IDs

    Returns:
        Number of relationships created
    """
    count = 0

    for rel_data in relationships:
        source = rel_data["source"]
        target = rel_data["target"]
        rel_type = rel_data.get("type", "RELATES_TO")

        if source not in concept_ids or target not in concept_ids:
            logger.warning(
                "concept_not_found_for_relationship",
                source=source,
                target=target,
            )
            continue

        # Create relationship
        await graph_store.create_relationship(
            source_id=concept_ids[source],
            target_id=concept_ids[target],
            relationship_type=rel_type,
            properties=rel_data.get("properties", {}),
        )

        count += 1

        logger.info(
            "relationship_created",
            source=source,
            target=target,
            type=rel_type,
        )

    return count


async def seed_knowledge_from_templates() -> tuple[int, int]:
    """
    Seed knowledge from template files.

    Returns:
        Tuple of (concepts_created, relationships_created)
    """
    logger.info("seeding_knowledge_from_templates")

    graph_store = get_graph_store()
    await graph_store.connect()

    # Load templates
    templates = await load_knowledge_templates()

    if not templates:
        logger.warning("no_knowledge_templates_found")
        return 0, 0

    # Create concepts
    concepts = templates.get("concepts", [])
    concept_ids = await create_concept_hierarchy(graph_store, concepts)

    # Create relationships
    relationships = templates.get("relationships", [])
    rel_count = await create_concept_relationships(
        graph_store, relationships, concept_ids
    )

    logger.info(
        "knowledge_seeding_from_templates_completed",
        concepts=len(concept_ids),
        relationships=rel_count,
    )

    return len(concept_ids), rel_count


async def seed_default_knowledge() -> tuple[int, int]:
    """
    Seed default knowledge hierarchy if no templates found.

    Returns:
        Tuple of (concepts_created, relationships_created)
    """
    logger.info("seeding_default_knowledge")

    graph_store = get_graph_store()
    await graph_store.connect()

    # Default concept hierarchy for ML research
    concepts = [
        # Core ML concepts
        {
            "name": "machine learning",
            "category": "core",
            "description": "The study of algorithms that improve through experience",
            "difficulty": 1,
        },
        {
            "name": "supervised learning",
            "category": "paradigm",
            "description": "Learning from labeled examples",
            "difficulty": 2,
        },
        {
            "name": "unsupervised learning",
            "category": "paradigm",
            "description": "Learning patterns from unlabeled data",
            "difficulty": 2,
        },
        {
            "name": "reinforcement learning",
            "category": "paradigm",
            "description": "Learning through interaction with an environment",
            "difficulty": 3,
        },
        # Deep learning
        {
            "name": "deep learning",
            "category": "technique",
            "description": "Neural networks with multiple layers",
            "difficulty": 3,
        },
        {
            "name": "neural networks",
            "category": "model",
            "description": "Computing systems inspired by biological neural networks",
            "difficulty": 2,
        },
        {
            "name": "convolutional neural networks",
            "category": "model",
            "description": "Neural networks designed for processing grid-like data",
            "difficulty": 3,
        },
        {
            "name": "recurrent neural networks",
            "category": "model",
            "description": "Neural networks for sequential data",
            "difficulty": 3,
        },
        {
            "name": "transformers",
            "category": "model",
            "description": "Attention-based neural network architecture",
            "difficulty": 4,
        },
        # Applications
        {
            "name": "natural language processing",
            "category": "application",
            "description": "Processing and understanding human language",
            "difficulty": 3,
        },
        {
            "name": "computer vision",
            "category": "application",
            "description": "Enabling computers to understand visual information",
            "difficulty": 3,
        },
        # Optimization
        {
            "name": "optimization",
            "category": "technique",
            "description": "Finding the best solution from all feasible solutions",
            "difficulty": 2,
        },
        {
            "name": "gradient descent",
            "category": "algorithm",
            "description": "Iterative optimization algorithm",
            "difficulty": 2,
        },
        # Fundamentals
        {
            "name": "statistics",
            "category": "foundation",
            "description": "Mathematical study of data collection and analysis",
            "difficulty": 1,
        },
        {
            "name": "linear algebra",
            "category": "foundation",
            "description": "Study of vectors and linear transformations",
            "difficulty": 1,
        },
        {
            "name": "probability",
            "category": "foundation",
            "description": "Mathematical study of uncertainty",
            "difficulty": 1,
        },
    ]

    # Create concepts
    concept_ids = await create_concept_hierarchy(graph_store, concepts)

    # Default relationships
    relationships = [
        # ML paradigms
        {"source": "supervised learning", "target": "machine learning", "type": "IS_A"},
        {"source": "unsupervised learning", "target": "machine learning", "type": "IS_A"},
        {"source": "reinforcement learning", "target": "machine learning", "type": "IS_A"},
        # Deep learning hierarchy
        {"source": "deep learning", "target": "machine learning", "type": "IS_A"},
        {"source": "neural networks", "target": "deep learning", "type": "ENABLES"},
        {"source": "convolutional neural networks", "target": "neural networks", "type": "IS_A"},
        {"source": "recurrent neural networks", "target": "neural networks", "type": "IS_A"},
        {"source": "transformers", "target": "neural networks", "type": "IS_A"},
        # Applications
        {"source": "natural language processing", "target": "machine learning", "type": "APPLIES"},
        {"source": "computer vision", "target": "machine learning", "type": "APPLIES"},
        {"source": "transformers", "target": "natural language processing", "type": "USED_IN"},
        {"source": "convolutional neural networks", "target": "computer vision", "type": "USED_IN"},
        # Optimization
        {"source": "optimization", "target": "machine learning", "type": "ENABLES"},
        {"source": "gradient descent", "target": "optimization", "type": "IS_A"},
        {"source": "gradient descent", "target": "neural networks", "type": "TRAINS"},
        # Foundations
        {"source": "statistics", "target": "machine learning", "type": "PREREQUISITE"},
        {"source": "linear algebra", "target": "machine learning", "type": "PREREQUISITE"},
        {"source": "probability", "target": "machine learning", "type": "PREREQUISITE"},
        {"source": "linear algebra", "target": "neural networks", "type": "PREREQUISITE"},
    ]

    # Create relationships
    rel_count = await create_concept_relationships(
        graph_store, relationships, concept_ids
    )

    logger.info(
        "default_knowledge_seeded",
        concepts=len(concept_ids),
        relationships=rel_count,
    )

    return len(concept_ids), rel_count


async def print_knowledge_summary(concepts_count: int, relationships_count: int) -> None:
    """
    Print summary of seeded knowledge.

    Args:
        concepts_count: Number of concepts created
        relationships_count: Number of relationships created
    """
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH SUMMARY")
    print("=" * 60)

    print(f"\nConcepts created: {concepts_count}")
    print(f"Relationships created: {relationships_count}")

    # Query some sample concepts
    graph_store = get_graph_store()

    # Get concepts by category
    query = """
    MATCH (c:Concept)
    RETURN c.category as category, count(*) as count
    ORDER BY count DESC
    """
    try:
        results = await graph_store.query(query)
        print(f"\nConcepts by category:")
        for record in results:
            print(f"  {record['category']}: {record['count']}")
    except Exception as e:
        logger.error("failed_to_query_categories", error=str(e))

    # Get relationship types
    query = """
    MATCH ()-[r]->()
    RETURN type(r) as rel_type, count(*) as count
    ORDER BY count DESC
    """
    try:
        results = await graph_store.query(query)
        print(f"\nRelationship types:")
        for record in results:
            print(f"  {record['rel_type']}: {record['count']}")
    except Exception as e:
        logger.error("failed_to_query_relationships", error=str(e))

    print("\n" + "=" * 60 + "\n")


async def main():
    """Main entry point."""
    logger.info("seed_knowledge_script_started")

    try:
        # Try to load from templates
        concepts, relationships = await seed_knowledge_from_templates()

        # If no templates found, use defaults
        if concepts == 0:
            logger.info("using_default_knowledge")
            concepts, relationships = await seed_default_knowledge()

        # Print summary
        await print_knowledge_summary(concepts, relationships)

        logger.info(
            "seed_knowledge_script_completed",
            concepts=concepts,
            relationships=relationships,
        )

    except Exception as e:
        logger.error("seed_knowledge_script_failed", error=str(e))
        raise
    finally:
        # Cleanup
        graph_store = get_graph_store()
        await graph_store.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
