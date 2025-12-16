# System-2 Novel Engine

A production-minded MVP for novel writing with a relational graph index and iterative drafting pipeline.

## Tech Stack

- **Python 3.12** - Runtime
- **FastAPI** - API framework
- **SQLAlchemy 2.x** - ORM
- **Alembic** - Database migrations
- **Postgres 16** - Database (with pgvector support)
- **RQ + Redis** - Task queue
- **Pydantic v2** - Data validation

## Architecture

### Pipeline State Machine

```
PLAN_SCENE → DRAFT_SCENE → EXTRACT_FACTS → RUN_CHECKS
                                              ↓
                                    ┌─────────┴─────────┐
                                    ↓                   ↓
                               (passed)            (failed)
                                    ↓                   ↓
                                COMMIT              REVISE
                                                      ↓
                                              EXTRACT_FACTS
                                                      ↓
                                                RUN_CHECKS
                                                   (loop until passed or max_attempts)
```

### Database Schema

- **project** - Novel projects
- **style_bible** - Versioned style guides
- **character** - Characters with metadata (JSONB)
- **location** - Locations with metadata (JSONB)
- **scene** - Scenes with chapter/scene ordering
- **draft** - Immutable, append-only drafts
- **event** - Story timeline events
- **fact** - Extracted facts from drafts
- **constraint** - Rules for continuity/style checks
- **entity_link** - Graph edges between entities
- **iteration** - Pipeline iterations
- **check_run** - Results of checks
- **task** - Pipeline task queue

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.12 for local development

### 1. Start Services

```bash
cd /path/to/novelWriter
docker-compose up -d
```

This starts:
- Postgres 16 (with pgvector) on port 5432
- Redis on port 6379
- API server on port 8000
- RQ worker for background tasks

### 2. Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"novel-engine"}
```

## API Reference

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List projects |
| GET | `/projects/{id}` | Get project |
| DELETE | `/projects/{id}` | Delete project |

### Characters

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/characters` | Create character |
| GET | `/projects/{id}/characters` | List characters |
| GET | `/characters/{id}` | Get character |
| PUT | `/characters/{id}` | Update character |
| DELETE | `/characters/{id}` | Delete character |

### Scenes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{id}/scenes` | Create scene |
| GET | `/projects/{id}/scenes` | List scenes (ordered) |
| GET | `/scenes/{id}` | Get scene |
| PUT | `/scenes/{id}` | Update scene |
| DELETE | `/scenes/{id}` | Delete scene |

### Drafts (append-only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scenes/{id}/drafts` | Create draft |
| GET | `/scenes/{id}/drafts` | List drafts |
| GET | `/drafts/{id}` | Get draft |

### Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pipeline/scenes/{id}/run` | Start pipeline |
| GET | `/pipeline/iterations/{id}` | Get iteration status |

## Example Workflow

### 1. Create a Project

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Novel", "description": "A thrilling mystery"}'
```

Response:
```json
{"id": 1, "name": "My Novel", "description": "A thrilling mystery", "created_at": "...", "updated_at": "..."}
```

### 2. Create a Character

```bash
curl -X POST http://localhost:8000/projects/1/characters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detective Holmes",
    "data_jsonb": {
      "role": "protagonist",
      "traits": ["analytical", "observant"],
      "appearance": {"height": "tall", "hair": "dark"}
    }
  }'
```

### 3. Create a Scene

```bash
curl -X POST http://localhost:8000/projects/1/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "chapter_no": 1,
    "scene_no": 1,
    "pov_character_id": 1,
    "card_jsonb": {
      "title": "The Discovery",
      "summary": "Holmes discovers a crucial clue",
      "tone": "suspenseful"
    }
  }'
```

### 4. Run the Pipeline

```bash
curl -X POST http://localhost:8000/pipeline/scenes/1/run \
  -H "Content-Type: application/json" \
  -d '{"max_attempts": 3}'
```

Response:
```json
{"iteration_id": 1, "status": "running", "message": "Pipeline started for scene 1, iteration 1"}
```

### 5. Check Iteration Status

```bash
curl http://localhost:8000/pipeline/iterations/1
```

Response (after completion):
```json
{
  "id": 1,
  "scene_id": 1,
  "iteration_no": 1,
  "status": "passed",
  "check_runs": [...],
  "tasks": [...]
}
```

### 6. View the Generated Draft

```bash
curl http://localhost:8000/scenes/1/drafts
```

## Local Development

### Without Docker

1. Create a virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL=postgresql://novel:novel_secret@localhost:5432/novel_engine
export REDIS_URL=redis://localhost:6379/0
```

3. Run the API:
```bash
uvicorn app.main:app --reload
```

4. Run the worker (in a separate terminal):
```bash
python -m app.worker
```

## Design Decisions

### Draft Immutability
Drafts are append-only. Each revision creates a new version. This preserves history and enables rollback/comparison.

### Stub LLM Calls
All LLM calls (in `services/extraction.py`) are stubbed with deterministic outputs. Replace with actual LLM integrations (OpenAI, Anthropic, etc.) for production.

### Optional pgvector
The `fact.embedding` column is added via migration only if pgvector is available. The system works without embeddings.

### Entity Links
The `entity_link` table provides a universal graph structure with temporal validity (valid_from/to scene). This enables querying relationships that change over the story timeline.

## License

MIT
