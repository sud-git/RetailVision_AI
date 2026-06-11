"""Phase 7 Analytics Models Migration

Revision ID: 008_analytics_models
Revises: 007_previous_phase
Create Date: 2024-01-15 10:00:00.000000

Migration to create all analytics tables for Phase 7:
- Heatmap: Stores spatial heatmap data with grid coordinates
- CustomerJourney: Tracks customer paths through store
- ZoneEngagement: Aggregated zone metrics
- RouteAnalytics: Common customer routes
- EngagementMetrics: Time-bucketed engagement data
- BusinessInsight: AI-generated insights
- AnalyticsSnapshot: Period summaries
- HeatmapHistory: Historical heatmap versions
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from datetime import datetime

# Revision identifiers
revision = '008_analytics_models'
down_revision = None  # Set to previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics tables"""
    
    # Heatmap table
    op.create_table(
        'heatmap',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('heatmap_type', sa.String(50), nullable=False),  # realtime, daily, weekly
        sa.Column('time_period_start', sa.DateTime, nullable=False),
        sa.Column('time_period_end', sa.DateTime, nullable=False),
        sa.Column('grid_data', postgresql.JSON, nullable=False),
        sa.Column('width', sa.Integer, nullable=False),
        sa.Column('height', sa.Integer, nullable=False),
        sa.Column('cell_size', sa.Integer, nullable=False),
        sa.Column('total_samples', sa.Integer, nullable=False),
        sa.Column('max_intensity', sa.Float, nullable=False),
        sa.Column('hotspot_count', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_heatmap_type_time', 'heatmap_type', 'time_period_start'),
    )
    
    # CustomerJourney table
    op.create_table(
        'customer_journey',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('path_points', postgresql.JSON, nullable=False),  # Array of zone transitions
        sa.Column('zones_visited', postgresql.ARRAY(sa.Integer), nullable=False),
        sa.Column('entry_zone', sa.Integer, nullable=True),
        sa.Column('exit_zone', sa.Integer, nullable=True),
        sa.Column('journey_type', sa.String(50), nullable=False),  # browsing, purchasing, exiting
        sa.Column('total_dwell_time', sa.Integer, nullable=False),
        sa.Column('avg_zone_dwell_time', sa.Float, nullable=False),
        sa.Column('zone_transitions', sa.Integer, nullable=False),
        sa.Column('engagement_score', sa.Float, nullable=False),
        sa.Column('conversion_flag', sa.Boolean, default=False),
        sa.Column('key_interactions', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_customer_journey_customer', 'customer_id'),
        sa.Index('idx_customer_journey_session', 'session_id'),
    )
    
    # ZoneEngagement table
    op.create_table(
        'zone_engagement',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('zone_id', sa.Integer, nullable=False),
        sa.Column('analytics_date', sa.Date, nullable=False),
        sa.Column('time_bucket', sa.String(50), nullable=False),  # hourly, daily, weekly
        sa.Column('visitor_count', sa.Integer, nullable=False),
        sa.Column('unique_visitor_count', sa.Integer, nullable=False),
        sa.Column('entry_count', sa.Integer, nullable=False),
        sa.Column('exit_count', sa.Integer, nullable=False),
        sa.Column('total_dwell_time', sa.Integer, nullable=False),
        sa.Column('avg_dwell_time', sa.Float, nullable=False),
        sa.Column('interaction_count', sa.Integer, nullable=False),
        sa.Column('pickup_count', sa.Integer, nullable=False),
        sa.Column('conversion_rate', sa.Float, nullable=False),
        sa.Column('engagement_score', sa.Float, nullable=False),
        sa.Column('zone_type', sa.String(50), nullable=False),  # high_value, engagement, checkout, etc.
        sa.Column('performance_rating', sa.String(50), nullable=False),  # excellent, good, average, poor
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_zone_engagement_date', 'analytics_date'),
        sa.Index('idx_zone_engagement_zone', 'zone_id'),
        sa.Index('idx_zone_engagement_zone_date', 'zone_id', 'analytics_date'),
    )
    
    # RouteAnalytics table
    op.create_table(
        'route_analytics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('zone_sequence', postgresql.ARRAY(sa.Integer), nullable=False),
        sa.Column('sequence_hash', sa.String(64), nullable=False),
        sa.Column('frequency', sa.Integer, nullable=False),
        sa.Column('avg_engagement', sa.Float, nullable=False),
        sa.Column('conversion_rate', sa.Float, nullable=False),
        sa.Column('avg_time', sa.Integer, nullable=False),
        sa.Column('first_seen', sa.DateTime, nullable=False),
        sa.Column('last_seen', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_route_analytics_hash', 'sequence_hash'),
        sa.Index('idx_route_analytics_frequency', 'frequency'),
    )
    
    # EngagementMetrics table
    op.create_table(
        'engagement_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('analytics_date', sa.Date, nullable=False),
        sa.Column('time_bucket', sa.String(50), nullable=False),  # hourly, daily, weekly
        sa.Column('total_customers', sa.Integer, nullable=False),
        sa.Column('avg_engagement_score', sa.Float, nullable=False),
        sa.Column('median_engagement_score', sa.Float, nullable=False),
        sa.Column('max_engagement_score', sa.Float, nullable=False),
        sa.Column('min_engagement_score', sa.Float, nullable=False),
        sa.Column('engagement_distribution', postgresql.JSON, nullable=False),  # Histogram
        sa.Column('conversion_rate', sa.Float, nullable=False),
        sa.Column('avg_session_length', sa.Integer, nullable=False),
        sa.Column('peak_hour', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_engagement_metrics_date', 'analytics_date'),
        sa.Index('idx_engagement_metrics_bucket', 'time_bucket'),
    )
    
    # BusinessInsight table
    op.create_table(
        'business_insight',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('analytics_date', sa.Date, nullable=False),
        sa.Column('insight_type', sa.String(100), nullable=False),  # zone_performance, trend, anomaly, recommendation
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('affected_zones', postgresql.ARRAY(sa.Integer), nullable=True),
        sa.Column('affected_products', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('key_metrics', postgresql.JSON, nullable=True),
        sa.Column('severity', sa.String(50), nullable=False),  # info, warning, critical
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('action_required', sa.Boolean, default=False),
        sa.Column('actioned_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_business_insight_date', 'analytics_date'),
        sa.Index('idx_business_insight_type', 'insight_type'),
        sa.Index('idx_business_insight_severity', 'severity'),
    )
    
    # AnalyticsSnapshot table
    op.create_table(
        'analytics_snapshot',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(50), nullable=False),  # daily, weekly, monthly
        sa.Column('total_customers', sa.Integer, nullable=False),
        sa.Column('avg_engagement', sa.Float, nullable=False),
        sa.Column('overall_conversion_rate', sa.Float, nullable=False),
        sa.Column('top_zones', postgresql.JSON, nullable=False),  # Array of zone IDs with scores
        sa.Column('bottom_zones', postgresql.JSON, nullable=False),
        sa.Column('key_insights', postgresql.JSON, nullable=False),  # Array of insights
        sa.Column('recommendations', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('snapshot_data', postgresql.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_analytics_snapshot_date', 'snapshot_date'),
        sa.Index('idx_analytics_snapshot_period', 'period_type'),
    )
    
    # HeatmapHistory table
    op.create_table(
        'heatmap_history',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('original_heatmap_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('heatmap_type', sa.String(50), nullable=False),
        sa.Column('time_period_start', sa.DateTime, nullable=False),
        sa.Column('time_period_end', sa.DateTime, nullable=False),
        sa.Column('grid_data', postgresql.JSON, nullable=False),
        sa.Column('width', sa.Integer, nullable=False),
        sa.Column('height', sa.Integer, nullable=False),
        sa.Column('cell_size', sa.Integer, nullable=False),
        sa.Column('max_intensity', sa.Float, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_heatmap_history_original', 'original_heatmap_id'),
        sa.Index('idx_heatmap_history_version', 'original_heatmap_id', 'version'),
    )
    
    print("✓ Created all 8 analytics tables successfully")


def downgrade():
    """Drop analytics tables"""
    
    # Drop in reverse order to avoid FK conflicts
    op.drop_table('heatmap_history')
    op.drop_table('analytics_snapshot')
    op.drop_table('business_insight')
    op.drop_table('engagement_metrics')
    op.drop_table('route_analytics')
    op.drop_table('zone_engagement')
    op.drop_table('customer_journey')
    op.drop_table('heatmap')
    
    print("✓ Dropped all analytics tables successfully")
