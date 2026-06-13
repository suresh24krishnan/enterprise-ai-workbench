# backend/

FastAPI application — the governed REST API for the Enterprise AI Workbench.

## What Is Running in Step 2

- `GET /health` — liveness check
- `GET /api/session` — returns a mock authenticated session
- `GET /api/claims` — list of mock claims
- `GET /api/claims/{claim_id}` — full claim detail
- `GET /api/claims/{claim_id}/summary` — AI-generated claim summary (mock)
- `GET /api/claims/{claim_id}/evidence` — evidence sources used in the summary
- `GET /api/claims/{claim_id}/audit` — audit trail for the claim session

All responses use the Pydantic contracts from `shared/contracts/python/`.

## Prerequisites

- Python 3.11+

## Setup

Run all commands from the **project root** (`enterprise-ai-workbench/`):

```bash
# 1. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Copy environment file (only needed once)
cp .env.example .env
```

## Run

From the **project root**:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Architecture

```
routes_*.py  (HTTP boundary — validates input, calls service)
    │
    ▼
claim_service.py  (business orchestration — no HTTP, no I/O)
    │
    ▼
IClaimRepository  (interface — service depends on this only)
    │
    ▼
MockClaimRepository  (implementation — swapped in Phase 2)
```

## Project Root Requirement

`uvicorn backend.main:app` must be run from the project root so that
`shared/contracts/python` is importable as `shared.contracts.python`.
This mirrors how the Docker container works (both backend/ and shared/ are mounted under /app).
