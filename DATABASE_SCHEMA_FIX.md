# Database Schema Fix - Papers Table

## Issue
The application was failing with the error:
```
column "content" of relation "papers" does not exist
```

This occurred when trying to save papers to the database because the `save_paper` method in `src/storage/state_store.py` was attempting to insert into `content` and `metadata` columns that didn't exist in the `papers` table.

## Root Cause
1. The initial database schema (migration `698c1e702669_initial_schema.py`) created a `papers` table without `content` and `metadata` columns
2. The code in `state_store.py` was attempting to save to these non-existent columns
3. Additionally, the `alembic.ini` configuration had the wrong database port (5432 instead of 5433)

## Solution Applied

### 1. Fixed Database Connection
Updated `alembic.ini` to use the correct PostgreSQL port:
- Changed from: `postgresql://agent_system:dev_password@127.0.0.1:5432/research_collective`
- Changed to: `postgresql://agent_system:dev_password@127.0.0.1:5433/research_collective`

### 2. Created New Migration
Created Alembic migration `b385e6b3f099_add_content_and_metadata_to_papers.py` to add missing columns:
- Added `content` column of type TEXT (for storing full paper content)
- Added `metadata` column of type JSONB (for storing structured metadata like authors, venue, etc.)

### 3. Applied Migration
1. Stamped the database with the initial migration version: `alembic stamp 698c1e702669`
2. Ran the upgrade: `alembic upgrade head`

## Current Schema
The `papers` table now includes:
```sql
 paper_id        | character varying(255)   | PRIMARY KEY
 title           | text                     | NOT NULL
 authors         | text[]                   |
 abstract        | text                     |
 published_date  | date                     |
 arxiv_id        | character varying(50)    |
 doi             | character varying(255)   |
 citations_count | integer                  | DEFAULT 0
 embedding       | vector(1536)             |
 created_at      | timestamp with time zone | DEFAULT NOW()
 content         | text                     | ← NEW
 metadata        | jsonb                    | ← NEW
```

## Files Modified
1. `alembic.ini` - Fixed database port
2. `alembic/versions/b385e6b3f099_add_content_and_metadata_to_papers.py` - New migration created

## Result
The `save_paper` method in `src/storage/state_store.py` can now successfully insert papers with content and metadata into the database.

## Date
October 16, 2025
