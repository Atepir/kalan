"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables and .env files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Ollama API Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3.1:8b",
        description="Ollama model to use (e.g., llama3.1:8b, mistral:7b, codellama:13b)",
    )
    ollama_max_tokens: int = Field(default=4096, description="Max tokens for Ollama responses")

    # Database Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="research_collective", description="PostgreSQL database name")
    postgres_user: str = Field(default="agent_system", description="PostgreSQL user")
    postgres_password: str = Field(default="dev_password", description="PostgreSQL password")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Neo4j Graph Database
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="dev_password", description="Neo4j password")

    # Qdrant Vector Database
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    qdrant_collection_name: str = Field(
        default="research_knowledge",
        description="Qdrant collection name",
    )

    # Redis
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")

    # Application Settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=True, description="Enable debug mode")

    # Rate Limiting
    max_requests_per_minute: int = Field(default=50, description="Max API requests per minute")
    max_concurrent_agents: int = Field(default=10, description="Max concurrent active agents")

    # Agent Configuration
    default_agent_stage: str = Field(default="apprentice", description="Default agent starting stage")
    max_mentees_per_mentor: int = Field(default=3, description="Max students per mentor")
    promotion_cooldown_days: int = Field(default=30, description="Days between promotion attempts")

    # Learning Configuration
    min_papers_for_promotion: int = Field(default=5, description="Min papers read for first promotion")
    min_knowledge_depth: float = Field(default=0.7, description="Min knowledge depth for promotion")
    min_confidence_threshold: float = Field(default=0.65, description="Min confidence threshold")

    # Research Configuration
    max_experiment_runtime_seconds: int = Field(default=300, description="Max experiment execution time")
    enable_sandbox: bool = Field(default=True, description="Enable sandboxed execution")

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")

    # MCP Server Configuration
    literature_server_port: int = Field(default=5001, description="Literature server port")
    experiment_server_port: int = Field(default=5002, description="Experiment server port")
    knowledge_server_port: int = Field(default=5003, description="Knowledge server port")
    writing_server_port: int = Field(default=5004, description="Writing server port")

    # External APIs
    semantic_scholar_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API key")
    pubmed_api_key: Optional[str] = Field(default=None, description="PubMed API key")

    # Storage Paths
    data_dir: Path = Field(default=Path("./data"), description="Root data directory")
    papers_dir: Path = Field(default=Path("./data/papers"), description="Papers storage directory")
    experiments_dir: Path = Field(default=Path("./data/experiments"), description="Experiments directory")
    knowledge_graph_dir: Path = Field(
        default=Path("./data/knowledge_graph"),
        description="Knowledge graph data directory",
    )

    def model_post_init(self, __context: object) -> None:
        """Create directories if they don't exist."""
        for dir_path in [self.data_dir, self.papers_dir, self.experiments_dir, self.knowledge_graph_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    This function is cached to ensure we only load settings once.
    """
    return Settings()  # type: ignore[call-arg]
