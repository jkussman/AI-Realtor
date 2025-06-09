"""
Script to run database migrations.
"""

import os
from sqlalchemy import create_engine, text
from migrations.create_buildings_table import upgrade as create_buildings
from migrations.add_contact_confidence import upgrade as add_contact_confidence

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
    """Run all pending database migrations."""
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./ai_realtor.db')
    
    # Create engine
    engine = create_engine(database_url)
    
    print("Running migrations...")
    
    try:
        # Check if database exists
        database_exists = check_database_exists(engine)
        
        if not database_exists:
            # Create buildings table with all fields
            print("Creating buildings table...")
            create_buildings(engine)
            print("✅ Buildings table created")
        else:
            print("ℹ️ Buildings table already exists")
        
        # Add contact confidence columns if needed
        print("\nAdding contact confidence columns...")
        add_contact_confidence(engine)
        
    except Exception as e:
        print(f"❌ Error running migrations: {str(e)}")
        raise e
    
    print("\n✅ All migrations complete")

if __name__ == "__main__":
    run_migrations() 