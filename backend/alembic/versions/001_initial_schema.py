"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create vendors table
    op.create_table('vendors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('website', sa.String(), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('base_url', sa.String(), nullable=False),
        sa.Column('search_url_template', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('scraping_config', sa.JSON(), nullable=True),
        sa.Column('delivery_areas', sa.JSON(), nullable=True),
        sa.Column('default_delivery_cost', sa.String(), nullable=True),
        sa.Column('supported_categories', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('name_en', sa.String(), nullable=True),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('level', sa.String(), nullable=True),
        sa.Column('path', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('slug', sa.String(), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)
    
    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('sku', sa.String(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('original_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('vendor_product_id', sa.String(), nullable=True),
        sa.Column('vendor_url', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('image_urls', sa.JSON(), nullable=True),
        sa.Column('availability', sa.String(), nullable=True),
        sa.Column('stock_quantity', sa.String(), nullable=True),
        sa.Column('delivery_cost', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('delivery_time', sa.String(), nullable=True),
        sa.Column('delivery_areas', sa.JSON(), nullable=True),
        sa.Column('specifications', sa.JSON(), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('search_keywords', sa.Text(), nullable=True),
        sa.Column('normalized_name', sa.String(), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_price_change_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_product_active_updated', 'products', ['is_active', 'last_updated_at'], unique=False)
    op.create_index('idx_product_brand_model', 'products', ['brand', 'model'], unique=False)
    op.create_index('idx_product_category_price', 'products', ['category_id', 'price'], unique=False)
    op.create_index('idx_product_search', 'products', ['normalized_name', 'brand'], unique=False)
    op.create_index('idx_product_vendor_price', 'products', ['vendor_id', 'price'], unique=False)
    op.create_index(op.f('ix_products_brand'), 'products', ['brand'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_normalized_name'), 'products', ['normalized_name'], unique=False)
    op.create_index(op.f('ix_products_price'), 'products', ['price'], unique=False)
    op.create_index(op.f('ix_products_vendor_id'), 'products', ['vendor_id'], unique=False)
    
    # Create searches table
    op.create_table('searches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('normalized_query', sa.String(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration', sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column('total_results', sa.String(), nullable=True),
        sa.Column('vendors_searched', sa.JSON(), nullable=True),
        sa.Column('vendors_successful', sa.JSON(), nullable=True),
        sa.Column('vendors_failed', sa.JSON(), nullable=True),
        sa.Column('lowest_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('highest_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('average_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_range', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('client_ip', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_searches_client_ip'), 'searches', ['client_ip'], unique=False)
    op.create_index(op.f('ix_searches_id'), 'searches', ['id'], unique=False)
    op.create_index(op.f('ix_searches_normalized_query'), 'searches', ['normalized_query'], unique=False)
    op.create_index(op.f('ix_searches_query'), 'searches', ['query'], unique=False)
    op.create_index(op.f('ix_searches_status'), 'searches', ['status'], unique=False)
    op.create_index(op.f('ix_searches_user_id'), 'searches', ['user_id'], unique=False)
    
    # Create product_price_history table
    op.create_table('product_price_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('original_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('availability', sa.String(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_price_history_product_date', 'product_price_history', ['product_id', 'recorded_at'], unique=False)
    op.create_index(op.f('ix_product_price_history_product_id'), 'product_price_history', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_price_history_recorded_at'), 'product_price_history', ['recorded_at'], unique=False)
    
    # Create search_results table
    op.create_table('search_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('search_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rank', sa.String(), nullable=True),
        sa.Column('relevance_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('found_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('vendor_id', sa.String(), nullable=False),
        sa.Column('price_at_search', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('availability_at_search', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['search_id'], ['searches.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_results_product', 'search_results', ['product_id'], unique=False)
    op.create_index('idx_search_results_search_rank', 'search_results', ['search_id', 'rank'], unique=False)
    op.create_index('idx_search_results_vendor', 'search_results', ['vendor_id'], unique=False)
    
    # Create search_analytics table
    op.create_table('search_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hour', sa.String(), nullable=True),
        sa.Column('total_searches', sa.String(), nullable=True),
        sa.Column('successful_searches', sa.String(), nullable=True),
        sa.Column('failed_searches', sa.String(), nullable=True),
        sa.Column('average_duration', sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column('top_queries', sa.JSON(), nullable=True),
        sa.Column('top_categories', sa.JSON(), nullable=True),
        sa.Column('vendor_stats', sa.JSON(), nullable=True),
        sa.Column('average_results_per_search', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('total_products_found', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_date', 'search_analytics', ['date'], unique=False)
    op.create_index('idx_analytics_date_hour', 'search_analytics', ['date', 'hour'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('search_analytics')
    op.drop_table('search_results')
    op.drop_table('product_price_history')
    op.drop_table('searches')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('vendors')

