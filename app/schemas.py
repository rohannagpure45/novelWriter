"""
Pydantic v2 schemas for the System-2 Novel Engine.
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


# ============================================================================
# Project Schemas
# ============================================================================

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# StyleBible Schemas
# ============================================================================

class StyleBibleBase(BaseModel):
    content_jsonb: dict[str, Any] = {}


class StyleBibleCreate(StyleBibleBase):
    pass


class StyleBibleRead(StyleBibleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    version: int
    created_at: datetime


# ============================================================================
# Character Schemas
# ============================================================================

class CharacterBase(BaseModel):
    name: str
    data_jsonb: dict[str, Any] = {}


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    data_jsonb: Optional[dict[str, Any]] = None


class CharacterRead(CharacterBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Location Schemas
# ============================================================================

class LocationBase(BaseModel):
    name: str
    data_jsonb: dict[str, Any] = {}


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    data_jsonb: Optional[dict[str, Any]] = None


class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Scene Schemas
# ============================================================================

class SceneBase(BaseModel):
    chapter_no: int
    scene_no: int
    pov_character_id: Optional[int] = None
    card_jsonb: dict[str, Any] = {}


class SceneCreate(SceneBase):
    pass


class SceneUpdate(BaseModel):
    chapter_no: Optional[int] = None
    scene_no: Optional[int] = None
    pov_character_id: Optional[int] = None
    card_jsonb: Optional[dict[str, Any]] = None


class SceneRead(SceneBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Draft Schemas (no update - append-only)
# ============================================================================

class DraftBase(BaseModel):
    text: str


class DraftCreate(DraftBase):
    pass


class DraftRead(DraftBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    scene_id: int
    version: int
    created_at: datetime


# ============================================================================
# Event Schemas
# ============================================================================

class EventBase(BaseModel):
    story_time: Optional[str] = None
    data_jsonb: dict[str, Any] = {}


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime


# ============================================================================
# Fact Schemas
# ============================================================================

class FactBase(BaseModel):
    fact_type: str
    subject_type: str
    subject_id: Optional[int] = None
    predicate: str
    object_jsonb: dict[str, Any] = {}
    confidence: float = 1.0


class FactCreate(FactBase):
    source_draft_id: int


class FactRead(FactBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    source_draft_id: int
    created_at: datetime


# ============================================================================
# Constraint Schemas
# ============================================================================

class ConstraintBase(BaseModel):
    constraint_type: str
    rule_jsonb: dict[str, Any] = {}
    severity: str = "error"


class ConstraintCreate(ConstraintBase):
    pass


class ConstraintRead(ConstraintBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime


# ============================================================================
# EntityLink Schemas
# ============================================================================

class EntityLinkBase(BaseModel):
    from_type: str
    from_id: int
    to_type: str
    to_id: int
    link_type: str
    props_jsonb: dict[str, Any] = {}
    valid_from_scene_id: Optional[int] = None
    valid_to_scene_id: Optional[int] = None


class EntityLinkCreate(EntityLinkBase):
    pass


class EntityLinkRead(EntityLinkBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


# ============================================================================
# CheckRun Schemas
# ============================================================================

class CheckRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    iteration_id: int
    draft_id: int
    check_type: str
    passed: bool
    findings_jsonb: list[dict[str, Any]]
    created_at: datetime


# ============================================================================
# Task Schemas
# ============================================================================

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    iteration_id: int
    task_type: str
    status: str
    input_jsonb: dict[str, Any]
    output_jsonb: dict[str, Any]
    attempts: int
    locked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Iteration Schemas
# ============================================================================

class IterationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    scene_id: int
    iteration_no: int
    status: str
    created_at: datetime
    updated_at: datetime
    check_runs: list[CheckRunRead] = []
    tasks: list[TaskRead] = []


# ============================================================================
# Pipeline Schemas
# ============================================================================

class PipelineRunRequest(BaseModel):
    max_attempts: int = 3
    draft_id: Optional[int] = None


class PipelineRunResponse(BaseModel):
    iteration_id: int
    status: str
    message: str
