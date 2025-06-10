"""
Migration script to add website column to buildings table.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.sql import text

def upgrade(engine):
    """Add website column to buildings table."""
    with engine.begin() as conn:
        # Add the new column
        conn.execute(text("""
            ALTER TABLE buildings 
            ADD COLUMN website VARCHAR;
        """))

def downgrade(engine):
    """Remove website column from buildings table."""
    with engine.begin() as conn:
        # Drop the column
        conn.execute(text("""
            ALTER TABLE buildings 
            DROP COLUMN IF EXISTS website;
        """)) 