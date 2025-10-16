"""add_content_and_metadata_to_papers

Revision ID: b385e6b3f099
Revises: 698c1e702669
Create Date: 2025-10-16 12:28:24.228497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b385e6b3f099'
down_revision: Union[str, Sequence[str], None] = '698c1e702669'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add content column to papers table
    op.execute("""
        ALTER TABLE papers 
        ADD COLUMN IF NOT EXISTS content TEXT
    """)
    
    # Add metadata column to papers table (JSONB for structured data)
    op.execute("""
        ALTER TABLE papers 
        ADD COLUMN IF NOT EXISTS metadata JSONB
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove metadata column from papers table
    op.execute("""
        ALTER TABLE papers 
        DROP COLUMN IF EXISTS metadata
    """)
    
    # Remove content column from papers table
    op.execute("""
        ALTER TABLE papers 
        DROP COLUMN IF EXISTS content
    """)
