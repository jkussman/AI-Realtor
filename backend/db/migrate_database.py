"""
Database migration script to add new rental information fields to the buildings table.
Run this before starting the server with the new building fields.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path to import database modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def migrate_database():
    """Add new rental information columns to the buildings table."""
    
    # Database URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./ai_realtor.db")
    engine = create_engine(database_url)
    
    # SQL commands to add new columns
    migration_commands = [
        # New detailed rental information fields
        "ALTER TABLE buildings ADD COLUMN is_coop BOOLEAN DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN is_mixed_use BOOLEAN DEFAULT 0", 
        "ALTER TABLE buildings ADD COLUMN total_apartments INTEGER",
        "ALTER TABLE buildings ADD COLUMN two_bedroom_apartments INTEGER",
        "ALTER TABLE buildings ADD COLUMN recent_2br_rent INTEGER",
        "ALTER TABLE buildings ADD COLUMN rent_range_2br TEXT",
        "ALTER TABLE buildings ADD COLUMN has_laundry BOOLEAN DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN laundry_type TEXT",
        "ALTER TABLE buildings ADD COLUMN amenities JSON",
        "ALTER TABLE buildings ADD COLUMN pet_policy TEXT",
        "ALTER TABLE buildings ADD COLUMN building_style TEXT",
        "ALTER TABLE buildings ADD COLUMN management_company TEXT",
        "ALTER TABLE buildings ADD COLUMN contact_info TEXT",
        "ALTER TABLE buildings ADD COLUMN recent_availability BOOLEAN DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN rental_notes TEXT",
        "ALTER TABLE buildings ADD COLUMN neighborhood TEXT",
        "ALTER TABLE buildings ADD COLUMN stories INTEGER"
    ]
    
    print("🔄 Starting database migration...")
    
    with engine.connect() as conn:
        for i, command in enumerate(migration_commands, 1):
            try:
                conn.execute(text(command))
                print(f"✅ Migration {i}/{len(migration_commands)}: Added column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️ Migration {i}/{len(migration_commands)}: Column already exists, skipping")
                else:
                    print(f"❌ Migration {i}/{len(migration_commands)}: Error - {e}")
        
        # Commit the changes
        conn.commit()
    
    print("✅ Database migration completed!")
    print("🎉 New rental information fields have been added to the buildings table.")
    print("\nNew fields include:")
    print("  • Co-op and mixed-use classification")
    print("  • Total apartments and 2-bedroom counts") 
    print("  • Recent rent prices and rent ranges")
    print("  • Laundry facilities and amenities")
    print("  • Pet policy and building style")
    print("  • Management company and contact info")
    print("  • Availability status and rental notes")
    print("  • Neighborhood and story count")

if __name__ == "__main__":
    migrate_database() 