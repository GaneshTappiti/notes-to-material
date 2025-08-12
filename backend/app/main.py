"""Minimal FastAPI application skeleton.

This pared‑down version only mounts the uploads router (see api/uploads.py) as
requested. Additional domain routers / business logic can be added later.

Run (locally):
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import uploads, jobs, results, questions, exports, generate, embeddings, retrieval
from .models import create_db

app = FastAPI(title="StudyForge Backend", version="0.0.1")

# Allow everything for quick local iteration – tighten later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount only the uploads router under /api
app.include_router(uploads.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(results.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(embeddings.router, prefix="/api")
app.include_router(retrieval.router, prefix="/api")

@app.on_event("startup")
def _startup():  # pragma: no cover - simple init
    create_db()


@app.get("/health")
async def health():
    return {"status": "ok"}
