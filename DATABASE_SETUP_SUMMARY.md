# Database Setup Summary

## Issue Resolved

The issue was that Alembic was not initialized for your project. Here's what was done:

### 1. Alembic Initialization

Created Alembic migration structure:
- `alembic/` directory with migrations
- `alembic.ini` configuration file
- Initial migration file: `698c1e702669_initial_schema.py`

### 2. Database Schema Deployment

Due to Windows networking issues with psycopg2/asyncpg connections from the host to Docker (WinError 64), the schema was deployed directly using:

```powershell
Get-Content scripts/init_db.sql | docker exec -i research-collective-postgres psql -U agent_system -d research_collective
```

### 3. Verified Tables

All 7 tables created successfully:
- `agents`
- `knowledge_topics`
- `papers`
- `agent_papers`
- `experience_log`
- `mentorships`
- `experiments`

## Known Issues

### Python-to-Docker PostgreSQL Connection (Windows)

There's a networking issue preventing Python libraries (psycopg2/asyncpg) from connecting to PostgreSQL in Docker from Windows host:
- Error: `ConnectionResetError: [WinError 64] Le nom réseau spécifié n'est plus disponible`
- This affects: Alembic migrations run from host

**Workaround Options:**

1. **Run migrations inside Docker** (Recommended):
   ```powershell
   docker exec -it research-collective-postgres bash
   # Then run alembic commands from within container
   ```

2. **Apply schema directly** (What we did):
   ```powershell
   Get-Content scripts/init_db.sql | docker exec -i research-collective-postgres psql -U agent_system -d research_collective
   ```

3. **Use Docker network** - Run your Python app inside a Docker container

### Future Migrations

When you need to make schema changes:

**Option A: Use SQL files**
1. Create a new `.sql` file in `scripts/`
2. Apply it: `Get-Content scripts/migration.sql | docker exec -i research-collective-postgres psql -U agent_system -d research_collective`

**Option B: Use Alembic from Docker**
1. Add Alembic to a Docker service in `docker-compose.yml`
2. Run: `docker-compose run app poetry run alembic upgrade head`

## Poetry Shell Command

Note: Poetry 2.0+ removed the `shell` command by default. Use instead:

```powershell
# Get activation command
poetry env activate

# Then run the output command
& "C:\Users\atepi\AppData\Local\pypoetry\Cache\virtualenvs\mcp-research-collective-lJON8_ba-py3.10\Scripts\activate.ps1"
```

Or simply use `poetry run <command>` for individual commands.

## Next Steps

Your database is ready! You can now:

1. Run the seed scripts:
   ```powershell
   poetry run python scripts/seed_knowledge.py
   poetry run python scripts/seed_agents.py
   ```

2. Start the application:
   ```powershell
   poetry run python run.py
   ```

## Database Connection in Your Code

Your application uses `asyncpg` which may have the same Windows connectivity issue. If you encounter problems:

1. Check if app runs from Docker
2. Or investigate Windows Docker networking settings
3. Possible solutions:
   - Enable WSL 2 backend for Docker Desktop
   - Check Windows Firewall settings
   - Try Docker host network mode (Linux only)
