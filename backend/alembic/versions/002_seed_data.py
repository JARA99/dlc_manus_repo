"""Seed initial data

Revision ID: 002_seed_data
Revises: 001_initial_schema
Create Date: 2025-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean, JSON, DateTime

# revision identifiers, used by Alembic.
revision = '002_seed_data'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert initial seed data."""
    
    # Define table structures for data insertion
    vendors_table = table('vendors',
        column('id', String),
        column('name', String),
        column('website', String),
        column('base_url', String),
        column('is_active', Boolean),
        column('status', String),
        column('supported_categories', JSON),
        column('delivery_areas', JSON),
        column('scraping_config', JSON)
    )
    
    categories_table = table('categories',
        column('id', String),
        column('name', String),
        column('name_en', String),
        column('parent_id', String),
        column('level', String),
        column('path', String),
        column('is_active', Boolean),
        column('slug', String),
        column('sort_order', String)
    )
    
    # Insert vendor data
    op.bulk_insert(vendors_table, [
        {
            'id': 'cemaco',
            'name': 'Cemaco',
            'website': 'https://cemaco.com',
            'base_url': 'https://cemaco.com',
            'is_active': True,
            'status': 'active',
            'supported_categories': ['electronics', 'home', 'appliances'],
            'delivery_areas': ['Guatemala City', 'Antigua', 'Quetzaltenango'],
            'scraping_config': {
                'search_url': 'https://cemaco.com/search',
                'product_selector': '.product-item',
                'name_selector': '.product-name',
                'price_selector': '.price',
                'delay': 2.0
            }
        },
        {
            'id': 'max',
            'name': 'Max',
            'website': 'https://max.com.gt',
            'base_url': 'https://max.com.gt',
            'is_active': True,
            'status': 'active',
            'supported_categories': ['electronics', 'computers', 'phones'],
            'delivery_areas': ['Guatemala City', 'Mixco', 'Villa Nueva'],
            'scraping_config': {
                'search_url': 'https://max.com.gt/buscar',
                'product_selector': '.product',
                'name_selector': 'h3',
                'price_selector': '.precio',
                'delay': 1.5
            }
        },
        {
            'id': 'elektra',
            'name': 'Elektra',
            'website': 'https://elektra.com.gt',
            'base_url': 'https://elektra.com.gt',
            'is_active': True,
            'status': 'active',
            'supported_categories': ['electronics', 'appliances', 'furniture'],
            'delivery_areas': ['Guatemala City', 'Escuintla', 'Chimaltenango'],
            'scraping_config': {
                'search_url': 'https://elektra.com.gt/search',
                'product_selector': '.item',
                'name_selector': '.item-title',
                'price_selector': '.price-current',
                'delay': 2.5
            }
        },
        {
            'id': 'walmart',
            'name': 'Walmart Guatemala',
            'website': 'https://walmart.com.gt',
            'base_url': 'https://walmart.com.gt',
            'is_active': True,
            'status': 'active',
            'supported_categories': ['electronics', 'home', 'grocery', 'clothing'],
            'delivery_areas': ['Guatemala City', 'Antigua', 'Mixco', 'Villa Nueva'],
            'scraping_config': {
                'search_url': 'https://walmart.com.gt/search',
                'product_selector': '[data-testid="product-tile"]',
                'name_selector': '[data-testid="product-title"]',
                'price_selector': '[data-testid="price-current"]',
                'delay': 1.0
            }
        },
        {
            'id': 'pricesmart',
            'name': 'PriceSmart',
            'website': 'https://pricesmart.com',
            'base_url': 'https://pricesmart.com',
            'is_active': True,
            'status': 'active',
            'supported_categories': ['electronics', 'home', 'grocery'],
            'delivery_areas': ['Guatemala City', 'Mixco'],
            'scraping_config': {
                'search_url': 'https://pricesmart.com/search',
                'product_selector': '.product-tile',
                'name_selector': '.product-name',
                'price_selector': '.price',
                'delay': 2.0
            }
        }
    ])
    
    # Insert category data
    op.bulk_insert(categories_table, [
        # Root categories
        {
            'id': 'electronics',
            'name': 'Electrónicos',
            'name_en': 'Electronics',
            'parent_id': None,
            'level': '0',
            'path': 'electronics',
            'is_active': True,
            'slug': 'electronicos',
            'sort_order': '1'
        },
        {
            'id': 'home',
            'name': 'Hogar',
            'name_en': 'Home',
            'parent_id': None,
            'level': '0',
            'path': 'home',
            'is_active': True,
            'slug': 'hogar',
            'sort_order': '2'
        },
        {
            'id': 'appliances',
            'name': 'Electrodomésticos',
            'name_en': 'Appliances',
            'parent_id': None,
            'level': '0',
            'path': 'appliances',
            'is_active': True,
            'slug': 'electrodomesticos',
            'sort_order': '3'
        },
        {
            'id': 'clothing',
            'name': 'Ropa',
            'name_en': 'Clothing',
            'parent_id': None,
            'level': '0',
            'path': 'clothing',
            'is_active': True,
            'slug': 'ropa',
            'sort_order': '4'
        },
        {
            'id': 'grocery',
            'name': 'Supermercado',
            'name_en': 'Grocery',
            'parent_id': None,
            'level': '0',
            'path': 'grocery',
            'is_active': True,
            'slug': 'supermercado',
            'sort_order': '5'
        },
        
        # Electronics subcategories
        {
            'id': 'phones',
            'name': 'Teléfonos',
            'name_en': 'Phones',
            'parent_id': 'electronics',
            'level': '1',
            'path': 'electronics/phones',
            'is_active': True,
            'slug': 'telefonos',
            'sort_order': '1'
        },
        {
            'id': 'computers',
            'name': 'Computadoras',
            'name_en': 'Computers',
            'parent_id': 'electronics',
            'level': '1',
            'path': 'electronics/computers',
            'is_active': True,
            'slug': 'computadoras',
            'sort_order': '2'
        },
        {
            'id': 'tablets',
            'name': 'Tablets',
            'name_en': 'Tablets',
            'parent_id': 'electronics',
            'level': '1',
            'path': 'electronics/tablets',
            'is_active': True,
            'slug': 'tablets',
            'sort_order': '3'
        },
        {
            'id': 'audio',
            'name': 'Audio',
            'name_en': 'Audio',
            'parent_id': 'electronics',
            'level': '1',
            'path': 'electronics/audio',
            'is_active': True,
            'slug': 'audio',
            'sort_order': '4'
        },
        {
            'id': 'tv',
            'name': 'Televisores',
            'name_en': 'TVs',
            'parent_id': 'electronics',
            'level': '1',
            'path': 'electronics/tv',
            'is_active': True,
            'slug': 'televisores',
            'sort_order': '5'
        },
        
        # Home subcategories
        {
            'id': 'furniture',
            'name': 'Muebles',
            'name_en': 'Furniture',
            'parent_id': 'home',
            'level': '1',
            'path': 'home/furniture',
            'is_active': True,
            'slug': 'muebles',
            'sort_order': '1'
        },
        {
            'id': 'decor',
            'name': 'Decoración',
            'name_en': 'Decor',
            'parent_id': 'home',
            'level': '1',
            'path': 'home/decor',
            'is_active': True,
            'slug': 'decoracion',
            'sort_order': '2'
        },
        {
            'id': 'kitchen',
            'name': 'Cocina',
            'name_en': 'Kitchen',
            'parent_id': 'home',
            'level': '1',
            'path': 'home/kitchen',
            'is_active': True,
            'slug': 'cocina',
            'sort_order': '3'
        },
        
        # Appliances subcategories
        {
            'id': 'refrigerators',
            'name': 'Refrigeradoras',
            'name_en': 'Refrigerators',
            'parent_id': 'appliances',
            'level': '1',
            'path': 'appliances/refrigerators',
            'is_active': True,
            'slug': 'refrigeradoras',
            'sort_order': '1'
        },
        {
            'id': 'washing_machines',
            'name': 'Lavadoras',
            'name_en': 'Washing Machines',
            'parent_id': 'appliances',
            'level': '1',
            'path': 'appliances/washing_machines',
            'is_active': True,
            'slug': 'lavadoras',
            'sort_order': '2'
        },
        {
            'id': 'microwaves',
            'name': 'Microondas',
            'name_en': 'Microwaves',
            'parent_id': 'appliances',
            'level': '1',
            'path': 'appliances/microwaves',
            'is_active': True,
            'slug': 'microondas',
            'sort_order': '3'
        }
    ])


def downgrade() -> None:
    """Remove seed data."""
    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM categories WHERE parent_id IS NOT NULL")
    op.execute("DELETE FROM categories WHERE parent_id IS NULL")
    op.execute("DELETE FROM vendors")

