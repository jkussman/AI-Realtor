"""
Migration script to create the buildings table.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import text
from datetime import datetime

def upgrade(engine):
    """Create buildings table."""
    meta = MetaData()
    
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                address VARCHAR NOT NULL,
                latitude VARCHAR,
                longitude VARCHAR,
                building_type VARCHAR NOT NULL,
                bounding_box JSON,
                approved BOOLEAN DEFAULT FALSE,
                contact_email VARCHAR,
                contact_name VARCHAR,
                email_sent BOOLEAN DEFAULT FALSE,
                reply_received BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Contact confidence fields
                contact_email_confidence INTEGER DEFAULT 0,
                contact_source VARCHAR,
                contact_source_url VARCHAR,
                contact_verified BOOLEAN DEFAULT FALSE,
                contact_last_verified TIMESTAMP,
                verification_notes TEXT,
                verification_flags JSON,
                
                -- Basic building info
                property_manager VARCHAR,
                number_of_units INTEGER,
                year_built INTEGER,
                square_footage INTEGER,
                
                -- Detailed rental information
                is_coop BOOLEAN DEFAULT FALSE,
                is_mixed_use BOOLEAN DEFAULT FALSE,
                total_apartments INTEGER,
                two_bedroom_apartments INTEGER,
                recent_2br_rent INTEGER,
                rent_range_2br VARCHAR,
                has_laundry BOOLEAN DEFAULT FALSE,
                laundry_type VARCHAR,
                amenities JSON,
                pet_policy VARCHAR,
                building_style VARCHAR,
                management_company VARCHAR,
                contact_info VARCHAR,
                recent_availability BOOLEAN DEFAULT FALSE,
                rental_notes TEXT,
                neighborhood VARCHAR,
                stories INTEGER
            );
        """))
        print("✅ Buildings table created")

def downgrade(engine):
    """Drop buildings table."""
    meta = MetaData()
    
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS buildings;")) 