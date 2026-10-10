"""Sincroniza el esquema con los modelos (drift de scripts ad-hoc)

Crea las tablas y columnas que hasta ahora solo existían vía scripts ad-hoc
(create_ml_tables.py, create_notifications_tables.py, create_new_tables.py,
add_extraordinary_fields.py, add_vacation_fields.py). Es idempotente: en
producción, donde esos scripts ya corrieron, no hace nada.

Revision ID: sync_schema_drift
Revises: carta_grupos_fudo
Create Date: 2026-10-09

"""
from alembic import op
import sqlalchemy as sa


revision = 'sync_schema_drift'
down_revision = 'carta_grupos_fudo'
branch_labels = None
depends_on = None


def _existing_tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def _existing_columns(table):
    return {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    tables = _existing_tables()

    if 'holidays' not in tables:
        op.create_table(
            'holidays',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('date', sa.Date(), nullable=False, unique=True),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('type', sa.String(50)),
            sa.Column('impact_multiplier', sa.Float()),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime()),
        )

    if 'ml_model_versions' not in tables:
        op.create_table(
            'ml_model_versions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('version', sa.String(50), nullable=False),
            sa.Column('trained_at', sa.DateTime(), nullable=False),
            sa.Column('training_records', sa.Integer(), nullable=False),
            sa.Column('train_score', sa.Float()),
            sa.Column('test_score', sa.Float()),
            sa.Column('features_used', sa.JSON()),
            sa.Column('hyperparameters', sa.JSON()),
            sa.Column('is_active', sa.Boolean()),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime()),
        )

    if 'ml_prediction_accuracy' not in tables:
        op.create_table(
            'ml_prediction_accuracy',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('hour', sa.Integer(), nullable=False),
            sa.Column('predicted_sales_count', sa.Integer()),
            sa.Column('predicted_sales_amount', sa.Numeric(10, 2)),
            sa.Column('recommended_staff_count', sa.Integer()),
            sa.Column('actual_sales_count', sa.Integer()),
            sa.Column('actual_sales_amount', sa.Numeric(10, 2)),
            sa.Column('actual_staff_count', sa.Integer()),
            sa.Column('sales_count_error', sa.Float()),
            sa.Column('sales_amount_error', sa.Float()),
            sa.Column('staff_count_error', sa.Float()),
            sa.Column('model_version', sa.String(50)),
            sa.Column('created_at', sa.DateTime()),
            sa.UniqueConstraint('date', 'hour', name='unique_date_hour_accuracy'),
        )

    if 'staffing_metrics' not in tables:
        op.create_table(
            'staffing_metrics',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('hour', sa.Integer(), nullable=False),
            sa.Column('day_of_week', sa.Integer(), nullable=False),
            sa.Column('employees_scheduled', sa.Integer(), nullable=False),
            sa.Column('employees_present', sa.Integer()),
            sa.Column('sales_count', sa.Integer()),
            sa.Column('sales_amount', sa.Numeric(10, 2)),
            sa.Column('is_holiday', sa.Boolean()),
            sa.Column('weather_condition', sa.String(50)),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime()),
        )
        op.create_index('ix_staffing_metrics_date', 'staffing_metrics', ['date'])
        op.create_index('idx_staffing_date_hour', 'staffing_metrics', ['date', 'hour'])
        op.create_index('idx_staffing_day_hour', 'staffing_metrics', ['day_of_week', 'hour'])

    if 'staffing_predictions' not in tables:
        op.create_table(
            'staffing_predictions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('hour', sa.Integer(), nullable=False),
            sa.Column('predicted_sales_count', sa.Integer(), nullable=False),
            sa.Column('predicted_sales_amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('recommended_staff_count', sa.Integer(), nullable=False),
            sa.Column('confidence_score', sa.Float()),
            sa.Column('model_version', sa.String(50)),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_staffing_predictions_date', 'staffing_predictions', ['date'])
        op.create_index('idx_prediction_date_hour', 'staffing_predictions', ['date', 'hour'])

    if 'prediction_alerts' not in tables:
        op.create_table(
            'prediction_alerts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('schedule_id', sa.Integer(), sa.ForeignKey('schedules.id')),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('hour', sa.Integer(), nullable=False),
            sa.Column('recommended_staff', sa.Integer(), nullable=False),
            sa.Column('scheduled_staff', sa.Integer(), nullable=False),
            sa.Column('difference', sa.Integer(), nullable=False),
            sa.Column('difference_percentage', sa.Float(), nullable=False),
            sa.Column('severity', sa.String(20)),
            sa.Column('status', sa.String(20)),
            sa.Column('acknowledged_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('acknowledged_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime()),
        )

    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('type', sa.String(50), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=False),
            sa.Column('related_schedule_id', sa.Integer(), sa.ForeignKey('schedules.id')),
            sa.Column('related_shift_id', sa.Integer(), sa.ForeignKey('shifts.id')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    if 'schedule_change_logs' not in tables:
        op.create_table(
            'schedule_change_logs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('schedule_id', sa.Integer(), sa.ForeignKey('schedules.id'), nullable=False),
            sa.Column('shift_id', sa.Integer(), sa.ForeignKey('shifts.id')),
            sa.Column('change_type', sa.String(50), nullable=False),
            sa.Column('changed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('affected_employee_id', sa.Integer(), sa.ForeignKey('employees.id')),
            sa.Column('old_data', sa.JSON()),
            sa.Column('new_data', sa.JSON()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    payroll_columns = _existing_columns('payrolls')
    if 'extraordinary_amount' not in payroll_columns:
        op.add_column('payrolls', sa.Column('extraordinary_amount', sa.Numeric(10, 2), server_default='0'))
    if 'extraordinary_description' not in payroll_columns:
        op.add_column('payrolls', sa.Column('extraordinary_description', sa.Text()))


def downgrade():
    # Ojo: en una base donde estos objetos venían de los scripts ad-hoc,
    # el downgrade también los elimina (con sus datos).
    payroll_columns = _existing_columns('payrolls')
    for column in ('extraordinary_description', 'extraordinary_amount'):
        if column in payroll_columns:
            op.drop_column('payrolls', column)

    tables = _existing_tables()
    for table in (
        'schedule_change_logs',
        'notifications',
        'prediction_alerts',
        'staffing_predictions',
        'staffing_metrics',
        'ml_prediction_accuracy',
        'ml_model_versions',
        'holidays',
    ):
        if table in tables:
            op.drop_table(table)
