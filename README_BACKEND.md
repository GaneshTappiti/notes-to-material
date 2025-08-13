# Scollab Generator Backend (Initial Scaffold)

This is an initial scaffold created by AI assistant. Replace in-memory stores with Postgres, implement workers, and secure API keys.

## Endpoints

- POST /api/uploads
- POST /api/jobs
- GET /api/jobs/{id}/status
- GET /api/jobs/{id}/results
- PATCH /api/questions/{id}
- POST /api/exports

## Next Steps

- Integrate real DB models (SQLAlchemy or Piccolo, etc.)
- Add background task queue
- Implement embedding + retrieval with Chroma
- Implement Gemini generation
- Add PDF export via puppeteer / react-pdf

def list_jobs(session, tenant_id: str):
## Multi-Tenant Support

The data models now include an optional `tenant_id` column. For production multi-tenancy:

- Every authenticated request should include `X-Tenant: <tenant-id>` header.
- Persist `tenant_id` on new rows (e.g., when creating jobs, pages, question results).
- All read queries must filter by `tenant_id`.
- The helper dependency `tenant_id` (in `app/services/tenant.py`) extracts the header or falls back to the current user.
- Use the `enforce_tenant` decorator on service-layer functions that require scoping.

Environment:

- `SINGLE_TENANT=1` disables enforcement (local dev default).

Example (service):

```python
from sqlmodel import select
from app.services.tenant import enforce_tenant

@enforce_tenant
def list_jobs(session, tenant_id: str):
	return session.exec(select(Job).where(Job.tenant_id == tenant_id)).all()
```

## Database Migrations

Alembic is initialized under `backend/alembic`. Recent migration added tenant columns.

Run migrations locally:

```bash
cd backend
alembic upgrade head
```

Create new migration after model change:

```bash
alembic revision -m "describe change"
# edit generated script
alembic upgrade head
```

## CI & Quality Gates

GitHub Actions workflow runs backend tests with coverage plus frontend type check.
Planned additions: Ruff/flake8 lint and mypy/pyright type checking.
