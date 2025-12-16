"""
Pipeline orchestration with deterministic state machine.

State transitions:
    PLAN_SCENE -> DRAFT_SCENE -> EXTRACT_FACTS -> RUN_CHECKS 
    -> (REVISE -> EXTRACT_FACTS -> RUN_CHECKS)* -> COMMIT
    
If max_attempts reached without passing checks, transitions to FAILED.
"""
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app import models, crud, schemas
from app.services import extraction, checks


class TaskType(str, Enum):
    """Pipeline task types."""
    PLAN_SCENE = "PLAN_SCENE"
    DRAFT_SCENE = "DRAFT_SCENE"
    EXTRACT_FACTS = "EXTRACT_FACTS"
    RUN_CHECKS = "RUN_CHECKS"
    REVISE = "REVISE"
    COMMIT = "COMMIT"


class IterationStatus(str, Enum):
    """Iteration statuses."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


# State machine transitions
NEXT_TASK = {
    TaskType.PLAN_SCENE: TaskType.DRAFT_SCENE,
    TaskType.DRAFT_SCENE: TaskType.EXTRACT_FACTS,
    TaskType.EXTRACT_FACTS: TaskType.RUN_CHECKS,
    # RUN_CHECKS branches: COMMIT if passed, REVISE if failed
    TaskType.REVISE: TaskType.EXTRACT_FACTS,
    # COMMIT is terminal
}


def get_redis_connection() -> Redis:
    """Get Redis connection from environment."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url)


def get_task_queue() -> Queue:
    """Get RQ task queue."""
    return Queue("novel-engine", connection=get_redis_connection())


def start_iteration(
    db: Session,
    scene_id: int,
    max_attempts: int = 3
) -> models.Iteration:
    """
    Start a new pipeline iteration for a scene.
    
    Creates the iteration and enqueues the first task (PLAN_SCENE).
    
    Args:
        db: Database session.
        scene_id: ID of the scene to process.
        max_attempts: Maximum revision attempts before failing.
        
    Returns:
        The created Iteration.
    """
    # Verify scene exists
    scene = crud.get_scene(db, scene_id)
    if not scene:
        raise ValueError(f"Scene {scene_id} not found")
    
    # Create iteration
    iteration = crud.create_iteration(db, scene_id)
    
    # Create first task
    first_task = crud.create_task(
        db,
        iteration_id=iteration.id,
        task_type=TaskType.PLAN_SCENE.value,
        input_jsonb={
            "scene_id": scene_id,
            "max_attempts": max_attempts,
            "current_attempt": 0
        }
    )
    
    # Update iteration status
    crud.update_iteration_status(db, iteration.id, IterationStatus.RUNNING.value)
    
    # Enqueue task for processing
    queue = get_task_queue()
    queue.enqueue(
        "app.services.pipeline.process_task",
        first_task.id,
        job_timeout="10m"
    )
    
    return iteration


