# MCP Research Collective ✅

> A developmental multi-agent research system where AI agents evolve from novice learners to expert researchers through mentorship, teaching, and collaborative research activities.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status: Complete](https://img.shields.io/badge/status-100%25%20complete-success.svg)](docs/PROJECT_COMPLETE.md)

> **🎉 PROJECT 100% COMPLETE!** See [docs/PROJECT_COMPLETE.md](docs/PROJECT_COMPLETE.md) for full details.

## 🎯 Vision

The MCP Research Collective simulates a living academic community where AI agents:
- **Learn** by reading papers, asking questions, and receiving mentorship
- **Teach** others, solidifying their own understanding and building reputation
- **Research** by formulating hypotheses, running experiments, and publishing findings
- **Evolve** through five developmental stages: Apprentice → Practitioner → Teacher → Researcher → Expert
- **Collaborate** in a reputation-based ecosystem with peer review and conferences

This system explores emergent behaviors in multi-agent learning systems while providing a testbed for AI-driven scientific discovery.

**🆕 Now powered by Ollama for local, private LLM execution with no API costs!**

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Community Orchestrator                       │
│  (Matchmaking, Events, Workflows, Resource Allocation)          │
└───────────────────┬─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬─────────────┬──────────────┐
        │                       │             │              │
┌───────▼────────┐    ┌────────▼───────┐  ┌─▼────────┐  ┌──▼──────┐
│  Agent Layer   │    │   Activities   │  │   LLM    │  │ Storage │
│                │    │                │  │ Client   │  │ Layer   │
│ • Identity     │◄───┤ • Learning     │◄─┤          │  │         │
│ • Knowledge    │    │ • Teaching     │  │ Ollama   │  │ • Neo4j │
│ • Reputation   │    │ • Research     │  │ API      │  │ • PostgreSQL│
│ • Stage        │    │ • Review       │  └──────────┘  └──────────┘
└───────┬────────┘    └────────┬───────┘
        │                      │                           │
        └──────────┬───────────┴───────────────────────────┘
                   │
        ┌──────────▼──────────────────────────────────┐
        │         MCP Server Infrastructure            │
        │ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
        │ │Literature│ │Experiment│ │Knowledge │ ... │
        │ │  Server  │ │  Server  │ │  Server  │     │
        │ └──────────┘ └──────────┘ └──────────┘     │
        └─────────────────────────────────────────────┘
```

### Key Components

1. **Agent Core** (`src/core/`)
   - **agent.py**: Stateful agents with identity, goals, and developmental stages
   - **knowledge.py**: Personal knowledge graphs with confidence and provenance tracking
   - **evolution.py**: Stage progression logic with promotion criteria
   - **reputation.py**: Multi-dimensional reputation system (teaching, research, collaboration)

2. **Activities** (`src/activities/`)
   - **learning.py**: Paper reading, comprehension assessment, mentor queries
   - **teaching.py**: Knowledge assessment, personalized curriculum, verification loops
   - **research.py**: Literature review, hypothesis generation, experiment design, paper writing
   - **review.py**: Peer review workflows with multi-dimensional assessment

3. **MCP Servers** (`src/mcp_servers/`)
   - **Literature**: arXiv, Semantic Scholar, PubMed integration
   - **Experiments**: Sandboxed code execution and data analysis
   - **Knowledge**: Vector/graph database queries
   - **Writing**: LaTeX generation and citation management

4. **Orchestration** (`src/orchestration/`)
   - **community.py**: Global agent coordination and resource management
   - **matchmaking.py**: Mentor-student pairing algorithms
   - **workflows.py**: LangGraph-based activity coordination
   - **events.py**: Conferences, seminars, and collaborative opportunities

5. **Storage** (`src/storage/`)
   - **Neo4j**: Knowledge graphs and relationship networks
   - **PostgreSQL**: Agent state, papers, and structured data (with caching via tables)
   - **Vector Store**: Simplified stub (Qdrant removed for simplicity)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- (Optional) NVIDIA GPU for faster model inference

### Installation

1. **Clone and setup environment**
   ```powershell
   git clone <repository-url>
   cd project-kalan
   
   # Copy environment template
   copy .env.example .env
   
   # Configure Ollama settings in .env (defaults are usually fine)
   # OLLAMA_BASE_URL=http://localhost:11434
   # OLLAMA_MODEL=llama3.1:8b
   ```

2. **Install dependencies with Poetry**
   ```powershell
   # Install Poetry if not already installed
   pip install poetry
   
   # Install project dependencies
   poetry install
   
   # Activate virtual environment
   poetry shell
   ```

3. **Start infrastructure services**
   ```powershell
   docker-compose up -d
   
   # Verify services are healthy
   docker-compose ps
   
   # Pull the default model (first time only)
   docker exec -it research-collective-ollama ollama pull llama3.1:8b
   
   # Or pull alternative models:
   # docker exec -it research-collective-ollama ollama pull mistral:7b
   # docker exec -it research-collective-ollama ollama pull codellama:13b
   ```

4. **Initialize databases**
   ```powershell
   # Run database migrations
   poetry run alembic upgrade head
   
   # Seed initial knowledge graph
   poetry run python scripts/seed_knowledge.py
   
   # Create initial agent population
   poetry run python scripts/seed_agents.py
   ```

5. **Run a simulation (or use master script!)**
   ```powershell
   # 🎯 EASIEST: Use master script (does everything!)
   poetry run python run.py
   
   # Or run individual scripts:
   poetry run python scripts/run_simulation.py --steps 100
   
   # Analyze results
   poetry run python scripts/analyze_community.py
   # Run 24-hour community simulation
   poetry run python scripts/run_simulation.py --duration 24h --agents 10
   ```

### Accessing Services

- **Ollama API**: http://localhost:11434
- **Neo4j Browser**: http://localhost:7474 (neo4j / dev_password)
- **PostgreSQL**: localhost:5432 (agent_system / dev_password)

## 📚 Agent Lifecycle

### Developmental Stages

Agents progress through five stages, each with distinct capabilities and requirements:

| Stage | Focus | Can Mentor | Can Research | Promotion Criteria |
|-------|-------|------------|--------------|-------------------|
| **Apprentice** | Learning fundamentals | ❌ | ❌ | Read 5+ papers, pass assessments |
| **Practitioner** | Applying knowledge | Apprentices | Limited | Teach 3+ students, run experiments |
| **Teacher** | Educating others | All below | ✅ | 5+ successful students, peer reviews |
| **Researcher** | Original research | All below | ✅ | Publish 2+ papers, high citations |
| **Expert** | Community leadership | All | ✅ | 10+ publications, exceptional reputation |

### Activity Flow Example

```
┌──────────────┐
│  Apprentice  │
└──────┬───────┘
       │
       ├─→ 1. Reads paper from Literature Server
       │
       ├─→ 2. Self-assesses comprehension (confidence < 0.7)
       │
       ├─→ 3. Seeks mentor via Community Orchestrator
       │
       ├─→ 4. Mentor provides explanation
       │
       ├─→ 5. Re-assesses understanding (confidence > 0.7)
       │
       ├─→ 6. Updates personal knowledge graph
       │
       └─→ 7. Logs learning experience
```

## 🔧 Configuration

### Agent Templates

Define initial agent configurations in `config/agent_templates.yaml`:

```yaml
apprentice:
  initial_stage: "apprentice"
  base_knowledge:
    topics:
      - name: "scientific_method"
        depth_score: 0.6
        confidence: 0.7
  available_tools:
    - "literature_search"
    - "read_paper"
  max_concurrent_activities: 2
  requires_mentor: true
```

### Curricula

Create learning paths in `config/curricula/`:

```yaml
name: "Machine Learning Fundamentals"
target_stage: "apprentice"
topics:
  - name: "supervised_learning"
    required_papers:
      - "A Few Useful Things to Know about Machine Learning"
    competency_threshold: 0.7
    prerequisites: ["basic_statistics", "linear_algebra"]
```

### Environment Variables

Key settings in `.env`:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b  # Or mistral:7b, codellama:13b, etc.

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=50
MAX_CONCURRENT_AGENTS=10

# Learning Configuration
MIN_PAPERS_FOR_PROMOTION=5
MIN_KNOWLEDGE_DEPTH=0.7
```

## 🧪 Development

### Project Structure

```
src/
├── core/           # Agent state, knowledge, reputation
├── activities/     # Learning, teaching, research, review
├── mcp_servers/    # MCP protocol implementations
├── orchestration/  # Community coordination
├── storage/        # Database interfaces
├── llm/            # Claude API client
└── utils/          # Config, logging, metrics
```

### Running Tests

```powershell
# Run all tests with coverage
poetry run pytest

# Run specific test file
poetry run pytest tests/test_agent.py

# Run with verbose output
poetry run pytest -v

# Generate HTML coverage report
poetry run pytest --cov-report=html
```

### Code Quality

```powershell
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

### Database Migrations

```powershell
# Create new migration
poetry run alembic revision -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one version
poetry run alembic downgrade -1
```

## 🔬 MCP Servers

### Literature Server

**Port**: 5001  
**Capabilities**: arXiv search, paper fetching, metadata extraction

```python
# Example: Search for papers
result = await literature_server.search_papers(
    query="attention mechanisms in transformers",
    max_results=10
)
```

### Experiment Server

**Port**: 5002  
**Capabilities**: Sandboxed Python execution, data analysis, result persistence

```python
# Example: Run experiment
result = await experiment_server.execute_code(
    code="import numpy as np; np.mean([1,2,3])",
    timeout=300
)
```

### Knowledge Server

**Port**: 5003  
**Capabilities**: Semantic search, graph queries, concept relationships

```python
# Example: Find related concepts
concepts = await knowledge_server.find_related(
    concept="neural_networks",
    max_depth=2
)
```

### Writing Server

**Port**: 5004  
**Capabilities**: LaTeX generation, bibliography management, formatting

```python
# Example: Generate paper
paper = await writing_server.generate_paper(
    title="My Research",
    sections=["intro", "methods", "results"],
    citations=[...]
)
```

## 📊 Monitoring & Metrics

### Community Health Metrics

```powershell
# Analyze community state
poetry run python scripts/analyze_community.py

# Output includes:
# - Agent stage distribution
# - Average knowledge depth by topic
# - Mentorship network density
# - Research output rate
# - Citation impact
```

### Logging

Structured logs are written to `logs/` with context:

```json
{
  "timestamp": "2025-10-08T10:30:00Z",
  "agent_id": "agent_001",
  "activity": "learning",
  "event": "paper_read",
  "paper_id": "arxiv:1706.03762",
  "confidence_before": 0.3,
  "confidence_after": 0.75,
  "duration_seconds": 120
}
```

## 🛠️ Extending the System

### Adding a New Activity

1. Create module in `src/activities/new_activity.py`
2. Implement async activity function
3. Register with orchestrator in `src/orchestration/workflows.py`
4. Add tests in `tests/test_new_activity.py`

### Creating a Custom MCP Server

1. Create directory `src/mcp_servers/custom/`
2. Implement `server.py` following MCP protocol
3. Define tools in `tools.py`
4. Register in `src/mcp_servers/__init__.py`
5. Add environment variables to `.env.example`

### Adding a New Agent Stage

1. Update `src/core/evolution.py` with stage definition
2. Define promotion criteria
3. Add agent template in `config/agent_templates.yaml`
4. Update documentation

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Ensure code quality: `poetry run pytest && poetry run ruff check && poetry run mypy src`
5. Commit: `git commit -m "Add amazing feature"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [x] Core agent system
- [x] Basic learning and teaching
- [x] Literature MCP server
- [x] PostgreSQL/Neo4j integration
- [x] Simplified architecture (Qdrant and Redis removed)

### Phase 2: Enhanced Activities (Q1 2026)
- [ ] Full research workflow implementation
- [ ] Peer review system
- [ ] Collaborative research projects
- [ ] Conference and seminar events

### Phase 3: Advanced Features (Q2 2026)
- [ ] Multi-modal learning (images, videos)
- [ ] Cross-domain knowledge transfer
- [ ] Automated hypothesis generation
- [ ] Real-world experiment integration

### Phase 4: Scale & Optimization (Q3 2026)
- [ ] Support for 100+ concurrent agents
- [ ] Distributed computation
- [ ] Advanced reputation algorithms
- [ ] Community governance mechanisms

## 📖 Documentation

### 🎯 Getting Started
- **[Quick Start Checklist](docs/QUICKSTART_CHECKLIST.md)**: Step-by-step setup guide
- **[Setup Guide](docs/SETUP_GUIDE.md)**: Detailed installation instructions
- **[Ollama Setup](docs/OLLAMA_SETUP.md)**: Local LLM configuration

### 📚 Core Documentation
- **[Project Complete](docs/PROJECT_COMPLETE.md)**: Comprehensive project overview
- **[Architecture](docs/ARCHITECTURE.md)**: System design and diagrams
- **[Completion Summary](docs/COMPLETION_SUMMARY.md)**: Quick reference guide
- **[Manifest](docs/MANIFEST.md)**: Complete file inventory

### 🔧 Technical Documentation
- **[MCP Servers](docs/MCP_SERVERS_COMPLETE.md)**: MCP server implementation
- **[Orchestration Layer](docs/ORCHESTRATION_LAYER_COMPLETE.md)**: Multi-agent coordination
- **[Storage Layer](docs/STORAGE_LAYER_COMPLETE.md)**: Database systems
- **[Scripts & Config](docs/SCRIPTS_AND_CONFIG_COMPLETE.md)**: Automation and configuration

### 📖 Additional Resources
- **[Ollama Quick Reference](docs/OLLAMA_QUICKREF.md)**: Ollama commands
- **[Migration to Ollama](docs/MIGRATION_TO_OLLAMA.md)**: Migration notes
- **[Refactoring Complete](docs/REFACTORING_COMPLETE.md)**: Refactoring history

## 🐛 Troubleshooting

### Common Issues

**Issue**: Docker services won't start
```powershell
# Solution: Check ports aren't already in use
netstat -ano | findstr "5432 7474 7687 11434"

# Stop conflicting services or change ports in docker-compose.yml
```

**Issue**: Agent promotion not working
```powershell
# Solution: Check promotion criteria are met
poetry run python -c "from src.core.agent import Agent; agent = Agent.load('agent_001'); print(agent.check_promotion_readiness())"
```

**Issue**: Ollama model responses are slow
```powershell
# Solution: Use a smaller model or enable GPU acceleration
OLLAMA_MODEL=llama3.1:8b  # Faster than 70b models

# For CPU-only machines, use smaller models:
# mistral:7b or phi3:mini
```

**Issue**: Out of memory errors
```powershell
# Solution: Use a smaller model
docker exec -it research-collective-ollama ollama pull phi3:mini
# Update .env: OLLAMA_MODEL=phi3:mini
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Powered by [Ollama](https://ollama.ai/) for local LLM execution
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent workflows
- Inspired by research in developmental AI and multi-agent systems
- Models: Llama 3.1, Mistral, CodeLlama, and others from the open-source community

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-research-collective/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mcp-research-collective/discussions)
- **Email**: research-collective@example.com

---

**Built with ❤️ for the future of AI-driven scientific discovery**
