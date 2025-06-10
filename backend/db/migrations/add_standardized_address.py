"""
Migration script to add standardized_address column to buildings table.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.sql import text

def upgrade(engine):
    """Add standardized_address column to buildings table."""
    with engine.begin() as conn:
        # Add the new column (without UNIQUE constraint first)
        conn.execute(text("""
            ALTER TABLE buildings 
            ADD COLUMN standardized_address VARCHAR;
        """))
        
        # Create index on standardized_address
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_buildings_standardized_address 
            ON buildings (standardized_address)
            WHERE standardized_address IS NOT NULL;
        """))

def downgrade(engine):
    """Remove standardized_address column from buildings table."""
    with engine.begin() as conn:
        # Drop the index first
        conn.execute(text("""
            DROP INDEX IF EXISTS ix_buildings_standardized_address;
        """))
        
        # Drop the column
        conn.execute(text("""
            ALTER TABLE buildings 
            DROP COLUMN IF EXISTS standardized_address;
        """)) 