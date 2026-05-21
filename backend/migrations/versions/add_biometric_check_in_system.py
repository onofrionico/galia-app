"""Add biometric check-in system with GPS and photo fields

Revision ID: add_biometric_check_in_system
Revises: add_permissions_system
Create Date: 2026-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_biometric_check_in_system'
down_revision = 'add_permissions_system'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to work_blocks table for biometric check-in
    op.add_column('work_blocks', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('work_blocks', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('work_blocks', sa.Column('accuracy', sa.Float(), nullable=True))
    op.add_column('work_blocks', sa.Column('photo_url', sa.String(500), nullable=True))
    op.add_column('work_blocks', sa.Column('biometric_confidence', sa.Float(), nullable=True))
    op.add_column('work_blocks', sa.Column('biometric_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('work_blocks', sa.Column('entry_type', sa.String(50), nullable=False, server_default='legacy'))
    op.add_column('work_blocks', sa.Column('raw_metadata', postgresql.JSON(), nullable=True))

    # Create BiometricSession table
    op.create_table('biometric_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('qr_location_id', sa.String(100), nullable=True),
        sa.Column('qr_generated_at', sa.DateTime(), nullable=False),
        sa.Column('qr_scanned_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('work_block_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['work_block_id'], ['work_blocks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )

    # Create indices for BiometricSession
    op.create_index('ix_biometric_sessions_session_token', 'biometric_sessions', ['session_token'])
    op.create_index('ix_biometric_sessions_employee_id', 'biometric_sessions', ['employee_id'])
    op.create_index('ix_biometric_sessions_status', 'biometric_sessions', ['status'])
    op.create_index('ix_biometric_sessions_expires_at', 'biometric_sessions', ['expires_at'])

    # Create LocationBoundary table (optional geofencing)
    op.create_table('location_boundaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for LocationBoundary
    op.create_index('ix_location_boundaries_is_active', 'location_boundaries', ['is_active'])


def downgrade():
    # Drop LocationBoundary table
    op.drop_table('location_boundaries')

    # Drop BiometricSession table
    op.drop_index('ix_biometric_sessions_expires_at', table_name='biometric_sessions')
    op.drop_index('ix_biometric_sessions_status', table_name='biometric_sessions')
    op.drop_index('ix_biometric_sessions_employee_id', table_name='biometric_sessions')
    op.drop_index('ix_biometric_sessions_session_token', table_name='biometric_sessions')
    op.drop_table('biometric_sessions')

    # Drop columns from work_blocks
    op.drop_column('work_blocks', 'raw_metadata')
    op.drop_column('work_blocks', 'entry_type')
    op.drop_column('work_blocks', 'biometric_verified')
    op.drop_column('work_blocks', 'biometric_confidence')
    op.drop_column('work_blocks', 'photo_url')
    op.drop_column('work_blocks', 'accuracy')
    op.drop_column('work_blocks', 'longitude')
    op.drop_column('work_blocks', 'latitude')
