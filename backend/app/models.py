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
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import Column, JSON

STORAGE_DIR = Path(os.getenv("STORAGE_PATH", "storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{STORAGE_DIR / 'app.db'}")
ECHO = os.getenv("ECHO_SQL", "0") == "1"

engine = create_engine(DATABASE_URL, echo=ECHO, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})


class Page(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: Optional[str] = Field(default=None, index=True, description="Upload file identifier")
    file_name: str
    page_no: int
    text: str
    image_paths: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True, unique=True)
    job_name: str
    course_id: Optional[str] = Field(default=None)
    mode: str = Field(default="auto-generate")
    payload_json: dict = Field(sa_column=Column(JSON))
    status: str = Field(default="created")  # created|running|completed|error
    total_expected: int = 0
    generated_count: int = 0
    found_count: int = 0
    not_found_count: int = 0


class QuestionResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
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


def create_db():  # idempotent
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def get_pages_for_file(file_name: str) -> list[Page]:  # utility for tests
    with get_session() as session:
        return list(session.exec(select(Page).where(Page.file_name == file_name)))

def get_pages_for_files(file_ids: list[str]) -> list[Page]:
    if not file_ids:
        return []
    with get_session() as session:
        return list(session.exec(select(Page).where(Page.file_id.in_(file_ids))))
