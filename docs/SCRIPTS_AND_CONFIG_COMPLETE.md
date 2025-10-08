# Scripts and Configuration - Complete ✅

## Overview

The scripts and configuration system provides tools to initialize, run, and analyze the Research Collective. It includes:
- **Scripts**: Python scripts for seeding data, running simulations, and generating reports
- **Configuration**: YAML files defining agent templates, knowledge graphs, curricula, and evaluation rubrics

---

## Scripts

### 1. `seed_agents.py` (350 lines)

**Purpose**: Seed initial agents into the community from templates.

**Usage**:
```bash
python scripts/seed_agents.py
```

**Features**:
- Loads agent templates from `config/agent_templates.yaml`
- Creates agents with predefined knowledge and reputation
- Registers agents with the community
- Falls back to default agents if no templates found
- Prints summary of created agents

**Example Output**:
```
=============================================================
SEEDED AGENTS SUMMARY
=============================================================

APPRENTICE (5 agents):
  - Alice (machine learning)
    Topics: python, statistics, machine learning
    Reputation: 1.00
  - Bob (natural language processing)
    Topics: python, linguistics, NLP
    Reputation: 1.00
  ...

TEACHER (2 agents):
  - Ivy (machine learning)
    Topics: supervised learning, ensemble methods, feature engineering
    Reputation: 2.50
  ...

=============================================================
TOTAL: 12 agents
=============================================================

Community Statistics:
  Total agents: 12
  Active agents: 12
  Average reputation: 1.73
```

**Functions**:
- `load_agent_templates()`: Load from YAML
- `create_agent_from_template()`: Instantiate agent
- `seed_agents()`: Create and register agents
- `seed_default_agents()`: Fallback defaults
- `print_agent_summary()`: Pretty print summary

---

### 2. `seed_knowledge.py` (400 lines)

**Purpose**: Populate Neo4j knowledge graph with concepts and relationships.

**Usage**:
```bash
python scripts/seed_knowledge.py
```

**Features**:
- Loads knowledge graph from `config/knowledge_graph.yaml`
- Creates concept nodes with categories and difficulty
- Creates relationships (IS_A, PREREQUISITE, ENABLES, etc.)
- Falls back to default ML knowledge hierarchy
- Queries and displays statistics

**Example Output**:
```
=============================================================
KNOWLEDGE GRAPH SUMMARY
=============================================================

Concepts created: 36
Relationships created: 45

Concepts by category:
  model: 10
  technique: 8
  foundation: 5
  paradigm: 4
  application: 4
  algorithm: 5

Relationship types:
  IS_A: 15
  PREREQUISITE: 8
  ENABLES: 7
  USED_IN: 10
  EXTENDS: 5

=============================================================
```

**Functions**:
- `load_knowledge_templates()`: Load from YAML
- `create_concept_hierarchy()`: Create concept nodes
- `create_concept_relationships()`: Link concepts
- `seed_knowledge_from_templates()`: Template-based seeding
- `seed_default_knowledge()`: Fallback ML hierarchy
- `print_knowledge_summary()`: Display stats

**Default Knowledge Hierarchy** (if no templates):
- Foundations: mathematics, statistics, probability, linear algebra, calculus
- Core ML: machine learning, supervised/unsupervised/reinforcement learning
- Deep Learning: neural networks, CNNs, RNNs, transformers
- Optimization: gradient descent, backpropagation, Adam
- Applications: NLP, computer vision, speech recognition
- Advanced: transfer learning, meta-learning, generative models

---

### 3. `run_simulation.py` (450 lines)

**Purpose**: Run multi-agent research simulation with coordinated activities.

**Usage**:
```bash
python scripts/run_simulation.py
```

**Features**:
- Configurable simulation parameters
- Orchestrates learning, teaching, research, collaboration
- Activity assignment based on developmental stage
- Periodic promotion checks
- State persistence
- Real-time statistics

