"""
Migration script to add contact confidence columns to buildings table.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import text
from datetime import datetime

def column_exists(conn, table_name, column_name):
    """Check if a column exists in the table."""
    try:
        result = conn.execute(text(f"""
            SELECT COUNT(*) 
            FROM pragma_table_info('{table_name}') 
            WHERE name='{column_name}';
        """)).scalar()
        return result > 0
    except Exception as e:
        print(f"⚠️ Error checking column {column_name}: {e}")
        return False

def upgrade(engine):
    """Add contact confidence columns to buildings table if they don't exist."""
    try:
        with engine.begin() as conn:
            # Check if columns exist before adding them
            if not column_exists(conn, 'buildings', 'contact_email_confidence'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_email_confidence INTEGER DEFAULT 0;
                """))
                print("✅ Added contact_email_confidence column")
            
            if not column_exists(conn, 'buildings', 'contact_source'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_source VARCHAR;
                """))
                print("✅ Added contact_source column")
            
            if not column_exists(conn, 'buildings', 'contact_source_url'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_source_url VARCHAR;
                """))
                print("✅ Added contact_source_url column")
            
            if not column_exists(conn, 'buildings', 'contact_verified'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_verified BOOLEAN DEFAULT FALSE;
                """))
                print("✅ Added contact_verified column")
            
            if not column_exists(conn, 'buildings', 'contact_last_verified'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_last_verified TIMESTAMP;
                """))
                print("✅ Added contact_last_verified column")
            
            if not column_exists(conn, 'buildings', 'verification_notes'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN verification_notes TEXT;
                """))
                print("✅ Added verification_notes column")
            
            if not column_exists(conn, 'buildings', 'verification_flags'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN verification_flags JSON;
                """))
                print("✅ Added verification_flags column")
            
            print("✅ All contact confidence columns added or already exist")
            
    except Exception as e:
        print(f"❌ Error adding contact confidence columns: {e}")
        raise e

def downgrade(engine):
    """Remove contact confidence columns from buildings table."""
    try:
        with engine.begin() as conn:
            # First check if the buildings table exists
            table_exists = conn.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='buildings';
            """)).scalar()
            
            if not table_exists:
                print("⚠️ Buildings table does not exist, nothing to downgrade")
                return
            
            for column in [
                'contact_email_confidence',
                'contact_source',
                'contact_source_url',
                'contact_verified',
                'contact_last_verified',
                'verification_notes',
                'verification_flags'
            ]:
                if column_exists(conn, 'buildings', column):
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE buildings
                            DROP COLUMN {column};
                        """))
                        print(f"✅ Dropped column {column}")
                    except Exception as e:
                        print(f"❌ Error dropping column {column}: {e}")
                else:
                    print(f"ℹ️ Column {column} doesn't exist, skipping")
    except Exception as e:
        print(f"❌ Error in contact confidence downgrade: {e}")
        raise 