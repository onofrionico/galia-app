"""add_email_invoice_tables

Revision ID: b6552f084698
Revises: fa83c4360922
Create Date: 2026-03-26 17:11:13.970699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6552f084698'
down_revision = 'fa83c4360922'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_configurations table
    op.create_table('email_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_address', sa.String(length=255), nullable=False),
        sa.Column('imap_server', sa.String(length=255), nullable=False),
        sa.Column('imap_port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('encrypted_password', sa.Text(), nullable=False),
        sa.Column('use_ssl', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create email_invoices table
    op.create_table('email_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('received_date', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_id')
    )
    
    # Create invoice_attachments table
    op.create_table('invoice_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_invoice_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['email_invoice_id'], ['email_invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add new columns to expenses table
    op.add_column('expenses', sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'))
    op.add_column('expenses', sa.Column('invoice_attachment_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_expenses_invoice_attachment', 'expenses', 'invoice_attachments', ['invoice_attachment_id'], ['id'])
    
    # Add index for source column
    op.create_index('idx_expenses_source', 'expenses', ['source'])


def downgrade():
    # Drop index
    op.drop_index('idx_expenses_source', table_name='expenses')
    
    # Drop foreign key and columns from expenses
    op.drop_constraint('fk_expenses_invoice_attachment', 'expenses', type_='foreignkey')
    op.drop_column('expenses', 'invoice_attachment_id')
    op.drop_column('expenses', 'source')
    
    # Drop tables
    op.drop_table('invoice_attachments')
    op.drop_table('email_invoices')
    op.drop_table('email_configurations')
