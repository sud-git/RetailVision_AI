"""Alembic migrations for database schema."""
# This file represents the migration strategy
# Run: alembic init alembic (to set up the migrations directory)
# Then create migrations with: alembic revision --autogenerate -m "description"
# Apply migrations with: alembic upgrade head

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create tables - migration UP."""
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(255), unique=True, nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), unique=True, nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('customer_tier', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('lifetime_visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lifetime_purchase_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('preferences', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('flag_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create tracking_sessions table
    op.create_table(
        'tracking_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('total_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('zones_visited', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_interactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_dwell_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('engagement_level', sa.String(50), nullable=False, server_default='low'),
        sa.Column('interaction_types', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('session_status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('has_anomalies', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('anomaly_flags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create shelf_interactions table
    op.create_table(
        'shelf_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('zone_id', sa.String(100), nullable=False),
        sa.Column('zone_name', sa.String(255), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('engagement_level', sa.String(50), nullable=True),
        sa.Column('is_prolonged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('items_examined', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('product_ids', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('product_names', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('data_quality', sa.String(50), nullable=False, server_default='high'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['tracking_session_id'], ['tracking_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create dwell_time_records table
    op.create_table(
        'dwell_time_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zone_id', sa.String(100), nullable=False),
        sa.Column('zone_name', sa.String(255), nullable=False),
        sa.Column('dwell_time_seconds', sa.Integer(), nullable=False),
        sa.Column('first_visit', sa.DateTime(), nullable=False),
        sa.Column('last_visit', sa.DateTime(), nullable=False),
        sa.Column('visit_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('engagement_intensity', sa.String(50), nullable=False),
        sa.Column('interaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revisit_frequency', sa.String(50), nullable=True),
        sa.Column('avg_interaction_per_visit', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['tracking_session_id'], ['tracking_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(100), nullable=False),
        sa.Column('alert_severity', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('alert_title', sa.String(255), nullable=False),
        sa.Column('alert_description', sa.String(1000), nullable=False),
        sa.Column('zone_id', sa.String(100), nullable=True),
        sa.Column('related_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('zone_id', sa.String(100), nullable=True),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('event_severity', sa.String(50), nullable=False, server_default='info'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processing_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('processing_results', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create analytics_snapshots table
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_period', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_customers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_interactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_dwell_time_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('zone_metrics', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('engagement_breakdown', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('customer_segments', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('anomaly_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('anomaly_types', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('peak_hour', sa.String(5), nullable=True),
        sa.Column('peak_hour_customer_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_quality_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('processing_duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_customers_external_id', 'customers', ['external_id'])
    op.create_index('idx_customers_email', 'customers', ['email'])
    op.create_index('idx_customers_is_flagged', 'customers', ['is_flagged'])
    
    op.create_index('idx_sessions_customer_id', 'tracking_sessions', ['customer_id'])
    op.create_index('idx_sessions_entry_time', 'tracking_sessions', ['entry_time'])
    op.create_index('idx_sessions_is_completed', 'tracking_sessions', ['is_completed'])
    
    op.create_index('idx_interactions_zone_id', 'shelf_interactions', ['zone_id'])
    op.create_index('idx_interactions_session_id', 'shelf_interactions', ['tracking_session_id'])
    op.create_index('idx_interactions_start_time', 'shelf_interactions', ['start_time'])
    
    op.create_index('idx_dwell_zone_id', 'dwell_time_records', ['zone_id'])
    op.create_index('idx_dwell_session_id', 'dwell_time_records', ['tracking_session_id'])
    
    op.create_index('idx_alerts_alert_type', 'alerts', ['alert_type'])
    op.create_index('idx_alerts_is_active', 'alerts', ['is_active'])
    op.create_index('idx_alerts_customer_id', 'alerts', ['customer_id'])
    
    op.create_index('idx_events_event_type', 'events', ['event_type'])
    op.create_index('idx_events_created_at', 'events', ['created_at'])
    op.create_index('idx_events_is_processed', 'events', ['is_processed'])
    
    op.create_index('idx_snapshots_period', 'analytics_snapshots', ['snapshot_period', 'period_end'])


def downgrade():
    """Drop tables - migration DOWN."""
    
    # Drop indexes
    op.drop_index('idx_snapshots_period')
    op.drop_index('idx_events_is_processed')
    op.drop_index('idx_events_created_at')
    op.drop_index('idx_events_event_type')
    op.drop_index('idx_alerts_customer_id')
    op.drop_index('idx_alerts_is_active')
    op.drop_index('idx_alerts_alert_type')
    op.drop_index('idx_dwell_session_id')
    op.drop_index('idx_dwell_zone_id')
    op.drop_index('idx_interactions_start_time')
    op.drop_index('idx_interactions_session_id')
    op.drop_index('idx_interactions_zone_id')
    op.drop_index('idx_sessions_is_completed')
    op.drop_index('idx_sessions_entry_time')
    op.drop_index('idx_sessions_customer_id')
    op.drop_index('idx_customers_is_flagged')
    op.drop_index('idx_customers_email')
    op.drop_index('idx_customers_external_id')
    
    # Drop tables
    op.drop_table('analytics_snapshots')
    op.drop_table('events')
    op.drop_table('alerts')
    op.drop_table('dwell_time_records')
    op.drop_table('shelf_interactions')
    op.drop_table('tracking_sessions')
    op.drop_table('customers')
