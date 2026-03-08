"""Add employee_documents table

Revision ID: add_employee_documents
Revises: add_social_security_docs
Create Date: 2026-03-08 10:11:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_employee_documents'
down_revision = 'add_social_security_docs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('employee_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.Column('period_month', sa.Integer(), nullable=True),
    sa.Column('period_year', sa.Integer(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employee_documents_employee_id'), 'employee_documents', ['employee_id'], unique=False)
    op.create_index(op.f('ix_employee_documents_document_type'), 'employee_documents', ['document_type'], unique=False)
    op.create_index('idx_employee_doc_type', 'employee_documents', ['employee_id', 'document_type'], unique=False)
    op.create_index('idx_employee_doc_period', 'employee_documents', ['employee_id', 'period_year', 'period_month'], unique=False)


def downgrade():
    op.drop_index('idx_employee_doc_period', table_name='employee_documents')
    op.drop_index('idx_employee_doc_type', table_name='employee_documents')
    op.drop_index(op.f('ix_employee_documents_document_type'), table_name='employee_documents')
    op.drop_index(op.f('ix_employee_documents_employee_id'), table_name='employee_documents')
    op.drop_table('employee_documents')
