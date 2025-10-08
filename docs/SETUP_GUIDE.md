# MCP Research Collective - Setup Guide

## ✅ What Has Been Created

### 1. Project Configuration Files
- ✅ `pyproject.toml` - Poetry dependency management with all required packages
- ✅ `.env.example` - Environment variable template with all configuration options
- ✅ `docker-compose.yml` - Complete Docker setup for PostgreSQL, Neo4j, Qdrant, and Redis
- ✅ `.gitignore` - Comprehensive Python/.gitignore
- ✅ `README.md` - Full project documentation with architecture diagrams

### 2. Core Agent System (`src/core/`)
- ✅ `agent.py` - Complete Agent class with:
  - Identity and stage management
  - Goal tracking
  - Experience logging
  - Mentorship relationships
  - Promotion assessment
  - Pydantic models for type safety

- ✅ `knowledge.py` - Knowledge graph implementation:
  - Topic-based knowledge tracking
  - Depth/breadth/confidence scores
  - Source provenance
  - Prerequisite checking
  - Competency assessment
  - Knowledge transfer methods

- ✅ `evolution.py` - Stage progression system:
  - Promotion criteria for each stage
  - Eligibility evaluation
  - Automatic promotion execution
  - Progress tracking

- ✅ `reputation.py` - Multi-dimensional reputation:
  - Teaching, research, review, collaboration scores
  - Citation tracking
  - H-index calculation
  - Student outcome tracking

### 3. Utilities (`src/utils/`)
- ✅ `config.py` - Pydantic settings management
- ✅ `logging.py` - Structured logging with structlog
- ✅ `metrics.py` - Comprehensive metrics collection and tracking

### 4. LLM Integration (`src/llm/`)
- ✅ `client.py` - Claude API client with:
  - Async operations
  - Retry logic
  - Rate limiting
  - Token tracking
  - Batch generation
  - Tool use support

### 5. Database Setup
- ✅ `scripts/init_db.sql` - PostgreSQL schema with:
  - Agent tables
  - Knowledge tracking
  - Papers and relationships
  - Experience logs
  - Mentorships
  - Experiments
  - Vector search indexes

## 🚧 What Needs To Be Completed

### Priority 1: Core Functionality

1. **Activities Module** (`src/activities/`)
   - `learning.py` - Paper reading, comprehension, mentor queries
   - `teaching.py` - Student assessment, curriculum generation
   - `research.py` - Literature review, hypothesis generation, experiments
   - `review.py` - Peer review workflows

2. **Storage Layer** (`src/storage/`)
   - `state_store.py` - Agent state persistence (PostgreSQL)
   - `vector_store.py` - Qdrant integration for embeddings
   - `graph_store.py` - Neo4j integration for knowledge graphs
   - `document_store.py` - Document management

3. **LLM Integration** (`src/llm/`)
   - `prompts.py` - Prompt templates for all activities
   - `tools.py` - LLM tool definitions

### Priority 2: MCP Servers

4. **MCP Server Infrastructure** (`src/mcp_servers/`)
   - `literature/server.py` + `literature/tools.py` - arXiv, Semantic Scholar integration
   - `experiments/server.py` + `experiments/sandbox.py` - Code execution sandbox
   - `knowledge/server.py` + `knowledge/queries.py` - Knowledge base queries
   - `writing/server.py` + `writing/templates.py` - LaTeX generation

### Priority 3: Orchestration

5. **Orchestration Layer** (`src/orchestration/`)
   - `community.py` - Community-wide coordination
   - `matchmaking.py` - Mentor-student pairing algorithms
   - `workflows.py` - LangGraph workflows
   - `events.py` - Conferences and seminars

### Priority 4: Scripts and Configuration

6. **Seed Scripts** (`scripts/`)
   - `seed_agents.py` - Create initial agent population
   - `seed_knowledge.py` - Load foundational knowledge graph
   - `run_simulation.py` - Run community simulations
   - `analyze_community.py` - Community health metrics

7. **Configuration Files** (`config/`)
   - `agent_templates.yaml` - Agent initialization templates
   - `curricula/mathematics.yaml` - Math curriculum
   - `curricula/machine_learning.yaml` - ML curriculum
   - `curricula/physics.yaml` - Physics curriculum
   - `evaluation_rubrics.yaml` - Assessment criteria

### Priority 5: Testing

8. **Test Suite** (`tests/`)
   - `test_agent.py` - Agent core tests
   - `test_learning.py` - Learning workflow tests
   - `test_teaching.py` - Teaching system tests
   - `test_research.py` - Research workflow tests
   - `test_mcp_servers.py` - MCP server tests
   - `test_integration.py` - End-to-end integration tests

### Priority 6: Data

9. **Seed Data** (`data/`)
   - `knowledge_graph/concepts.json` - Base concepts (20-30 foundational topics)
   - `papers/.gitkeep` - Placeholder for seed papers
   - Create data directory structure

## 🏃 Quick Start (After Completion)

### Step 1: Install Dependencies

```powershell
# Install Poetry if needed
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Step 2: Configure Environment

```powershell
# Copy environment template
copy .env.example .env

# Edit .env if needed (defaults work for local Ollama)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
```

### Step 3: Start Infrastructure

```powershell
# Start all services (including Ollama)
docker-compose up -d