def process_task(task_id: int) -> dict[str, Any]:
    """
    Process a pipeline task.
    
    This is the main RQ job handler. It executes the task
    and advances the state machine.
    
    Args:
        task_id: ID of the task to process.
        
    Returns:
        Task output dictionary.
    """
    from app.db import SessionLocal
    
    db = SessionLocal()
    try:
        task = crud.get_task(db, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Lock the task
        task.locked_at = datetime.now(timezone.utc)
        task.status = "running"
        task.attempts += 1
        db.commit()
        
        # Execute based on task type
        task_type = TaskType(task.task_type)
        handler = TASK_HANDLERS.get(task_type)
        
        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")
        
        try:
            output = handler(db, task)
            task.output_jsonb = output
            task.status = "completed"
            db.commit()
            
            # Advance state machine
            advance_state_machine(db, task)
            
            return output
            
        except Exception as e:
            task.status = "failed"
            task.output_jsonb = {"error": str(e)}
            db.commit()
            raise
            
    finally:
        db.close()


def advance_state_machine(db: Session, completed_task: models.Task) -> None:
    """
    Advance the state machine after a task completes.
    
    Determines the next task based on current state and
    creates/enqueues it.
    
    Args:
        db: Database session.
        completed_task: The task that just completed.
    """
    task_type = TaskType(completed_task.task_type)
    iteration = crud.get_iteration(db, completed_task.iteration_id)
    input_data = completed_task.input_jsonb
    output_data = completed_task.output_jsonb
    
    # Handle branching for RUN_CHECKS
    if task_type == TaskType.RUN_CHECKS:
        all_passed = output_data.get("all_passed", False)
        current_attempt = input_data.get("current_attempt", 0)
        max_attempts = input_data.get("max_attempts", 3)
        
        if all_passed:
            # All checks passed - go to COMMIT
            next_task_type = TaskType.COMMIT
        elif current_attempt >= max_attempts:
            # Max attempts reached - fail the iteration
            crud.update_iteration_status(db, iteration.id, IterationStatus.FAILED.value)
            return
        else:
            # Checks failed - go to REVISE
            next_task_type = TaskType.REVISE
    elif task_type == TaskType.COMMIT:
        # COMMIT is terminal - mark iteration as passed
        crud.update_iteration_status(db, iteration.id, IterationStatus.PASSED.value)
        return
    else:
        # Standard transition
        next_task_type = NEXT_TASK.get(task_type)
        if not next_task_type:
            return
    
    # Build input for next task
    next_input = {
        "scene_id": input_data.get("scene_id"),
        "max_attempts": input_data.get("max_attempts", 3),
        "current_attempt": input_data.get("current_attempt", 0),
    }
    
    # Pass through relevant data from previous task
    if "draft_id" in output_data:
        next_input["draft_id"] = output_data["draft_id"]
    if "plan" in output_data:
        next_input["plan"] = output_data["plan"]
    if "facts" in output_data:
        next_input["facts"] = output_data["facts"]
    if "findings" in output_data:
        next_input["findings"] = output_data["findings"]
    
    # Increment attempt counter for REVISE
    if next_task_type == TaskType.REVISE:
        next_input["current_attempt"] = next_input.get("current_attempt", 0) + 1
    
    # Create and enqueue next task
    next_task = crud.create_task(
        db,
        iteration_id=iteration.id,
        task_type=next_task_type.value,
        input_jsonb=next_input
    )
    
    queue = get_task_queue()
    queue.enqueue(
        "app.services.pipeline.process_task",
        next_task.id,
        job_timeout="10m"
    )


# ============================================================================
# Task Handlers
# ============================================================================

def handle_plan_scene(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle PLAN_SCENE task."""
    scene_id = task.input_jsonb.get("scene_id")
    scene = crud.get_scene(db, scene_id)
    
    if not scene:
        raise ValueError(f"Scene {scene_id} not found")
    
    # Generate plan using stub LLM function
    plan = extraction.generate_scene_plan(scene.card_jsonb)
    
    return {
        "scene_id": scene_id,
        "plan": plan
    }


def handle_draft_scene(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle DRAFT_SCENE task."""
    scene_id = task.input_jsonb.get("scene_id")
    plan = task.input_jsonb.get("plan", {})
    scene = crud.get_scene(db, scene_id)
    
    if not scene:
        raise ValueError(f"Scene {scene_id} not found")
    
    # Generate draft using stub LLM function
    draft_text = extraction.generate_draft(scene.card_jsonb, plan)
    
    # Create draft record (append-only)
    draft = crud.create_draft(
        db,
        scene_id=scene_id,
        draft=schemas.DraftCreate(text=draft_text)
    )
    
    return {
        "scene_id": scene_id,
        "draft_id": draft.id,
        "version": draft.version
    }


def handle_extract_facts(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle EXTRACT_FACTS task."""
    draft_id = task.input_jsonb.get("draft_id")
    draft = crud.get_draft(db, draft_id)
    
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")
    
    # Extract facts using stub LLM function
    fact_dicts = extraction.extract_facts(draft.text)
    
    # Store facts in database
    stored_facts = []
    for fact_dict in fact_dicts:
        fact = crud.create_fact(
            db,
            source_draft_id=draft_id,
            fact=schemas.FactBase(**fact_dict)
        )
        stored_facts.append({
            "id": fact.id,
            **fact_dict
        })
    
    # Generate summary
    summary = extraction.summarize_scene(draft.text)
    
    return {
        "draft_id": draft_id,
        "facts": stored_facts,
        "summary": summary
    }


def handle_run_checks(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle RUN_CHECKS task."""
    scene_id = task.input_jsonb.get("scene_id")
    draft_id = task.input_jsonb.get("draft_id")
    facts = task.input_jsonb.get("facts", [])
    
    draft = crud.get_draft(db, draft_id)
    scene = crud.get_scene(db, scene_id)
    
    if not draft or not scene:
        raise ValueError("Draft or scene not found")
    
    # Get project constraints and style bible
    constraints_models = crud.get_constraints(db, scene.project_id)
    constraints = [
        {
            "id": c.id,
            "constraint_type": c.constraint_type,
            "rule_jsonb": c.rule_jsonb,
            "severity": c.severity
        }
        for c in constraints_models
    ]
    
    # Get latest style bible
    style_bible = {}
    if scene.project.style_bibles:
        latest_bible = max(scene.project.style_bibles, key=lambda x: x.version)
        style_bible = latest_bible.content_jsonb
    
    # Run all checks
    check_results = checks.run_all_checks(
        draft_text=draft.text,
        facts=facts,
        constraints=constraints,
        style_bible=style_bible
    )
    
    # Store check runs
    all_passed = True
    all_findings = []
    
    for result in check_results:
        crud.create_check_run(
            db,
            iteration_id=task.iteration_id,
            draft_id=draft_id,
            check_type=result.check_type,
            passed=result.passed,
            findings_jsonb=result.findings
        )
        
        if not result.passed:
            all_passed = False
        all_findings.extend(result.findings)
    
    return {
        "draft_id": draft_id,
        "all_passed": all_passed,
        "findings": all_findings,
        "check_count": len(check_results)
    }


def handle_revise(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle REVISE task."""
    scene_id = task.input_jsonb.get("scene_id")
    draft_id = task.input_jsonb.get("draft_id")
    findings = task.input_jsonb.get("findings", [])
    
    draft = crud.get_draft(db, draft_id)
    
    if not draft:
        raise ValueError(f"Draft {draft_id} not found")
    
    # Revise draft using stub LLM function
    revised_text = extraction.revise_draft(draft.text, findings)
    
    # Create new draft version (append-only)
    new_draft = crud.create_draft(
        db,
        scene_id=scene_id,
        draft=schemas.DraftCreate(text=revised_text)
    )
    
    return {
        "scene_id": scene_id,
        "draft_id": new_draft.id,
        "version": new_draft.version,
        "previous_draft_id": draft_id
    }


def handle_commit(db: Session, task: models.Task) -> dict[str, Any]:
    """Handle COMMIT task."""
    scene_id = task.input_jsonb.get("scene_id")
    draft_id = task.input_jsonb.get("draft_id")
    
    # In a real system, this might:
    # - Mark the draft as "final"
    # - Update scene metadata
    # - Trigger downstream processes
    
    return {
        "scene_id": scene_id,
        "draft_id": draft_id,
        "committed": True,
        "message": "Draft committed successfully"
    }


# Task type to handler mapping
TASK_HANDLERS = {
    TaskType.PLAN_SCENE: handle_plan_scene,
    TaskType.DRAFT_SCENE: handle_draft_scene,
    TaskType.EXTRACT_FACTS: handle_extract_facts,
    TaskType.RUN_CHECKS: handle_run_checks,
    TaskType.REVISE: handle_revise,
    TaskType.COMMIT: handle_commit,
}
