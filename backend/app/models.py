"""Database models and session setup.

Provides a lightweight abstraction using SQLModel so tests can run against
SQLite by default while production can point to Postgres via DATABASE_URL.

Environment:
  DATABASE_URL (default: sqlite:///./storage/app.db)
  ECHO_SQL (optional) set to '1' to echo statements

The only persisted model needed for current feature work is Page.
"""
from __future__ import annotations

import os
from typing import Optional, List
from pathlib import Path
from sqlmodel import SQLModel, Field, create_engine, Session, select  # type: ignore[import-untyped]
from sqlalchemy import Column, JSON

STORAGE_DIR = Path(os.getenv("STORAGE_PATH", "storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{STORAGE_DIR / 'app.db'}")
ECHO = os.getenv("ECHO_SQL", "0") == "1"

def create_engine_from_env(url: str | None = None):
    """Create a SQLModel/SQLAlchemy engine from env (Prompt 1 requirement).

    Fallback: sqlite:///./storage/app.db (relative safe path) with check_same_thread disabled.
    Passing a url overrides env resolution (useful for tests).
    """
    resolved = url or os.getenv("DATABASE_URL", f"sqlite:///{STORAGE_DIR / 'app.db'}")
    connect_args = {"check_same_thread": False} if resolved.startswith("sqlite") else {}
    return create_engine(resolved, echo=ECHO, connect_args=connect_args)

engine = create_engine_from_env(DATABASE_URL)


class Page(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True, description="Multi-tenant isolation key")
    file_id: Optional[str] = Field(default=None, index=True, description="Upload file identifier")
    file_name: str
    page_no: int
    text: str
    image_paths: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class Upload(SQLModel, table=True):  # type: ignore[misc]
    """Represents a logical uploaded study material file.

    Added after audit to have a first-class record for uploads (instead of
    deriving only from Page rows + JSON metadata on disk). This makes it easy
    to list uploads, show their page counts, and attach future processing
    status fields (embedding progress, etc.).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: str = Field(index=True, unique=True)
    file_name: str = Field(index=True)
    page_count: int = 0
    tenant_id: Optional[str] = Field(default=None, index=True)
    ocr_status: str = Field(default="done")  # future: pending|processing|done|error
    created_at: str = Field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat(), index=True)


class Job(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    job_id: str = Field(index=True, unique=True)
    job_name: str
    course_id: Optional[str] = Field(default=None)
    mode: str = Field(default="auto-generate")
    payload_json: dict = Field(sa_column=Column(JSON))
    file_ids: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="created")  # created|running|completed|error
    total_expected: int = 0
    generated_count: int = 0
    found_count: int = 0
    not_found_count: int = 0
    created_at: str = Field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat(), index=True)


class QuestionResult(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    job_id: str = Field(index=True)
    question_id: str
    mark_value: int
    question_text: str
    answer: str
    answer_format: str
    page_references: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    verbatim_quotes: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    diagram_images: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="FOUND")  # FOUND|NOT_FOUND
    retrieval_scores: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    raw_model_output: dict = Field(default_factory=dict, sa_column=Column(JSON))
    approved_at: Optional[str] = Field(default=None, description="UTC ISO timestamp when faculty approved")
    approver_id: Optional[int] = Field(default=None, foreign_key="user.id")


class AnswerVariant(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    question_id: str = Field(index=True)
    job_id: str = Field(index=True)
    mark_value: int
    answer_text: str
    created_at: str = Field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())


class PageEmbedding(SQLModel, table=True):  # type: ignore[misc]
    """Optional persisted embeddings per page.

    Vector stored as list[float] JSON for portability (SQLite/Postgres).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    page_id: int = Field(foreign_key="page.id", index=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    file_id: Optional[str] = Field(default=None, index=True)
    page_no: int
    embedding: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat())


class User(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="student", description="student|faculty|admin")
    created_at: str = Field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat())


class Export(SQLModel, table=True):  # type: ignore[misc]
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)
    template: str = Field(default="compact")
    status: str = Field(default="pending")  # pending|ready|error
    file_path: Optional[str] = Field(default=None)
    approved_only: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat(), index=True)



def create_db():  # idempotent (with lightweight missing-column recovery in tests)
    from sqlalchemy import inspect
    insp = inspect(engine)
    test_mode = os.getenv('TEST_MODE','0') == '1' or 'PYTEST_CURRENT_TEST' in os.environ
    # Detect missing columns for existing tables (simple schema drift handler for tests)
    if test_mode:
        rebuilt = False
        for table_name, table in SQLModel.metadata.tables.items():
            if table_name not in insp.get_table_names():
                continue
            existing_cols = {c['name'] for c in insp.get_columns(table_name)}
            expected_cols = {c.name for c in table.columns}
            missing = expected_cols - existing_cols
            if missing:
                # Drop only the affected table to preserve unrelated data
                try:
                    table.drop(engine)  # type: ignore[arg-type]
                    rebuilt = True
                except Exception:
                    # fallback: drop all if individual drop fails
                    SQLModel.metadata.drop_all(engine)
                    rebuilt = True
                    break
        if rebuilt:
            SQLModel.metadata.create_all(engine)
            return
    # Normal path
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def get_pages_for_file(file_name: str) -> list[Page]:  # utility for tests
    with get_session() as session:
        return list(session.exec(select(Page).where(Page.file_name == file_name)))

def get_pages_for_files(file_ids: list[str]) -> list[Page]:
    if not file_ids:
        return []
    from sqlalchemy import or_  # noqa: F401
    with get_session() as session:
        stmt = select(Page).where(Page.file_id.in_(file_ids))  # type: ignore[arg-type]
        return list(session.exec(stmt))


# Convenience helpers for jobs / questions persistence (avoid circular imports)
def create_job_row(job_id: str, job_name: str, mode: str, payload: dict, status: str = "created", course_id: str | None = None, total_expected: int = 0) -> Job:
    with get_session() as s:
        row = Job(job_id=job_id, job_name=job_name, course_id=course_id, mode=mode, payload_json=payload, status=status, total_expected=total_expected)
        s.add(row)
        s.commit()
        s.refresh(row)
        return row

def add_question_results(job_id: str, items: list[dict]):
    if not items:
        return 0
    with get_session() as s:
        count = 0
        for it in items:
            qr = QuestionResult(
                job_id=job_id,
                question_id=it.get('id') or it.get('question_id') or __import__('uuid').uuid4().hex[:8],
                mark_value=int(it.get('mark_value') or it.get('mark') or 0),
                question_text=it.get('question') or it.get('question_text') or '',
                answer=(it.get('answers') or {}).get('2') or it.get('answer') or '',
                answer_format=it.get('answer_format') or 'text',
                page_references=it.get('page_references') or [],
                verbatim_quotes=it.get('verbatim_quotes') or [],
                diagram_images=it.get('diagram_images') or [],
                status=it.get('status') or 'FOUND',
                retrieval_scores=it.get('retrieval_scores') or [],
                raw_model_output=it,
            )
            s.add(qr)
            count += 1
        s.commit()
        return count

# Explicit re-exports required by Prompt 1
__all__ = [
    'Page','Upload','Job','QuestionResult','AnswerVariant','PageEmbedding','User','Export',
    'create_engine_from_env','create_db','get_session','get_pages_for_file','get_pages_for_files',
    'create_job_row','add_question_results','engine'
]
