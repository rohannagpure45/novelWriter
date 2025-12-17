"""
FastAPI application for the System-2 Novel Engine.
"""
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app import crud, schemas, models
from app.services import pipeline


app = FastAPI(
    title="System-2 Novel Engine",
    description="A production-minded MVP for novel writing with relational graph index and iterative drafting pipeline.",
    version="0.1.0"
)

# Mount Static Files
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the single-page application."""
    index_path = STATIC_DIR / "index.html"
    with open(index_path, "r") as f:
        return f.read()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "novel-engine"}


# ============================================================================
# Project Endpoints
# ============================================================================

@app.post("/projects", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    return crud.create_project(db, project)


@app.get("/projects", response_model=list[schemas.ProjectRead])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects."""
    return crud.get_projects(db, skip=skip, limit=limit)


@app.get("/projects/{project_id}", response_model=schemas.ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a project by ID."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project."""
    if not crud.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return None


# ============================================================================
# Character Endpoints
# ============================================================================

@app.post(
    "/projects/{project_id}/characters",
    response_model=schemas.CharacterRead,
    status_code=status.HTTP_201_CREATED
)
def create_character(
    project_id: int,
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db)
):
    """Create a new character in a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.create_character(db, project_id, character)


@app.get("/projects/{project_id}/characters", response_model=list[schemas.CharacterRead])
def list_characters(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all characters in a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_characters(db, project_id, skip=skip, limit=limit)


@app.get("/characters/{character_id}", response_model=schemas.CharacterRead)
def get_character(character_id: int, db: Session = Depends(get_db)):
    """Get a character by ID."""
    character = crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@app.put("/characters/{character_id}", response_model=schemas.CharacterRead)
def update_character(
    character_id: int,
    character: schemas.CharacterUpdate,
    db: Session = Depends(get_db)
):
    """Update a character."""
    updated = crud.update_character(db, character_id, character)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return updated


@app.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: int, db: Session = Depends(get_db)):
    """Delete a character."""
    if not crud.delete_character(db, character_id):
        raise HTTPException(status_code=404, detail="Character not found")
    return None


# ============================================================================
# Scene Endpoints
# ============================================================================

@app.post(
    "/projects/{project_id}/scenes",
    response_model=schemas.SceneRead,
    status_code=status.HTTP_201_CREATED
)
def create_scene(
    project_id: int,
    scene: schemas.SceneCreate,
    db: Session = Depends(get_db)
):
    """Create a new scene in a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.create_scene(db, project_id, scene)


@app.get("/projects/{project_id}/scenes", response_model=list[schemas.SceneRead])
def list_scenes(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all scenes in a project, ordered by chapter and scene number."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_scenes(db, project_id, skip=skip, limit=limit)


@app.get("/scenes/{scene_id}", response_model=schemas.SceneRead)
def get_scene(scene_id: int, db: Session = Depends(get_db)):
    """Get a scene by ID."""
    scene = crud.get_scene(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@app.put("/scenes/{scene_id}", response_model=schemas.SceneRead)
def update_scene(
    scene_id: int,
    scene: schemas.SceneUpdate,
    db: Session = Depends(get_db)
):
    """Update a scene."""
    updated = crud.update_scene(db, scene_id, scene)
    if not updated:
        raise HTTPException(status_code=404, detail="Scene not found")
    return updated


@app.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    """Delete a scene."""
    if not crud.delete_scene(db, scene_id):
        raise HTTPException(status_code=404, detail="Scene not found")
    return None


# ============================================================================
# Draft Endpoints (append-only - no update/delete)
# ============================================================================

@app.post(
    "/scenes/{scene_id}/drafts",
    response_model=schemas.DraftRead,
    status_code=status.HTTP_201_CREATED
)
def create_draft(
    scene_id: int,
    draft: schemas.DraftCreate,
    db: Session = Depends(get_db)
):
    """Create a new draft for a scene (append-only)."""
    scene = crud.get_scene(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return crud.create_draft(db, scene_id, draft)


@app.get("/scenes/{scene_id}/drafts", response_model=list[schemas.DraftRead])
def list_drafts(
    scene_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all drafts for a scene, ordered by version descending."""
    scene = crud.get_scene(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return crud.get_drafts(db, scene_id, skip=skip, limit=limit)


@app.get("/drafts/{draft_id}", response_model=schemas.DraftRead)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    """Get a draft by ID."""
    draft = crud.get_draft(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


# ============================================================================
# Pipeline Endpoints
# ============================================================================

@app.post(
    "/pipeline/scenes/{scene_id}/run",
    response_model=schemas.PipelineRunResponse
)
def run_pipeline(
    scene_id: int,
    request: schemas.PipelineRunRequest = None,
    db: Session = Depends(get_db)
):
    """
    Start a pipeline iteration for a scene.
    
    Creates an iteration and enqueues tasks until checks pass or max_attempts reached.
    """
    request = request or schemas.PipelineRunRequest()
    
    scene = crud.get_scene(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Validate draft_id if provided
    if request.draft_id:
        draft = crud.get_draft(db, request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        if draft.scene_id != scene_id:
            raise HTTPException(status_code=400, detail="Draft does not belong to this scene")
    
    try:
        iteration = pipeline.start_iteration(
            db,
            scene_id=scene_id,
            max_attempts=request.max_attempts,
            draft_id=request.draft_id
        )
        
        return schemas.PipelineRunResponse(
            iteration_id=iteration.id,
            status=iteration.status,
            message=f"Pipeline started for scene {scene_id}, iteration {iteration.iteration_no}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/pipeline/iterations/{iteration_id}",
    response_model=schemas.IterationRead
)
def get_iteration(iteration_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a pipeline iteration.
    
    Includes the latest draft and all check runs.
    """
    iteration = crud.get_iteration(db, iteration_id)
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")
    return iteration


# ============================================================================
# Additional Utility Endpoints
# ============================================================================

@app.post(
    "/projects/{project_id}/constraints",
    response_model=schemas.ConstraintRead,
    status_code=status.HTTP_201_CREATED
)
def create_constraint(
    project_id: int,
    constraint: schemas.ConstraintCreate,
    db: Session = Depends(get_db)
):
    """Create a new constraint for a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.create_constraint(db, project_id, constraint)


@app.get("/projects/{project_id}/constraints", response_model=list[schemas.ConstraintRead])
def list_constraints(project_id: int, db: Session = Depends(get_db)):
    """List all constraints for a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_constraints(db, project_id)