# Pull the LLM model (first time only, ~5GB download)
docker exec -it research-collective-ollama ollama pull llama3.1:8b

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs -f
```

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed Ollama configuration.

### Step 4: Initialize Database

```powershell
# The PostgreSQL init script runs automatically
# To manually run migrations (when implemented):
poetry run alembic upgrade head
```

### Step 5: Seed Data

```powershell
# Load base knowledge graph
poetry run python scripts/seed_knowledge.py

# Create initial agent population
poetry run python scripts/seed_agents.py
```

### Step 6: Run Simulation

```powershell
# Run a test simulation
poetry run python scripts/run_simulation.py --duration 1h --agents 5

# Analyze results
poetry run python scripts/analyze_community.py
```

## 📋 Implementation Checklist

### Immediate Next Steps

1. [ ] Create `src/activities/learning.py` with basic paper reading workflow
2. [ ] Implement `src/storage/state_store.py` for agent persistence
3. [ ] Create `src/llm/prompts.py` with essential prompt templates
4. [ ] Implement `src/mcp_servers/literature/server.py` for arXiv access
5. [ ] Create `scripts/seed_agents.py` to bootstrap the system
6. [ ] Write basic tests in `tests/test_agent.py`

### Week 1 Goals

- [ ] Complete all activities modules
- [ ] Implement storage layer
- [ ] Create one working MCP server (literature)
- [ ] Build basic orchestration
- [ ] Write seed scripts

### Week 2 Goals

- [ ] Complete all MCP servers
- [ ] Implement full orchestration layer
- [ ] Create comprehensive test suite
- [ ] Add seed data and configurations
- [ ] Run first end-to-end simulation

## 🧪 Testing Strategy

### Unit Tests
```powershell
# Run all tests
poetry run pytest

# Run specific module
poetry run pytest tests/test_agent.py

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Integration Tests
```powershell
# Run integration tests (requires Docker services)
poetry run pytest tests/test_integration.py -v
```

### Simulation Tests
```powershell
# Run short simulation
poetry run python scripts/run_simulation.py --duration 10m --agents 3 --test-mode
```

## 🐛 Common Issues

### Import Errors
The lint errors about missing imports (pydantic, httpx, etc.) are expected until you run:
```powershell
poetry install
```

### Database Connection Issues
```powershell
# Verify Docker services are running
docker-compose ps

# Restart services if needed
docker-compose restart

# Check logs
docker-compose logs postgres
```

### Slow Ollama Responses
Adjust in `.env`:
```bash
OLLAMA_MODEL=phi3:mini       # Use smaller model
MAX_CONCURRENT_AGENTS=2      # Reduce concurrent operations
```

### Out of Memory with Ollama
```powershell
# Switch to smaller model
docker exec -it research-collective-ollama ollama pull phi3:mini
# Update .env: OLLAMA_MODEL=phi3:mini
```

## 📚 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Community Orchestrator                  │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐     │
│  │Matchmaker│  │ Workflows │  │   Events    │     │
│  └──────────┘  └───────────┘  └─────────────┘     │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────┐
    │                 │              │              │
┌───▼────┐     ┌─────▼──────┐  ┌───▼────┐  ┌──────▼──────┐
│ Agents │◄───►│ Activities │  │  LLM   │  │   Storage   │
│        │     │            │  │ Client │  │             │
│ • State│     │ • Learning │  │        │  │ • PostgreSQL│
│ • Know.│     │ • Teaching │  │ Claude │  │ • Neo4j     │
│ • Repul│     │ • Research │  │  API   │  │ • Qdrant    │
└────────┘     └────────────┘  └────────┘  └─────────────┘
                     │
            ┌────────┴─────────┐
            │   MCP Servers    │
            │ Literature | Exp │
            │ Knowledge | Write│
            └──────────────────┘
```

## 🎯 Development Philosophy

1. **Type Safety**: Use Pydantic models and type hints everywhere
2. **Async First**: All I/O operations should be async
3. **Observability**: Log everything with structured logging
4. **Error Handling**: Comprehensive error handling with retry logic
5. **Testing**: Maintain >80% test coverage
6. **Documentation**: Clear docstrings and inline comments

## 📖 Next Documentation to Create

1. `docs/architecture.md` - Deep dive into system design
2. `docs/agents.md` - Agent lifecycle and configuration guide
3. `docs/mcp.md` - MCP server implementation guide
4. `docs/api.md` - API reference documentation
5. `docs/tutorials/` - Step-by-step tutorials
6. `CONTRIBUTING.md` - Contribution guidelines

## 🤝 Getting Help

- Review the comprehensive README.md for project overview
- Check this SETUP_GUIDE.md for implementation status
- Examine existing code for patterns and examples
- Look at Pydantic models for data structures
- Review prompts.py (when created) for LLM interaction patterns

## 📞 Support

For questions or issues during development:
1. Check the comprehensive docstrings in existing modules
2. Review the architecture diagram in README.md
3. Examine similar implementations in related modules
4. Consult the official documentation for:
   - Pydantic: https://docs.pydantic.dev
   - Anthropic Claude: https://docs.anthropic.com
   - LangGraph: https://langchain-ai.github.io/langgraph
   - MCP: https://modelcontextprotocol.io

---

**Status**: Foundation complete, ready for core implementation 🚀
**Last Updated**: October 8, 2025
