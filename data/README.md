# Data Directory

This directory contains seed data, papers, experiments, and other persistent data for the Research Collective.

## Structure

```
data/
├── seed_agents/          # Sample agent definitions (JSON)
│   ├── apprentices.json  # Beginner agents
│   ├── practitioners.json # Intermediate agents
│   └── advanced.json     # Teachers, researchers, experts
│
├── seed_knowledge/       # Sample knowledge concepts (JSON)
│   ├── foundations.json  # Math, stats, programming
│   ├── core_ml.json      # Core ML concepts
│   ├── deep_learning.json # DL concepts
│   └── advanced.json     # Meta-learning, transfer learning
│
├── papers/               # Stored research papers
│   └── .gitkeep         # Papers stored by document_store
│
├── experiments/          # Experiment results and code
│   └── .gitkeep         # Experiments stored here
│
└── README.md            # This file
```

## Usage

### Seed Agents

Agent definition files can be loaded by `scripts/seed_agents.py`:
- Defines agent name, stage, specialization, knowledge
- JSON format for easy parsing
- Organized by developmental stage

### Seed Knowledge

Knowledge concept files can be loaded by `scripts/seed_knowledge.py`:
- Defines concepts with categories and difficulty
- Can include relationships between concepts
- Organized by knowledge domain

### Papers

Papers are stored in the `papers/` directory by the document store:
- Organized in sharded subdirectories (first 2 chars of ID)
- Each paper has metadata JSON and content file
- Managed automatically by `src/storage/document_store.py`

### Experiments

Experiment results are stored in `experiments/`:
- Code, outputs, metrics
- Linked to agent and timestamp
- Can be analyzed for research insights

## Data Formats

### Agent Definition (JSON)

```json
{
  "name": "Alice",
  "stage": "apprentice",
  "specialization": "machine learning",
  "model": "llama3.1:8b",
  "knowledge": [
    {
      "topic": "python",
      "depth": 1,
      "confidence": 0.7
    }
  ],
  "reputation": {
    "score": 1.0,
    "teaching_count": 0
  }
}
```

### Concept Definition (JSON)

```json
{
  "name": "machine learning",
  "category": "core",
  "description": "Study of algorithms that improve through experience",
  "difficulty": 2,
  "prerequisites": ["statistics", "linear algebra"],
  "related_concepts": ["deep learning", "supervised learning"]
}
```

## Notes

- All JSON files should be valid and parseable
- UTF-8 encoding required
- Use consistent naming conventions
- Keep file sizes reasonable (<1MB per file)
