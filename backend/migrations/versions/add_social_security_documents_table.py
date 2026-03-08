"""Add social_security_documents table

Revision ID: add_social_security_docs
Revises: add_absence_requests
Create Date: 2026-03-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_social_security_docs'
down_revision = 'add_absence_requests'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('social_security_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('period_month', sa.Integer(), nullable=False),
    sa.Column('period_year', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_social_security_documents_employee_id'), 'social_security_documents', ['employee_id'], unique=False)
    op.create_index('idx_social_security_period', 'social_security_documents', ['employee_id', 'period_year', 'period_month'], unique=False)
    op.create_index('idx_social_security_type', 'social_security_documents', ['document_type'], unique=False)


def downgrade():
    op.drop_index('idx_social_security_type', table_name='social_security_documents')
    op.drop_index('idx_social_security_period', table_name='social_security_documents')
    op.drop_index(op.f('ix_social_security_documents_employee_id'), table_name='social_security_documents')
    op.drop_table('social_security_documents')
