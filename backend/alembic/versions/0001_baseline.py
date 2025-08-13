"""baseline schema

Revision ID: 0001_baseline
Revises:
Create Date: 2025-08-13
"""
from alembic import op  # type: ignore[import-untyped]
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Core tables equivalent to current SQLModel definitions (simplified)
    op.create_table('page',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('file_id', sa.String, index=True),
        sa.Column('file_name', sa.String, nullable=False),
        sa.Column('page_no', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('image_paths', sa.JSON, nullable=True),
    )
    op.create_table('job',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.String, nullable=False, unique=True, index=True),
        sa.Column('job_name', sa.String, nullable=False),
        sa.Column('course_id', sa.String),
        sa.Column('mode', sa.String, nullable=False, server_default='auto-generate'),
        sa.Column('payload_json', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('status', sa.String, nullable=False, server_default='created'),
        sa.Column('total_expected', sa.Integer, nullable=False, server_default='0'),
        sa.Column('generated_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('found_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('not_found_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.String, nullable=False),
    )
    op.create_table('questionresult',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.String, index=True),
        sa.Column('question_id', sa.String, nullable=False),
        sa.Column('mark_value', sa.Integer, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('answer_format', sa.String, nullable=False),
        sa.Column('page_references', sa.JSON),
        sa.Column('verbatim_quotes', sa.JSON),
        sa.Column('diagram_images', sa.JSON),
        sa.Column('status', sa.String, nullable=False, server_default='FOUND'),
        sa.Column('retrieval_scores', sa.JSON),
        sa.Column('raw_model_output', sa.JSON),
        sa.Column('approved_at', sa.String),
        sa.Column('approver_id', sa.Integer),
    )
    op.create_table('pageembedding',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('page_id', sa.Integer, index=True),
        sa.Column('file_id', sa.String, index=True),
        sa.Column('page_no', sa.Integer, nullable=False),
        sa.Column('embedding', sa.JSON, nullable=False),
        sa.Column('created_at', sa.String, nullable=False),
    )
    op.create_table('user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('role', sa.String, nullable=False, server_default='student'),
        sa.Column('created_at', sa.String, nullable=False),
    )


def downgrade():
    op.drop_table('user')
    op.drop_table('pageembedding')
    op.drop_table('questionresult')
    op.drop_table('job')
    op.drop_table('page')
