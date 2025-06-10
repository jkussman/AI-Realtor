"""
Migration script to add contact_phone column to buildings table.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.sql import text

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
    """Add contact_phone column to buildings table if it doesn't exist."""
    try:
        with engine.begin() as conn:
            # Check if column exists before adding it
            if not column_exists(conn, 'buildings', 'contact_phone'):
                conn.execute(text("""
                    ALTER TABLE buildings
                    ADD COLUMN contact_phone VARCHAR;
                """))
                print("✅ Added contact_phone column")
            else:
                print("ℹ️ contact_phone column already exists")
            
    except Exception as e:
        print(f"❌ Error adding contact_phone column: {e}")
        raise e

def downgrade(engine):
    """Remove contact_phone column from buildings table."""
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
            
            if column_exists(conn, 'buildings', 'contact_phone'):
                try:
                    conn.execute(text("""
                        ALTER TABLE buildings
                        DROP COLUMN contact_phone;
                    """))
                    print("✅ Dropped contact_phone column")
                except Exception as e:
                    print(f"❌ Error dropping contact_phone column: {e}")
            else:
                print("ℹ️ contact_phone column doesn't exist, skipping")
                
    except Exception as e:
        print(f"❌ Error in contact_phone downgrade: {e}")
        raise e 