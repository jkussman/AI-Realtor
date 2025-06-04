"""
Migration script to add latitude and longitude columns to buildings table.
"""

import sqlite3
import os

def migrate_database():
    """Add latitude and longitude columns to buildings table."""
    
    # Get database path - database is in the backend directory
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai_realtor.db")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(buildings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add latitude column if it doesn't exist
        if 'latitude' not in columns:
            cursor.execute("ALTER TABLE buildings ADD COLUMN latitude TEXT")
            print("✅ Added latitude column")
        else:
            print("ℹ️ Latitude column already exists")
            
        # Add longitude column if it doesn't exist
        if 'longitude' not in columns:
            cursor.execute("ALTER TABLE buildings ADD COLUMN longitude TEXT")
            print("✅ Added longitude column")
        else:
            print("ℹ️ Longitude column already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Database migration completed successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database() 