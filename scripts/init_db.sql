-- Initialize PostgreSQL database with pgvector extension
-- This script is automatically run by docker-compose on first start

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enum types
CREATE TYPE agent_stage AS ENUM ('apprentice', 'practitioner', 'teacher', 'researcher', 'expert');
CREATE TYPE activity_type AS ENUM ('learning', 'teaching', 'research', 'review', 'collaboration');
CREATE TYPE outcome_type AS ENUM ('success', 'partial', 'failure');

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
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
);

-- Knowledge topics table
CREATE TABLE IF NOT EXISTS knowledge_topics (
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
);

-- Papers table
CREATE TABLE IF NOT EXISTS papers (
    paper_id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    published_date DATE,
    arxiv_id VARCHAR(50),
    doi VARCHAR(255),
    citations_count INTEGER DEFAULT 0,
    embedding vector(1536), -- OpenAI/Claude embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent papers relationship (read or authored)
CREATE TABLE IF NOT EXISTS agent_papers (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    paper_id VARCHAR(255) REFERENCES papers(paper_id) ON DELETE CASCADE,
    relationship VARCHAR(50) CHECK (relationship IN ('read', 'authored', 'reviewed')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, paper_id, relationship)
);

-- Experience log table
CREATE TABLE IF NOT EXISTS experience_log (
    log_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activity_type activity_type NOT NULL,
    description TEXT NOT NULL,
    outcome outcome_type NOT NULL,
    confidence_change FLOAT,
    metadata JSONB
);

-- Mentorship relationships table
CREATE TABLE IF NOT EXISTS mentorships (
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
);

-- Experiments table
CREATE TABLE IF NOT EXISTS experiments (
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
);

-- Create indexes for performance
CREATE INDEX idx_agents_stage ON agents(stage);
CREATE INDEX idx_agents_last_active ON agents(last_active);
CREATE INDEX idx_knowledge_agent ON knowledge_topics(agent_id);
CREATE INDEX idx_knowledge_name ON knowledge_topics(name);
CREATE INDEX idx_papers_arxiv ON papers(arxiv_id);
CREATE INDEX idx_agent_papers_agent ON agent_papers(agent_id);
CREATE INDEX idx_agent_papers_paper ON agent_papers(paper_id);
CREATE INDEX idx_experience_agent ON experience_log(agent_id);
CREATE INDEX idx_experience_timestamp ON experience_log(timestamp);
CREATE INDEX idx_experience_activity ON experience_log(activity_type);
CREATE INDEX idx_mentorships_mentor ON mentorships(mentor_id);
CREATE INDEX idx_mentorships_student ON mentorships(student_id);
CREATE INDEX idx_mentorships_active ON mentorships(is_active);
CREATE INDEX idx_experiments_agent ON experiments(agent_id);

-- Create vector similarity search index
CREATE INDEX ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent_system;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agent_system;

COMMIT;
