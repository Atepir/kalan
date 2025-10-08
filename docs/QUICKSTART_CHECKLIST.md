# 🚀 Quick Start Checklist

Copy this checklist and check off items as you complete them!

---

## 📋 Pre-Flight Checklist

### 1. System Requirements
- [ ] Windows 10/11 with PowerShell
- [ ] 8GB+ RAM (16GB recommended)
- [ ] 20GB+ free disk space
- [ ] Internet connection (for initial setup)

### 2. Install Prerequisites
- [ ] Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
- [ ] Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- [ ] Install Poetry: `pip install poetry`
- [ ] Install Ollama: `iwr https://ollama.ai/download/windows -useb | iex`

### 3. Clone and Setup
```powershell
# Clone repository
git clone <repository-url>
cd project-kalan

# Copy environment file
copy .env.example .env

# Install dependencies
poetry install
```

- [ ] Repository cloned
- [ ] Environment file created
- [ ] Dependencies installed

---

## 🐳 Docker Setup

### 4. Start Infrastructure
```powershell
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

- [ ] Docker services started
- [ ] All 6 services show "Up" status

Expected output:
```
NAME                        STATUS
research-postgres           Up
research-neo4j              Up
research-qdrant             Up
research-redis              Up
research-ollama             Up
research-adminer            Up
```

### 5. Pull LLM Models
```powershell
# Pull default model (required)
docker exec -it research-ollama ollama pull llama3.1:8b

# Pull additional models (optional but recommended)
docker exec -it research-ollama ollama pull mistral:7b
docker exec -it research-ollama ollama pull phi3:mini
docker exec -it research-ollama ollama pull codellama:13b
```

- [ ] llama3.1:8b pulled (required)
- [ ] mistral:7b pulled (optional)
- [ ] phi3:mini pulled (optional)
- [ ] codellama:13b pulled (optional)

---

## 🎯 First Run

### 6. Run Master Script
```powershell
# Activate Poetry environment
poetry shell

# Run the system!
poetry run python run.py
```

- [ ] Poetry shell activated
- [ ] Master script running

### 7. Watch Output
You should see:
```
================================================================================
 Checking Docker Infrastructure
================================================================================

✅ Docker Compose: ...
✅ Docker services are running

================================================================================
 Seeding Knowledge Graph
================================================================================