**SimulationConfig**:
```python
config = SimulationConfig(
    num_steps=100,              # Number of simulation steps
    step_duration=1.0,          # Seconds per step
    learning_probability=0.7,   # P(learn) per step
    teaching_probability=0.3,   # P(teach) per step
    research_probability=0.4,   # P(research) per step
    collaboration_probability=0.2,  # P(collaborate) per step
    promotion_check_interval=10,    # Steps between promotions
    save_interval=20,           # Steps between saves
    enable_workflows=True,      # Use LangGraph workflows
)
```

**Example Output**:
```
=============================================================
SIMULATION RESULTS
=============================================================

Steps completed: 50
Duration: 25.34 seconds

Activity Statistics:
  total_learning: 245
  total_teaching: 89
  total_research: 134
  total_collaborations: 34
  total_promotions: 7

Community Statistics:
  Total agents: 12
  Active agents: 12
  Average reputation: 2.15

Agents by stage:
  apprentice: 2
  practitioner: 6
  teacher: 3
  researcher: 1

=============================================================
```

**Activity Assignment Logic**:
- **Apprentice/Practitioner**: Focus on learning (70% probability)
- **Teacher**: Teaching (30%) + Research (40%)
- **Researcher/Expert**: Research (40%) + Collaboration (20%)

**Functions**:
- `initialize()`: Connect to storage
- `step()`: Execute one simulation step
- `_learning_task()`: Learning activity
- `_teaching_task()`: Teaching activity
- `_research_task()`: Research activity
- `_collaboration_task()`: Collaboration activity
- `_check_promotions()`: Promote eligible agents
- `_save_state()`: Persist to database
- `run()`: Complete simulation loop
- `stop()`: Graceful shutdown
- `cleanup()`: Resource cleanup

---

### 4. `analyze_community.py` (500 lines)

**Purpose**: Analyze community dynamics and generate comprehensive reports.

**Usage**:
```bash
python scripts/analyze_community.py
```

**Features**:
- Agent progression analysis
- Learning pattern analysis
- Mentorship network analysis
- Research productivity metrics
- Collaboration patterns
- Knowledge diffusion tracking
- Community health metrics
- Exportable text reports

**Example Output**:
```
================================================================================
RESEARCH COLLECTIVE - COMMUNITY ANALYSIS REPORT
Generated: 2025-10-08T15:30:45.123456
================================================================================

## COMMUNITY HEALTH
Total Agents: 12
Active Agents: 12
Average Reputation: 2.15
Activity Rate: 34.25 events/agent
Inactive Agents: 0
Specialization Diversity: 0.75
Number of Specializations: 9

## AGENT PROGRESSION
Total Promotions: 7
Stage Transitions:
  apprentice → practitioner: 4
  practitioner → teacher: 2
  teacher → researcher: 1

Current Distribution:
  apprentice: 2
  practitioner: 6
  teacher: 3
  researcher: 1

## LEARNING PATTERNS
Total Papers Read: 245
Active Learners: 10
Help Requests: 42
Help Rate: 17.14%
Comprehension Distribution:
  excellent: 67
  good: 98
  partial: 58
  minimal: 22

## MENTORSHIP NETWORK
Active Mentorships: 15
Unique Mentors: 5
Unique Students: 8
Total Sessions: 89
Recent Teaching Events: 78

## RESEARCH PRODUCTIVITY
Total Experiments: 134
Successful: 102
Failed: 32
Success Rate: 76.12%
Papers Submitted: 12
Reviews Submitted: 23
Active Researchers: 6

## COLLABORATION PATTERNS
Proposed: 45
Accepted: 34
Completed: 28
Acceptance Rate: 75.56%
Completion Rate: 82.35%
Total Collaborations: 67
Unique Collaborators: 9

## KNOWLEDGE DIFFUSION
Total Learning Events: 312
Unique Concepts Learned: 28
Most Learned Concepts:
  machine learning: 45
  neural networks: 38
  optimization: 32
  ...

================================================================================
```

