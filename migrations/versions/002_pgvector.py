"""Add pgvector support

Revision ID: 002_pgvector
Revises: 001_initial
Create Date: 2024-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_pgvector'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add pgvector extension and embedding column to fact table.
    
    This migration is designed to work with or without pgvector installed.
    If pgvector is not available, the extension creation will fail silently
    and the embedding column won't be added.
    """
    # Try to create the vector extension
    # This will fail if pgvector is not installed, but we catch the error
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
        
        # Only add the embedding column if the extension was created successfully
        # Using raw SQL because SQLAlchemy doesn't natively support the vector type
        op.execute('''
            ALTER TABLE fact 
            ADD COLUMN IF NOT EXISTS embedding vector(1536)
        ''')
        
        # Create an index for similarity search (optional, for performance)
        op.execute('''
            CREATE INDEX IF NOT EXISTS ix_fact_embedding 
            ON fact 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        ''')
        
    except Exception as e:
        # pgvector not available - this is fine, the system works without embeddings
        print(f"Note: pgvector extension not available ({e}). Embeddings disabled.")


def downgrade() -> None:
    """Remove pgvector support."""
    try:
        op.execute('DROP INDEX IF EXISTS ix_fact_embedding')
        op.execute('ALTER TABLE fact DROP COLUMN IF EXISTS embedding')
        # Note: We don't drop the extension as other tables might use it
    except Exception:
        pass  # Extension wasn't installed
