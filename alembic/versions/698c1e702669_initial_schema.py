"""initial_schema

Revision ID: 698c1e702669
Revises: 
Create Date: 2025-10-08 19:10:44.957338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '698c1e702669'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create enum types
    op.execute("""
        CREATE TYPE agent_stage AS ENUM ('apprentice', 'practitioner', 'teacher', 'researcher', 'expert')
    """)
    op.execute("""
        CREATE TYPE activity_type AS ENUM ('learning', 'teaching', 'research', 'review', 'collaboration')
    """)
    op.execute("""
        CREATE TYPE outcome_type AS ENUM ('success', 'partial', 'failure')
    """)
    
    # Create agents table
    op.execute("""
        CREATE TABLE agents (
            agent_id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            stage agent_stage NOT NULL DEFAULT 'apprentice',
            specialization VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            reputation_overall FLOAT DEFAULT 50.0,
            reputation_teaching FLOAT DEFAULT 50.0,
            reputation_research FLOAT DEFAULT 50.0,
            reputation_review FLOAT DEFAULT 50.0,
            reputation_collaboration FLOAT DEFAULT 50.0,
            total_experience_points INTEGER DEFAULT 0,
            promotion_count INTEGER DEFAULT 0
        )
    """)
    
    # Create knowledge topics table
    op.execute("""
        CREATE TABLE knowledge_topics (
            topic_id UUID PRIMARY KEY,
            agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            depth_score FLOAT CHECK (depth_score >= 0 AND depth_score <= 1),
            breadth_score FLOAT CHECK (breadth_score >= 0 AND breadth_score <= 1),
            confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
            validated BOOLEAN DEFAULT FALSE,
            validation_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(agent_id, name)
        )
    """)
    
    # Create papers table
    op.execute("""
        CREATE TABLE papers (
            paper_id VARCHAR(255) PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT[],
            abstract TEXT,
            published_date DATE,
            arxiv_id VARCHAR(50),
            doi VARCHAR(255),
            citations_count INTEGER DEFAULT 0,
            embedding vector(1536),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Create agent papers relationship
    op.execute("""
        CREATE TABLE agent_papers (
            id SERIAL PRIMARY KEY,
            agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            paper_id VARCHAR(255) REFERENCES papers(paper_id) ON DELETE CASCADE,
            relationship VARCHAR(50) CHECK (relationship IN ('read', 'authored', 'reviewed')),
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(agent_id, paper_id, relationship)
        )
    """)
    
    # Create experience log table
    op.execute("""
        CREATE TABLE experience_log (
            log_id UUID PRIMARY KEY,
            agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            activity_type activity_type NOT NULL,
            description TEXT NOT NULL,
            outcome outcome_type NOT NULL,
            confidence_change FLOAT,
            metadata JSONB
        )
    """)
    
    # Create mentorships table
    op.execute("""
        CREATE TABLE mentorships (
            relation_id UUID PRIMARY KEY,
            mentor_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            student_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            ended_at TIMESTAMP WITH TIME ZONE,
            sessions_count INTEGER DEFAULT 0,
            student_progress FLOAT DEFAULT 0.0,
            mentor_rating FLOAT,
            is_active BOOLEAN DEFAULT TRUE,
            topics TEXT[]
        )
    """)
    
    # Create experiments table
    op.execute("""
        CREATE TABLE experiments (
            experiment_id UUID PRIMARY KEY,
            agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            hypothesis TEXT,
            code TEXT,
            results JSONB,
            success BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            runtime_seconds FLOAT
        )
    """)
    
    # Create indexes
    op.create_index('idx_agents_stage', 'agents', ['stage'])
    op.create_index('idx_agents_last_active', 'agents', ['last_active'])
    op.create_index('idx_knowledge_agent', 'knowledge_topics', ['agent_id'])
    op.create_index('idx_knowledge_name', 'knowledge_topics', ['name'])
    op.create_index('idx_papers_arxiv', 'papers', ['arxiv_id'])
    op.create_index('idx_agent_papers_agent', 'agent_papers', ['agent_id'])
    op.create_index('idx_agent_papers_paper', 'agent_papers', ['paper_id'])
    op.create_index('idx_experience_agent', 'experience_log', ['agent_id'])
    op.create_index('idx_experience_timestamp', 'experience_log', ['timestamp'])
    op.create_index('idx_experience_activity', 'experience_log', ['activity_type'])
    op.create_index('idx_mentorships_mentor', 'mentorships', ['mentor_id'])
    op.create_index('idx_mentorships_student', 'mentorships', ['student_id'])
    op.create_index('idx_mentorships_active', 'mentorships', ['is_active'])
    op.create_index('idx_experiments_agent', 'experiments', ['agent_id'])
    
    # Create vector similarity search index
    op.execute("CREATE INDEX ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_experiments_agent', table_name='experiments')
    op.drop_index('idx_mentorships_active', table_name='mentorships')
    op.drop_index('idx_mentorships_student', table_name='mentorships')
    op.drop_index('idx_mentorships_mentor', table_name='mentorships')
    op.drop_index('idx_experience_activity', table_name='experience_log')
    op.drop_index('idx_experience_timestamp', table_name='experience_log')
    op.drop_index('idx_experience_agent', table_name='experience_log')
    op.drop_index('idx_agent_papers_paper', table_name='agent_papers')
    op.drop_index('idx_agent_papers_agent', table_name='agent_papers')
    op.drop_index('idx_papers_arxiv', table_name='papers')
    op.drop_index('idx_knowledge_name', table_name='knowledge_topics')
    op.drop_index('idx_knowledge_agent', table_name='knowledge_topics')
    op.drop_index('idx_agents_last_active', table_name='agents')
    op.drop_index('idx_agents_stage', table_name='agents')
    
    # Drop tables
    op.drop_table('experiments')
    op.drop_table('mentorships')
    op.drop_table('experience_log')
    op.drop_table('agent_papers')
    op.drop_table('papers')
    op.drop_table('knowledge_topics')
    op.drop_table('agents')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS outcome_type")
    op.execute("DROP TYPE IF EXISTS activity_type")
    op.execute("DROP TYPE IF EXISTS agent_stage")
    
    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS vector")