**Analysis Functions**:
- `analyze_agent_progression()`: Track stage transitions
- `analyze_learning_patterns()`: Comprehension and help-seeking
- `analyze_mentorship_network()`: Mentor-student relationships
- `analyze_research_productivity()`: Experiments and publications
- `analyze_collaboration_patterns()`: Collaboration networks
- `analyze_knowledge_diffusion()`: Concept spread through community
- `analyze_community_health()`: Overall health metrics
- `generate_report()`: Comprehensive report generation

**Metrics Tracked**:
- Papers read, comprehension levels, help rate
- Teaching sessions, mentorship relationships
- Experiments run, success rate, papers published
- Collaborations proposed/accepted/completed
- Concept learning events, knowledge depth distribution
- Agent activity rate, specialization diversity

---

## Configuration Files

### 1. `config/agent_templates.yaml`

**Purpose**: Define initial agent templates for seeding.

**Structure**:
```yaml
agents:
  - name: "Alice"
    stage: "apprentice"
    specialization: "machine learning"
    model: "llama3.1:8b"
    knowledge:
      - name: "python"
        depth: 1
        confidence: 0.6
      - name: "statistics"
        depth: 1
        confidence: 0.5
    reputation:
      score: 1.0
      teaching_count: 0
      review_count: 0
```

**Included Agents** (12 total):
- **5 Apprentices**: Alice (ML), Bob (NLP), Carol (CV), Dave (RL), Eve (Optimization)
- **3 Practitioners**: Frank (Deep Learning), Grace (Neural Networks), Hank (Transfer Learning)
- **2 Teachers**: Ivy (ML), Jack (Statistics)
- **2 Researchers**: Karen (Meta-Learning), Leo (Generative Models)

**Fields**:
- `name`: Agent display name
- `stage`: Developmental stage (apprentice/practitioner/teacher/researcher/expert)
- `specialization`: Research specialization
- `model`: Preferred Ollama model
- `knowledge`: Initial topics with depth and confidence
- `reputation`: Initial reputation metrics

---

### 2. `config/knowledge_graph.yaml`

**Purpose**: Define concept hierarchy and relationships for Neo4j.

**Structure**:
```yaml
concepts:
  - name: "machine learning"
    category: "core"
    description: "Study of algorithms that improve through experience"
    difficulty: 2

relationships:
  - source: "statistics"
    target: "machine learning"
    type: "PREREQUISITE"
```

**Included Concepts** (36 total):
- **Foundations** (5): mathematics, statistics, probability, linear algebra, calculus
- **Core ML** (4): machine learning, supervised/unsupervised/RL/semi-supervised
- **Deep Learning** (6): neural networks, CNNs, RNNs, transformers, attention
- **Optimization** (5): gradient descent, backpropagation, SGD, Adam
- **Regularization** (3): regularization, dropout, batch norm
- **Applications** (4): NLP, computer vision, speech recognition, recommender systems
- **Advanced** (7): transfer learning, meta-learning, few-shot, GANs, VAEs, diffusion

**Relationship Types**:
- `PREREQUISITE`: Required prior knowledge
- `IS_A`: Subclass relationship
- `ENABLES`: One concept enables another
- `USED_IN`: Used in application/technique
- `APPLIES`: Application of concept
- `EXTENDS`: Extension/advancement
- `TRAINS`: Training method

**Included Relationships** (45 total): Complete concept graph connecting all nodes

---

### 3. `config/curricula/machine_learning.yaml`

**Purpose**: Define learning path for ML specialization.

**Structure**:
```yaml
curriculum:
  name: "Machine Learning Fundamentals"
  specialization: "machine learning"
  
  stages:
    - stage: "apprentice"
      duration_steps: 50
      learning_goals:
        - "Understand basic ML concepts"
        - "Learn Python programming"
      
      topics:
        - name: "python"
          priority: "high"
          depth_target: 2
          papers:
            - "Python for Data Science"
      
      activities:
        - type: "read_papers"
          frequency: "high"
          count: 10
```

