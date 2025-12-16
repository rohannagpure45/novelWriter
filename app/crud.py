"""
CRUD operations for the System-2 Novel Engine.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas


# ============================================================================
# Project CRUD
# ============================================================================

def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()


def delete_project(db: Session, project_id: int) -> bool:
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False


# ============================================================================
# Character CRUD
# ============================================================================

def create_character(
    db: Session, project_id: int, character: schemas.CharacterCreate
) -> models.Character:
    db_character = models.Character(project_id=project_id, **character.model_dump())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


def get_character(db: Session, character_id: int) -> Optional[models.Character]:
    return db.query(models.Character).filter(models.Character.id == character_id).first()


def get_characters(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> list[models.Character]:
    return (
        db.query(models.Character)
        .filter(models.Character.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_character(
    db: Session, character_id: int, character: schemas.CharacterUpdate
) -> Optional[models.Character]:
    db_character = get_character(db, character_id)
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_character, field, value)
        db.commit()
        db.refresh(db_character)
    return db_character


def delete_character(db: Session, character_id: int) -> bool:
    db_character = get_character(db, character_id)
    if db_character:
        db.delete(db_character)
        db.commit()
        return True
    return False


# ============================================================================
# Location CRUD
# ============================================================================

def create_location(
    db: Session, project_id: int, location: schemas.LocationCreate
) -> models.Location:
    db_location = models.Location(project_id=project_id, **location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def get_location(db: Session, location_id: int) -> Optional[models.Location]:
    return db.query(models.Location).filter(models.Location.id == location_id).first()


def get_locations(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> list[models.Location]:
    return (
        db.query(models.Location)
        .filter(models.Location.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_location(
    db: Session, location_id: int, location: schemas.LocationUpdate
) -> Optional[models.Location]:
    db_location = get_location(db, location_id)
    if db_location:
        update_data = location.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_location, field, value)
        db.commit()
        db.refresh(db_location)
    return db_location


def delete_location(db: Session, location_id: int) -> bool:
    db_location = get_location(db, location_id)
    if db_location:
        db.delete(db_location)
        db.commit()
        return True
    return False


# ============================================================================
# Scene CRUD
# ============================================================================

def create_scene(
    db: Session, project_id: int, scene: schemas.SceneCreate
) -> models.Scene:
    db_scene = models.Scene(project_id=project_id, **scene.model_dump())
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    return db_scene


def get_scene(db: Session, scene_id: int) -> Optional[models.Scene]:
    return db.query(models.Scene).filter(models.Scene.id == scene_id).first()


def get_scenes(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> list[models.Scene]:
    return (
        db.query(models.Scene)
        .filter(models.Scene.project_id == project_id)
        .order_by(models.Scene.chapter_no, models.Scene.scene_no)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_scene(
    db: Session, scene_id: int, scene: schemas.SceneUpdate
) -> Optional[models.Scene]:
    db_scene = get_scene(db, scene_id)
    if db_scene:
        update_data = scene.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_scene, field, value)
        db.commit()
        db.refresh(db_scene)
    return db_scene


def delete_scene(db: Session, scene_id: int) -> bool:
    db_scene = get_scene(db, scene_id)
    if db_scene:
        db.delete(db_scene)
        db.commit()
        return True
    return False


# ============================================================================
# Draft CRUD (append-only - no update/delete)
# ============================================================================

def create_draft(
    db: Session, scene_id: int, draft: schemas.DraftCreate
) -> models.Draft:
    # Get next version number
    max_version = (
        db.query(func.max(models.Draft.version))
        .filter(models.Draft.scene_id == scene_id)
        .scalar()
    )
    next_version = (max_version or 0) + 1
    
    db_draft = models.Draft(
        scene_id=scene_id,
        version=next_version,
        text=draft.text
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft


def get_draft(db: Session, draft_id: int) -> Optional[models.Draft]:
    return db.query(models.Draft).filter(models.Draft.id == draft_id).first()


def get_drafts(
    db: Session, scene_id: int, skip: int = 0, limit: int = 100
) -> list[models.Draft]:
    return (
        db.query(models.Draft)
        .filter(models.Draft.scene_id == scene_id)
        .order_by(models.Draft.version.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_latest_draft(db: Session, scene_id: int) -> Optional[models.Draft]:
    return (
        db.query(models.Draft)
        .filter(models.Draft.scene_id == scene_id)
        .order_by(models.Draft.version.desc())
        .first()
    )


# ============================================================================
# Iteration CRUD
# ============================================================================

def create_iteration(db: Session, scene_id: int) -> models.Iteration:
    # Get next iteration number
    max_iteration = (
        db.query(func.max(models.Iteration.iteration_no))
        .filter(models.Iteration.scene_id == scene_id)
        .scalar()
    )
    next_iteration = (max_iteration or 0) + 1
    
    db_iteration = models.Iteration(
        scene_id=scene_id,
        iteration_no=next_iteration,
        status="pending"
    )
    db.add(db_iteration)
    db.commit()
    db.refresh(db_iteration)
    return db_iteration


def get_iteration(db: Session, iteration_id: int) -> Optional[models.Iteration]:
    return db.query(models.Iteration).filter(models.Iteration.id == iteration_id).first()


def update_iteration_status(
    db: Session, iteration_id: int, status: str
) -> Optional[models.Iteration]:
    db_iteration = get_iteration(db, iteration_id)
    if db_iteration:
        db_iteration.status = status
        db.commit()
        db.refresh(db_iteration)
    return db_iteration


# ============================================================================
# Task CRUD
# ============================================================================

def create_task(
    db: Session,
    iteration_id: int,
    task_type: str,
    input_jsonb: dict = None
) -> models.Task:
    db_task = models.Task(
        iteration_id=iteration_id,
        task_type=task_type,
        status="pending",
        input_jsonb=input_jsonb or {}
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def get_pending_task(db: Session, iteration_id: int) -> Optional[models.Task]:
    return (
        db.query(models.Task)
        .filter(
            models.Task.iteration_id == iteration_id,
            models.Task.status == "pending"
        )
        .order_by(models.Task.id)
        .first()
    )


def update_task(
    db: Session,
    task_id: int,
    status: str = None,
    output_jsonb: dict = None,
    attempts: int = None
) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if db_task:
        if status is not None:
            db_task.status = status
        if output_jsonb is not None:
            db_task.output_jsonb = output_jsonb
        if attempts is not None:
            db_task.attempts = attempts
        db.commit()
        db.refresh(db_task)
    return db_task


# ============================================================================
# CheckRun CRUD
# ============================================================================

def create_check_run(
    db: Session,
    iteration_id: int,
    draft_id: int,
    check_type: str,
    passed: bool,
    findings_jsonb: list = None
) -> models.CheckRun:
    db_check_run = models.CheckRun(
        iteration_id=iteration_id,
        draft_id=draft_id,
        check_type=check_type,
        passed=passed,
        findings_jsonb=findings_jsonb or []
    )
    db.add(db_check_run)
    db.commit()
    db.refresh(db_check_run)
    return db_check_run


# ============================================================================
# Fact CRUD
# ============================================================================

def create_fact(
    db: Session,
    source_draft_id: int,
    fact: schemas.FactBase
) -> models.Fact:
    db_fact = models.Fact(
        source_draft_id=source_draft_id,
        **fact.model_dump()
    )
    db.add(db_fact)
    db.commit()
    db.refresh(db_fact)
    return db_fact


def get_facts_for_draft(db: Session, draft_id: int) -> list[models.Fact]:
    return (
        db.query(models.Fact)
        .filter(models.Fact.source_draft_id == draft_id)
        .all()
    )


# ============================================================================
# Constraint CRUD
# ============================================================================

def create_constraint(
    db: Session,
    project_id: int,
    constraint: schemas.ConstraintCreate
) -> models.Constraint:
    db_constraint = models.Constraint(
        project_id=project_id,
        **constraint.model_dump()
    )
    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint)
    return db_constraint


def get_constraints(db: Session, project_id: int) -> list[models.Constraint]:
    return (
        db.query(models.Constraint)
        .filter(models.Constraint.project_id == project_id)
        .all()
    )
