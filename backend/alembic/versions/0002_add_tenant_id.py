"""add tenant_id columns

Revision ID: 0002_add_tenant_id
Revises: 0001_baseline
Create Date: 2025-08-13
"""
from alembic import op  # type: ignore
import sqlalchemy as sa

revision = '0002_add_tenant_id'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None

def upgrade():
    tables = [
        'page','job','questionresult','answervariant','pageembedding','user'
    ]
    for tbl in tables:
        try:
            op.add_column(tbl, sa.Column('tenant_id', sa.String, nullable=True))
            op.create_index(f'ix_{tbl}_tenant_id', tbl, ['tenant_id'])
        except Exception:  # pragma: no cover
            pass

def downgrade():
    tables = [
        'page','job','questionresult','answervariant','pageembedding','user'
    ]
    for tbl in tables:
        try:
            op.drop_index(f'ix_{tbl}_tenant_id', table_name=tbl)
        except Exception:
            pass
        try:
            op.drop_column(tbl, 'tenant_id')
        except Exception:
            pass