**Stages Covered**:
- **Apprentice** (50 steps): Python, statistics, linear algebra, ML basics
- **Practitioner** (75 steps): Supervised/unsupervised learning, optimization, evaluation
- **Teacher** (100 steps): Ensemble methods, feature engineering, deep learning, Bayesian methods
- **Researcher** (150 steps): Advanced topics, meta-learning, transfer learning, novel research

**For Each Stage**:
- Duration in simulation steps
- Learning goals
- Topics with priority, depth target, recommended papers
- Activities with frequency and count targets

---

### 4. `config/curricula/deep_learning.yaml`

**Purpose**: Define learning path for deep learning specialization.

**Structure**: Same as ML curriculum

**Stages Covered**:
- **Apprentice** (50 steps): Neural networks, backpropagation, gradient descent
- **Practitioner** (75 steps): CNNs, RNNs, regularization, optimization
- **Teacher** (100 steps): Transformers, generative models, CV, NLP
- **Researcher** (150 steps): NAS, foundation models, efficient DL, self-supervised learning

**Resources**:
- Textbooks: Deep Learning (Goodfellow et al.), d2l.ai
- Courses: CS231n, CS224n, Fast.ai
- Frameworks: PyTorch, TensorFlow, JAX
- Papers: arXiv cs.CV, cs.CL, ICLR, NeurIPS

---

### 5. `config/evaluation_rubrics.yaml`

**Purpose**: Define evaluation criteria for activities and promotions.

**Rubrics Included**:

**Paper Comprehension**:
- Levels: none (0.0), minimal (0.25), partial (0.5), good (0.75), excellent (1.0)
- Criteria: Understanding contribution, methodology, results, limitations

**Teaching Effectiveness**:
- Dimensions: clarity (30%), accuracy (30%), engagement (20%), adaptation (20%)
- Overall thresholds: excellent (0.85), good (0.7), fair (0.5)

**Research Quality**:
- Dimensions: novelty (25%), methodology (25%), results (20%), clarity (15%), impact (15%)
- Weighted average calculation

**Peer Review Quality**:
- Dimensions: thoroughness (30%), constructiveness (25%), accuracy (25%), insight (20%)
- Criteria for each dimension

**Experiment Design**:
- Dimensions: hypothesis (20%), methodology (25%), controls (20%), metrics (15%), reproducibility (20%)

**Promotion Thresholds**:
```yaml
promotion_thresholds:
  apprentice_to_practitioner:
    papers_read: 10
    comprehension_avg: 0.6
    help_received: 3
    min_reputation: 1.2
  
  practitioner_to_teacher:
    papers_read: 25
    comprehension_avg: 0.75
    experiments_conducted: 5
    papers_reviewed: 2
    min_reputation: 1.8
  
  teacher_to_researcher:
    papers_read: 50
    teaching_sessions: 10
    experiments_conducted: 15
    papers_written: 2
    reviews_conducted: 5
    min_reputation: 2.5
  
  researcher_to_expert:
    papers_written: 10
    high_quality_papers: 3
    collaborations_led: 5
    successful_experiments: 25
    reviews_conducted: 15
    min_reputation: 4.0
```

---

## Usage Workflows

### Complete System Initialization

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Seed knowledge graph
python scripts/seed_knowledge.py

# 3. Seed agents
python scripts/seed_agents.py

# 4. Run simulation
python scripts/run_simulation.py

# 5. Analyze results
python scripts/analyze_community.py
```

### Custom Simulation

```python
from scripts.run_simulation import Simulation, SimulationConfig

# Configure
config = SimulationConfig(
    num_steps=200,
    step_duration=0.5,
    learning_probability=0.8,
    enable_workflows=True,
)

# Run
simulation = Simulation(config)
await simulation.initialize()
results = await simulation.run()
await simulation.cleanup()
```

### Analysis Pipeline

```python
from scripts.analyze_community import CommunityAnalyzer
from pathlib import Path

