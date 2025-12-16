"""
SQLAlchemy models for the System-2 Novel Engine.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Boolean, Float, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db import Base


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Project(Base):
    """A novel project."""
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    style_bibles = relationship("StyleBible", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="project", cascade="all, delete-orphan")
    constraints = relationship("Constraint", back_populates="project", cascade="all, delete-orphan")


class StyleBible(Base):
    """Versioned style guide for a project."""
    __tablename__ = "style_bible"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    content_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", back_populates="style_bibles")

    __table_args__ = (
        UniqueConstraint("project_id", "version", name="uq_style_bible_project_version"),
    )


class Character(Base):
    """A character in the novel."""
    __tablename__ = "character"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    data_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="characters")
    pov_scenes = relationship("Scene", back_populates="pov_character")


class Location(Base):
    """A location in the novel."""
    __tablename__ = "location"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    data_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="locations")


class Scene(Base):
    """A scene in the novel."""
    __tablename__ = "scene"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    chapter_no = Column(Integer, nullable=False)
    scene_no = Column(Integer, nullable=False)
    pov_character_id = Column(Integer, ForeignKey("character.id", ondelete="SET NULL"), nullable=True)
    card_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="scenes")
    pov_character = relationship("Character", back_populates="pov_scenes")
    drafts = relationship("Draft", back_populates="scene", cascade="all, delete-orphan")
    iterations = relationship("Iteration", back_populates="scene", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_scene_ordering", "project_id", "chapter_no", "scene_no"),
        UniqueConstraint("project_id", "chapter_no", "scene_no", name="uq_scene_ordering"),
    )


class Draft(Base):
    """
    An immutable draft of a scene.
    Append-only: no updates or deletes allowed.
    """
    __tablename__ = "draft"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scene.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    scene = relationship("Scene", back_populates="drafts")
    facts = relationship("Fact", back_populates="source_draft", cascade="all, delete-orphan")
    check_runs = relationship("CheckRun", back_populates="draft", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("scene_id", "version", name="uq_draft_scene_version"),
    )


class Event(Base):
    """A story event with timeline positioning."""
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    story_time = Column(String(100), nullable=True)  # Flexible story-time representation
    data_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", back_populates="events")


class Fact(Base):
    """
    An extracted fact from a draft.
    Used for continuity checking.
    """
    __tablename__ = "fact"

    id = Column(Integer, primary_key=True, index=True)
    source_draft_id = Column(Integer, ForeignKey("draft.id", ondelete="CASCADE"), nullable=False)
    fact_type = Column(String(50), nullable=False)  # e.g., "character_trait", "location_detail"
    subject_type = Column(String(50), nullable=False)  # e.g., "character", "location"
    subject_id = Column(Integer, nullable=True)  # FK to the subject entity
    predicate = Column(String(255), nullable=False)  # e.g., "has_eye_color", "is_located_in"
    object_jsonb = Column(JSONB, nullable=False, default=dict)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    # Optional: embedding for semantic search (added via migration)
    # embedding = Column(Vector(1536), nullable=True)

    source_draft = relationship("Draft", back_populates="facts")


class Constraint(Base):
    """A rule/constraint that drafts must satisfy."""
    __tablename__ = "constraint"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    constraint_type = Column(String(50), nullable=False)  # e.g., "continuity", "style"
    rule_jsonb = Column(JSONB, nullable=False, default=dict)
    severity = Column(String(20), nullable=False, default="error")  # error, warning, info
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", back_populates="constraints")


class EntityLink(Base):
    """
    Universal graph edges between entities.
    Supports temporal validity via scene references.
    """
    __tablename__ = "entity_link"

    id = Column(Integer, primary_key=True, index=True)
    from_type = Column(String(50), nullable=False)
    from_id = Column(Integer, nullable=False)
    to_type = Column(String(50), nullable=False)
    to_id = Column(Integer, nullable=False)
    link_type = Column(String(50), nullable=False)  # e.g., "knows", "located_at", "owns"
    props_jsonb = Column(JSONB, nullable=False, default=dict)
    valid_from_scene_id = Column(Integer, ForeignKey("scene.id", ondelete="SET NULL"), nullable=True)
    valid_to_scene_id = Column(Integer, ForeignKey("scene.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_entity_link_from", "from_type", "from_id"),
        Index("ix_entity_link_to", "to_type", "to_id"),
    )


class Iteration(Base):
    """A pipeline iteration for a scene."""
    __tablename__ = "iteration"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scene.id", ondelete="CASCADE"), nullable=False)
    iteration_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, passed, failed
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    scene = relationship("Scene", back_populates="iterations")
    check_runs = relationship("CheckRun", back_populates="iteration", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="iteration", cascade="all, delete-orphan")


class CheckRun(Base):
    """A check run within an iteration."""
    __tablename__ = "check_run"

    id = Column(Integer, primary_key=True, index=True)
    iteration_id = Column(Integer, ForeignKey("iteration.id", ondelete="CASCADE"), nullable=False)
    draft_id = Column(Integer, ForeignKey("draft.id", ondelete="CASCADE"), nullable=False)
    check_type = Column(String(50), nullable=False)  # e.g., "continuity", "style"
    passed = Column(Boolean, nullable=False, default=False)
    findings_jsonb = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    iteration = relationship("Iteration", back_populates="check_runs")
    draft = relationship("Draft", back_populates="check_runs")


class Task(Base):
    """A pipeline task within an iteration."""
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True)
    iteration_id = Column(Integer, ForeignKey("iteration.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), nullable=False)  # PLAN_SCENE, DRAFT_SCENE, etc.
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    input_jsonb = Column(JSONB, nullable=False, default=dict)
    output_jsonb = Column(JSONB, nullable=False, default=dict)
    attempts = Column(Integer, nullable=False, default=0)
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    iteration = relationship("Iteration", back_populates="tasks")
