"""Add advanced models for complete AI system

Revision ID: 002_advanced_models
Revises: 001_initial
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_advanced_models'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Create ai_generated_content table
    op.create_table(
        'ai_generated_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(length=255), nullable=True),
        sa.Column('trend_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('voiceover_text', sa.Text(), nullable=True),
        sa.Column('voiceover_url', sa.String(length=1000), nullable=True),
        sa.Column('video_url', sa.String(length=1000), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('subtitles', sa.JSON(), nullable=True),
        sa.Column('generation_method', sa.String(length=50), nullable=True),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True),
        sa.Column('generation_params', sa.JSON(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trend_id'], ['trends.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_generated_content_content_id'), 'ai_generated_content', ['content_id'], unique=True)

    # Create automation_workflows table
    op.create_table(
        'automation_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.String(length=255), nullable=True),
        sa.Column('workflow_type', sa.String(length=50), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['ai_generated_content.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_workflows_workflow_id'), 'automation_workflows', ['workflow_id'], unique=True)

    # Create content_calendar table
    op.create_table(
        'content_calendar',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.String(length=255), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('trend_id', sa.Integer(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('predicted_engagement', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('posted_content_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['ai_generated_content.id'], ),
        sa.ForeignKeyConstraint(['trend_id'], ['trends.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_calendar_calendar_id'), 'content_calendar', ['calendar_id'], unique=True)
    op.create_index(op.f('ix_content_calendar_scheduled_date'), 'content_calendar', ['scheduled_date'], unique=False)

    # Create trend_predictions table
    op.create_table(
        'trend_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_id', sa.String(length=255), nullable=True),
        sa.Column('topic', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('viral_score', sa.Float(), nullable=False),
        sa.Column('predicted_peak_date', sa.DateTime(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('predicted_engagement', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('prediction_features', sa.JSON(), nullable=True),
        sa.Column('actual_performance', sa.JSON(), nullable=True),
        sa.Column('prediction_accuracy', sa.Float(), nullable=True),
        sa.Column('predicted_at', sa.DateTime(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trend_predictions_prediction_id'), 'trend_predictions', ['prediction_id'], unique=True)

    # Create ab_test_results table
    op.create_table(
        'ab_test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.String(length=255), nullable=True),
        sa.Column('test_type', sa.String(length=50), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('variant_a', sa.JSON(), nullable=True),
        sa.Column('variant_b', sa.JSON(), nullable=True),
        sa.Column('variant_c', sa.JSON(), nullable=True),
        sa.Column('variant_a_metrics', sa.JSON(), nullable=True),
        sa.Column('variant_b_metrics', sa.JSON(), nullable=True),
        sa.Column('variant_c_metrics', sa.JSON(), nullable=True),
        sa.Column('winner', sa.String(length=10), nullable=True),
        sa.Column('improvement_percentage', sa.Float(), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('test_duration_days', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['ai_generated_content.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_results_test_id'), 'ab_test_results', ['test_id'], unique=True)

    # Create competitor_analysis table
    op.create_table(
        'competitor_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.String(length=255), nullable=True),
        sa.Column('competitor_name', sa.String(length=200), nullable=True),
        sa.Column('competitor_url', sa.String(length=1000), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('content_url', sa.String(length=1000), nullable=True),
        sa.Column('content_title', sa.String(length=500), nullable=True),
        sa.Column('content_category', sa.String(length=100), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('successful_elements', sa.JSON(), nullable=True),
        sa.Column('content_strategy', sa.JSON(), nullable=True),
        sa.Column('learnings', sa.Text(), nullable=True),
        sa.Column('ai_insights', sa.JSON(), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('content_published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_analysis_analysis_id'), 'competitor_analysis', ['analysis_id'], unique=True)

    # Create performance_metrics table
    op.create_table(
        'performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.String(length=255), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=True),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('saves', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('click_through_rate', sa.Float(), nullable=True),
        sa.Column('watch_time', sa.Float(), nullable=True),
        sa.Column('average_view_duration', sa.Float(), nullable=True),
        sa.Column('reach', sa.Integer(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=True),
        sa.Column('unique_viewers', sa.Integer(), nullable=True),
        sa.Column('revenue', sa.Float(), nullable=True),
        sa.Column('ad_revenue', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['ai_generated_content.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_metrics_metric_id'), 'performance_metrics', ['metric_id'], unique=True)
    op.create_index(op.f('ix_performance_metrics_recorded_at'), 'performance_metrics', ['recorded_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_performance_metrics_recorded_at'), table_name='performance_metrics')
    op.drop_index(op.f('ix_performance_metrics_metric_id'), table_name='performance_metrics')
    op.drop_table('performance_metrics')
    op.drop_index(op.f('ix_competitor_analysis_analysis_id'), table_name='competitor_analysis')
    op.drop_table('competitor_analysis')
    op.drop_index(op.f('ix_ab_test_results_test_id'), table_name='ab_test_results')
    op.drop_table('ab_test_results')
    op.drop_index(op.f('ix_trend_predictions_prediction_id'), table_name='trend_predictions')
    op.drop_table('trend_predictions')
    op.drop_index(op.f('ix_content_calendar_scheduled_date'), table_name='content_calendar')
    op.drop_index(op.f('ix_content_calendar_calendar_id'), table_name='content_calendar')
    op.drop_table('content_calendar')
    op.drop_index(op.f('ix_automation_workflows_workflow_id'), table_name='automation_workflows')
    op.drop_table('automation_workflows')
    op.drop_index(op.f('ix_ai_generated_content_content_id'), table_name='ai_generated_content')
    op.drop_table('ai_generated_content')