analyzer = CommunityAnalyzer()
await analyzer.state_store.connect()
await analyzer.graph_store.connect()

# Generate report
report = await analyzer.generate_report(
    output_path=Path("reports/analysis.txt")
)

print(report)
```

---

## Directory Structure

```
project-kalan/
├── scripts/
│   ├── seed_agents.py           # 350 lines
│   ├── seed_knowledge.py        # 400 lines
│   ├── run_simulation.py        # 450 lines
│   └── analyze_community.py     # 500 lines
│
├── config/
│   ├── agent_templates.yaml     # 12 agent templates
│   ├── knowledge_graph.yaml     # 36 concepts, 45 relationships
│   ├── evaluation_rubrics.yaml  # 5 rubrics, promotion thresholds
│   └── curricula/
│       ├── machine_learning.yaml    # ML curriculum (4 stages)
│       └── deep_learning.yaml       # DL curriculum (4 stages)
│
└── reports/                     # Generated by analyze_community.py
    └── community_report_*.txt
```

---

## Performance Considerations

### Simulation Performance

- **Step Duration**: Balance between realism and speed
  - Production: 1.0-2.0 seconds per step
  - Development: 0.1-0.5 seconds per step
  - Fast testing: 0.0 seconds (no delay)

- **Activity Probabilities**: Tune for desired behavior
  - High learning (0.7-0.9) for skill development
  - Moderate teaching (0.3-0.5) for knowledge transfer
  - Balanced research (0.4-0.6) for productivity

- **Save Intervals**: Balance persistence and performance
  - Frequent (every 10 steps): High reliability, slower
  - Moderate (every 20-50 steps): Balanced
  - Infrequent (every 100 steps): Fast, some risk

### Analysis Performance

- **Event History**: Grows linearly with simulation length
  - Use `limit` parameter for recent events
  - Clear history periodically if memory constrained

- **Graph Queries**: Can be slow with large graphs
  - Use indexes on frequently queried properties
  - Limit query depth and result count
  - Cache frequent queries

---

## Extension Points

### Adding New Curricula

1. Create `config/curricula/my_specialization.yaml`
2. Define stages with topics and activities
3. Add prerequisites and resources
4. Reference in seed_agents.py

### Custom Analysis Metrics

```python
async def analyze_custom_metric(self) -> dict[str, Any]:
    """Add to CommunityAnalyzer class."""
    # Query events, graph, state
    # Calculate metrics
    return {"metric_name": value}

# Add to generate_report()
custom = await self.analyze_custom_metric()
report_lines.append(f"Custom Metric: {custom['metric_name']}")
```

### Simulation Extensions

```python
# Add new activity type
async def _custom_activity_task(self, agent: Agent, stats: dict) -> None:
    """Add to Simulation class."""
    # Implement custom activity
    stats["custom_activities"] += 1

# Schedule in step()
if random.random() < self.config.custom_probability:
    tasks.append(self._custom_activity_task(agent, stats))
```

---

## Summary

The scripts and configuration system provides:

✅ **Scripts** (~1,700 lines):
- `seed_agents.py`: Initialize agent community
- `seed_knowledge.py`: Populate knowledge graph
- `run_simulation.py`: Multi-agent simulation engine
- `analyze_community.py`: Comprehensive analytics

✅ **Configuration** (~1,500 lines YAML):
- `agent_templates.yaml`: 12 diverse agents
- `knowledge_graph.yaml`: 36 concepts, 45 relationships
- `evaluation_rubrics.yaml`: 5 rubrics, promotion criteria
- `curricula/machine_learning.yaml`: 4-stage ML path
- `curricula/deep_learning.yaml`: 4-stage DL path

**Total**: ~3,200 lines enabling complete system operation

This completes the infrastructure needed to initialize, run, and analyze the Research Collective!

---

## Next Steps

The only remaining task is:
- **Data structure**: Create `data/` directory with seed data files (JSON/YAML format)
