"""
Script to run database migrations.
"""

import os
from sqlalchemy import create_engine, text

# Import migrations
from .migrations.create_buildings_table import upgrade as create_buildings
from .migrations.update_contact_info_to_json import upgrade as update_contact_info
from .migrations.add_website import upgrade as add_website

def check_database_exists(engine):
    """Check if the database file exists and has the buildings table."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='buildings';
            """)).scalar()
            return result > 0
    except Exception:
        return False

def run_migrations():
    """Run all database migrations in order."""
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///ai_realtor.db')
    engine = create_engine(database_url)
    
    # Run migrations in order
    create_buildings(engine)  # This now includes all necessary fields
    update_contact_info(engine)  # Update contact_info to JSON type
    add_website(engine)  # Add website column
    
    print("✅ All migrations completed successfully")

if __name__ == "__main__":
    run_migrations() 