✅ Created 31 concepts
✅ Created 45 relationships
...
```

- [ ] Docker check passed
- [ ] Knowledge seeding completed
- [ ] Agent seeding completed
- [ ] Simulation running
- [ ] Analysis generated

---

## ✅ Verify Success

### 8. Check Results

**Terminal Output:**
- [ ] Simulation completed N steps
- [ ] Activity statistics shown
- [ ] Community statistics shown
- [ ] Report path displayed

**Reports Directory:**
```powershell
dir reports/
```
- [ ] Report file exists: `community_report_YYYYMMDD_HHMMSS.txt`
- [ ] Report is readable

**Neo4j Browser:**
- [ ] Open http://localhost:7474
- [ ] Login: username=`neo4j`, password=`password`
- [ ] Run query: `MATCH (n) RETURN n LIMIT 25`
- [ ] See knowledge graph nodes

**Adminer (PostgreSQL):**
- [ ] Open http://localhost:8081
- [ ] Login: server=`postgres`, username=`researcher`, password=`research_password`
- [ ] Select database: `research_collective`
- [ ] Browse table: `agent_state`
- [ ] See 12 agents

---

## 🎓 Next Steps

### 9. Explore the System

**Read Documentation:**
- [ ] Read `PROJECT_COMPLETE.md` (comprehensive overview)
- [ ] Skim `ARCHITECTURE.md` (system diagram)
- [ ] Read `COMPLETION_SUMMARY.md` (quick reference)

**Explore Data:**
- [ ] Browse `data/seed_agents/*.json` files
- [ ] Browse `data/seed_knowledge/*.json` files
- [ ] Check `config/` YAML files

**Run Variations:**
```powershell
# Quick test (10 steps)
poetry run python run.py --steps 10 --duration 0.1

# Extended run (200 steps)
poetry run python run.py --steps 200

# Skip seeding (reuse existing data)
poetry run python run.py --skip-seed
```

- [ ] Tried quick test run
- [ ] Explored Neo4j graph
- [ ] Read generated reports

### 10. Customize

**Add Your Own Agent:**
1. [ ] Edit `data/seed_agents/apprentices.json`
2. [ ] Add new agent with your name
3. [ ] Run: `poetry run python run.py`
4. [ ] Watch your agent learn!

**Add Your Own Knowledge:**
1. [ ] Edit `data/seed_knowledge/foundations.json`
2. [ ] Add a new concept
3. [ ] Run: `poetry run python run.py`
4. [ ] See it in Neo4j graph

---

## 🐛 Troubleshooting

### Common Issues

**"Docker not found"**
- [ ] Install Docker Desktop
- [ ] Start Docker Desktop
- [ ] Wait for Docker to be ready (green icon in system tray)

**"Ollama not responding"**
```powershell
# Check Ollama service
docker ps | findstr ollama

# Restart Ollama
docker-compose restart ollama

# Check Ollama logs
docker-compose logs ollama
```
- [ ] Ollama container running
- [ ] Models pulled successfully

**"Database connection failed"**
```powershell
# Check PostgreSQL
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait 10 seconds
timeout /t 10
```
- [ ] PostgreSQL logs show no errors
- [ ] Connection successful after restart

**"Services slow to start"**
```powershell
# Wait for all services to be ready
timeout /t 30

# Check service health
docker-compose ps
```
- [ ] Waited for services
- [ ] All services healthy

---

## 📊 Success Criteria

Your system is working correctly if:

- ✅ `poetry run python run.py` completes without errors
- ✅ Simulation runs for N steps (default 50)
- ✅ Report generated in `reports/` directory
- ✅ Neo4j shows 31+ knowledge nodes
- ✅ PostgreSQL shows 12 agent records
- ✅ Qdrant has embeddings stored
- ✅ No error messages in terminal

---

## 🎉 Completion

### All Done!

- [ ] **System installed and running**
- [ ] **First simulation completed**
- [ ] **Results verified**
- [ ] **Documentation read**
- [ ] **Ready to explore and customize**

**Congratulations! Your Research Collective is operational! 🚀🤖📚**

---

## 📚 Quick Reference

### Essential Commands
```powershell
# Start system
poetry run python run.py

# Quick test
poetry run python run.py --steps 10

# Extended run
poetry run python run.py --steps 200

# Skip seeding
poetry run python run.py --skip-seed

# View reports
dir reports/

# Open Neo4j
start http://localhost:7474

# Open Adminer
start http://localhost:8081
```

### Essential Files
- `run.py` - Master script (START HERE!)
- `PROJECT_COMPLETE.md` - Full documentation
- `ARCHITECTURE.md` - System diagram
- `COMPLETION_SUMMARY.md` - Quick reference
- `data/seed_agents/*.json` - Agent templates
- `data/seed_knowledge/*.json` - Knowledge concepts

### Essential URLs
- Neo4j: http://localhost:7474 (neo4j/password)
- Adminer: http://localhost:8081 (postgres/researcher/research_password)
- Qdrant: http://localhost:6333/dashboard
- Ollama: http://localhost:11434

---

## 💡 Tips

1. **Start Small**: Run with `--steps 10` first to verify everything works
2. **Monitor Resources**: Docker services use ~4GB RAM, keep an eye on memory
3. **Read Reports**: Generated reports show detailed agent statistics
4. **Explore Neo4j**: Graph visualization helps understand knowledge structure
5. **Customize Gradually**: Start by modifying one agent, then expand
6. **Save Logs**: Terminal output contains valuable debugging information

---

**Need help?** Review the documentation:
- `PROJECT_COMPLETE.md` - Comprehensive guide
- `SETUP_GUIDE.md` - Detailed installation
- `OLLAMA_SETUP.md` - Ollama-specific help
- `ARCHITECTURE.md` - System architecture

**Happy researching! 🎓**
