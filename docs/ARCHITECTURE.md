# MCP Research Collective - System Architecture

## Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        🎯 MASTER RUN SCRIPT (run.py)                         │
│                     Orchestrates Complete Workflow                           │
└────────────────┬────────────────────────────────────────────────────────────┘
                 │
                 ├─► 1. Check Docker Infrastructure
                 ├─► 2. Seed Knowledge Graph (31 concepts)
                 ├─► 3. Seed Agent Community (12 agents)
                 ├─► 4. Run Simulation (50 steps default)
                 └─► 5. Generate Analysis Report
                 
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         🐳 DOCKER INFRASTRUCTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ PostgreSQL   │  │    Neo4j     │  │   Qdrant     │  │    Redis     │   │
│  │  +pgvector   │  │  Graph DB    │  │  Vector DB   │  │   Cache      │   │
│  │              │  │              │  │              │  │              │   │
│  │ Agent State  │  │ Knowledge    │  │ Embeddings   │  │ Metrics      │   │
│  │ Papers       │  │ Graph        │  │ Semantic     │  │ Queues       │   │
│  │ Sessions     │  │ Prereqs      │  │ Search       │  │ Sessions     │   │
│  │              │  │              │  │              │  │              │   │
│  │ Port: 5432   │  │ Port: 7474   │  │ Port: 6333   │  │ Port: 6379   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐                                         │
│  │   Ollama     │  │   Adminer    │                                         │
│  │   LLM API    │  │   DB UI      │                                         │
│  │              │  │              │                                         │
│  │ 4 Models:    │  │ PostgreSQL   │                                         │
│  │ - llama3.1   │  │ Admin        │                                         │
│  │ - mistral    │  │              │                                         │
│  │ - phi3       │  │              │                                         │
│  │ - codellama  │  │ Port: 8081   │                                         │
│  │              │  │              │                                         │
│  │ Port: 11434  │  └──────────────┘                                         │
│  └──────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                          🤖 MULTI-AGENT SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                     Community Orchestrator                          │     │
│  │  • Agent Coordination        • Resource Allocation                  │     │
│  │  • Matchmaking (mentor ↔ student)  • Event Management              │     │
│  │  • LangGraph Workflows       • Activity Scheduling                  │     │
│  └────────────┬───────────────────────────────────────────────────────┘     │
│               │                                                               │
│      ┌────────┴───────┬──────────────┬──────────────┬──────────────┐       │
│      │                │              │              │              │       │
│  ┌───▼────┐  ┌───────▼──┐  ┌───────▼──┐  ┌───────▼──┐  ┌────────▼───┐   │
│  │Apprentice│ │Practitioner│ │Researcher│ │ Teacher  │ │Contributor │   │
│  │ (5)     │ │    (3)    │ │   (2)    │ │   (1)    │ │    (1)     │   │
│  │         │ │           │ │          │ │          │ │            │   │
│  │Rep: 1.0+│ │ Rep: 2.0+ │ │Rep: 3.0+ │ │Rep: 3.5+ │ │ Rep: 4.0+  │   │
│  │         │ │           │ │          │ │          │ │            │   │
│  │Can:     │ │Can:       │ │Can:      │ │Can:      │ │Can:        │   │
│  │• Learn  │ │• Learn    │ │• Research│ │• Teach   │ │• All       │   │
│  │         │ │• Research │ │• Publish │ │• Mentor  │ │• Lead      │   │
│  │         │ │           │ │• Review  │ │• Review  │ │• Organize  │   │
│  └─────────┘ └───────────┘ └──────────┘ └──────────┘ └────────────┘   │
│                                                                               │
│  Total: 12 Agents                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                        🎓 KNOWLEDGE SYSTEM (31 Concepts)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Foundations (6)          Core ML (7)              Deep Learning (9)         │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐          │
│  │ Mathematics  │───────►│ Machine      │───────►│ Deep         │          │
│  │ Statistics   │        │ Learning     │        │ Learning     │          │
│  │ Probability  │        │ Supervised   │        │ Neural Nets  │          │
│  │ Linear Alg   │        │ Unsupervised │        │ CNNs         │          │
│  │ Calculus     │        │ Reinforcement│        │ RNNs         │          │
│  │ Python       │        │ Optimization │        │ Transformers │          │
│  └──────────────┘        │ Regularization│       │ Attention    │          │
│                          └──────────────┘        │ Dropout      │          │
│  Difficulty: 1                                   │ Batch Norm   │          │
│                          Difficulty: 2-3         └──────────────┘          │
│                                                                               │
│                                                   Difficulty: 2-4            │
│                                                                               │
│  Advanced Topics (9)                                                          │
│  ┌──────────────────────────────────────────────────────────┐               │
│  │ Transfer Learning    │ Meta-Learning      │ Few-Shot     │               │
│  │ Generative Models    │ GANs               │ VAEs         │               │
│  │ Diffusion Models     │ Neural Arch Search │ Self-Supervised│             │
│  └──────────────────────────────────────────────────────────┘               │
│                                                                               │
│  Difficulty: 4-5                                                              │
│                                                                               │
│  Graph Structure: 45 prerequisite relationships in Neo4j                      │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         🎯 ACTIVITY SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  LEARNING   │  │  TEACHING   │  │  RESEARCH   │  │   REVIEW    │       │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤       │
│  │             │  │             │  │             │  │             │       │
│  │• Read paper │  │• Give lesson│  │• Lit review │  │• Read paper │       │
│  │• Comprehend │  │• Assess     │  │• Form hypo  │  │• Evaluate   │       │
│  │• Ask Qs     │  │• Curriculum │  │• Experiment │  │• Critique   │       │
│  │• Practice   │  │• Feedback   │  │• Analyze    │  │• Score      │       │
│  │• Update     │  │• Verify     │  │• Write      │  │• Recommend  │       │
│  │  knowledge  │  │• Track      │  │• Publish    │  │             │       │
│  │             │  │  progress   │  │             │  │             │       │
│  │Probability: │  │             │  │Probability: │  │Triggered by:│       │
│  │    70%      │  │Probability: │  │    40%      │  │  publishing │       │
│  │             │  │    30%      │  │             │  │             │       │
│  │All stages   │  │Teacher+     │  │Practitioner+│  │Researcher+  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                               │
│  Each activity uses:                                                          │
│  • Ollama LLM (model selection based on task)                                │
│  • MCP servers (literature, experiments, knowledge, writing)                 │
│  • Storage layer (state, graph, vector, cache)                               │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                    🔧 MCP SERVER INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │ Literature Server│  │Experiments Server│  │ Knowledge Server │          │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│  │                  │  │                  │  │                  │          │
│  │• arXiv API       │  │• Python sandbox  │  │• Vector search   │          │
│  │• Semantic Scholar│  │• Code execution  │  │  (Qdrant)        │          │
│  │• Paper metadata  │  │• Data analysis   │  │• Graph queries   │          │
│  │• Citations       │  │• Result capture  │  │  (Neo4j)         │          │
│  │• Full text       │  │• Error handling  │  │• Concept lookup  │          │
│  │                  │  │• Timeout mgmt    │  │• Prereq chains   │          │
│  │                  │  │                  │  │                  │          │
│  │Used by:          │  │Used by:          │  │Used by:          │          │
│  │ Learning         │  │ Research         │  │ All activities   │          │
│  │ Research         │  │                  │  │                  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                               │
│  ┌──────────────────┐                                                        │
│  │  Writing Server  │                                                        │
│  ├──────────────────┤                                                        │
│  │                  │                                                        │
│  │• LaTeX generation│                                                        │
│  │• Paper structure │                                                        │
│  │• Citations       │                                                        │
│  │• Bibliography    │                                                        │
│  │• Templates       │                                                        │
│  │                  │                                                        │
│  │Used by:          │                                                        │
│  │ Research         │                                                        │
│  └──────────────────┘                                                        │
│                                                                               │
│  All servers implement Model Context Protocol (MCP)                           │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                       📊 DATA FLOW                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. INITIALIZATION                                                            │
│     run.py → seed_knowledge.py → Neo4j + Qdrant                             │
│           → seed_agents.py → PostgreSQL                                      │
│                                                                               │
│  2. SIMULATION STEP                                                           │
│     Community Orchestrator                                                    │
│          ↓                                                                   │
│     Select Active Agents                                                      │
│          ↓                                                                   │
│     Determine Activity (learning/teaching/research/review)                    │
│          ↓                                                                   │
│     Execute Activity:                                                         │
│        • Query LLM (Ollama)                                                  │
│        • Use MCP servers (literature/experiments/knowledge/writing)          │
│        • Update state (PostgreSQL)                                           │
│        • Update knowledge (Neo4j + Qdrant)                                   │
│        • Update reputation                                                    │
│        • Log metrics (Redis)                                                 │
│          ↓                                                                   │
│     Check for Promotions                                                      │
│          ↓                                                                   │
│     Save Checkpoint                                                           │
│                                                                               │
│  3. ANALYSIS                                                                  │
│     analyze_community.py                                                      │
│          ↓                                                                   │
│     Query all storage systems                                                 │
│          ↓                                                                   │
│     Generate statistics                                                       │
│          ↓                                                                   │
│     Create report → reports/                                                  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                    📁 FILE ORGANIZATION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Configuration (4 files)       Source Code (28 modules)                      │
│  ├── pyproject.toml            ├── src/                                      │
│  ├── docker-compose.yml        │   ├── core/ (4)                             │
│  ├── .env.example              │   ├── activities/ (4)                       │
│  └── .gitignore                │   ├── llm/ (3)                              │
│                                │   ├── mcp_servers/ (11)                     │
│  Documentation (10 files)      │   ├── orchestration/ (4)                    │
│  ├── README.md                 │   ├── storage/ (4)                          │
│  ├── PROJECT_COMPLETE.md       │   └── utils/ (3)                            │
│  ├── COMPLETION_SUMMARY.md     │                                             │
│  ├── SETUP_GUIDE.md            Scripts (5 files)                             │
│  ├── OLLAMA_SETUP.md           ├── run.py ⭐                                 │
│  ├── OLLAMA_QUICKREF.md        ├── scripts/                                  │
│  └── ... (4 more)              │   ├── seed_knowledge.py                     │
│                                │   ├── seed_agents.py                        │
│  Configuration (7 files)       │   ├── run_simulation.py                     │
│  ├── config/                   │   └── analyze_community.py                  │
│  │   ├── agent_templates.yaml  │                                             │
│  │   ├── knowledge_graph.yaml  Data (8 files)                                │
│  │   ├── evaluation_rubrics... ├── data/                                     │
│  │   └── curricula/ (2)        │   ├── seed_agents/ (3)                     │
│                                │   ├── seed_knowledge/ (4)                   │
│                                │   ├── papers/                               │
│                                │   └── experiments/                          │
│                                │                                             │
│                                Reports (generated)                            │
│                                └── reports/                                   │
│                                    └── community_report_*.txt                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

USAGE: poetry run python run.py [--steps N] [--duration S] [--skip-seed] [--skip-docker]
