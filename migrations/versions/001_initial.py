"""Initial schema with all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_id'), 'project', ['id'], unique=False)

    # Create style_bible table
    op.create_table(
        'style_bible',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'version', name='uq_style_bible_project_version')
    )
    op.create_index(op.f('ix_style_bible_id'), 'style_bible', ['id'], unique=False)

    # Create character table
    op.create_table(
        'character',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('data_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_character_id'), 'character', ['id'], unique=False)

    # Create location table
    op.create_table(
        'location',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('data_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_id'), 'location', ['id'], unique=False)

    # Create scene table
    op.create_table(
        'scene',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('chapter_no', sa.Integer(), nullable=False),
        sa.Column('scene_no', sa.Integer(), nullable=False),
        sa.Column('pov_character_id', sa.Integer(), nullable=True),
        sa.Column('card_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pov_character_id'], ['character.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'chapter_no', 'scene_no', name='uq_scene_ordering')
    )
    op.create_index(op.f('ix_scene_id'), 'scene', ['id'], unique=False)
    op.create_index('ix_scene_ordering', 'scene', ['project_id', 'chapter_no', 'scene_no'], unique=False)

    # Create draft table
    op.create_table(
        'draft',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['scene_id'], ['scene.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scene_id', 'version', name='uq_draft_scene_version')
    )
    op.create_index(op.f('ix_draft_id'), 'draft', ['id'], unique=False)

    # Create event table
    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('story_time', sa.String(length=100), nullable=True),
        sa.Column('data_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_id'), 'event', ['id'], unique=False)

    # Create fact table
    op.create_table(
        'fact',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_draft_id', sa.Integer(), nullable=False),
        sa.Column('fact_type', sa.String(length=50), nullable=False),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('predicate', sa.String(length=255), nullable=False),
        sa.Column('object_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_draft_id'], ['draft.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fact_id'), 'fact', ['id'], unique=False)

    # Create constraint table
    op.create_table(
        'constraint',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('constraint_type', sa.String(length=50), nullable=False),
        sa.Column('rule_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='error'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_constraint_id'), 'constraint', ['id'], unique=False)

    # Create entity_link table
    op.create_table(
        'entity_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_type', sa.String(length=50), nullable=False),
        sa.Column('from_id', sa.Integer(), nullable=False),
        sa.Column('to_type', sa.String(length=50), nullable=False),
        sa.Column('to_id', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.String(length=50), nullable=False),
        sa.Column('props_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('valid_from_scene_id', sa.Integer(), nullable=True),
        sa.Column('valid_to_scene_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['valid_from_scene_id'], ['scene.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['valid_to_scene_id'], ['scene.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entity_link_id'), 'entity_link', ['id'], unique=False)
    op.create_index('ix_entity_link_from', 'entity_link', ['from_type', 'from_id'], unique=False)
    op.create_index('ix_entity_link_to', 'entity_link', ['to_type', 'to_id'], unique=False)

    # Create iteration table
    op.create_table(
        'iteration',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('iteration_no', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['scene_id'], ['scene.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iteration_id'), 'iteration', ['id'], unique=False)

    # Create check_run table
    op.create_table(
        'check_run',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iteration_id', sa.Integer(), nullable=False),
        sa.Column('draft_id', sa.Integer(), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('findings_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['draft_id'], ['draft.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['iteration_id'], ['iteration.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_check_run_id'), 'check_run', ['id'], unique=False)

    # Create task table
    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('iteration_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('input_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['iteration_id'], ['iteration.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_id'), 'task', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('task')
    op.drop_table('check_run')
    op.drop_table('iteration')
    op.drop_table('entity_link')
    op.drop_table('constraint')
    op.drop_table('fact')
    op.drop_table('event')
    op.drop_table('draft')
    op.drop_table('scene')
    op.drop_table('location')
    op.drop_table('character')
    op.drop_table('style_bible')
    op.drop_table('project')
