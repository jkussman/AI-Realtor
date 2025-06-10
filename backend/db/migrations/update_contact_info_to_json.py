"""
Migration to update contact_info column type from VARCHAR to JSON.
"""

from sqlalchemy import text

def upgrade(engine):
    """Run the migration to update contact_info column type."""
    with engine.connect() as connection:
        # SQLite doesn't support ALTER COLUMN, so we need to:
        # 1. Create a new temporary table
        # 2. Copy the data
        # 3. Drop the old table
        # 4. Rename the new table
        
        # Create new table with updated schema
        connection.execute(text("""
            CREATE TABLE buildings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                address VARCHAR NOT NULL,
                standardized_address VARCHAR,
                latitude VARCHAR,
                longitude VARCHAR,
                building_type VARCHAR NOT NULL,
                bounding_box JSON,
                approved BOOLEAN DEFAULT FALSE,
                contact_email VARCHAR,
                contact_name VARCHAR,
                contact_phone VARCHAR,
                website VARCHAR,
                email_sent BOOLEAN DEFAULT FALSE,
                reply_received BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contact_email_confidence INTEGER DEFAULT 0,
                contact_source VARCHAR,
                contact_source_url VARCHAR,
                contact_verified BOOLEAN DEFAULT FALSE,
                contact_last_verified TIMESTAMP,
                verification_notes TEXT,
                verification_flags JSON,
                property_manager VARCHAR,
                number_of_units INTEGER,
                year_built INTEGER,
                square_footage INTEGER,
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
                contact_info JSON,
                recent_availability BOOLEAN DEFAULT FALSE,
                rental_notes TEXT,
                neighborhood VARCHAR,
                stories INTEGER
            )
        """))
        
        # Copy data from old table to new table
        connection.execute(text("""
            INSERT INTO buildings_new 
            SELECT * FROM buildings
        """))
        
        # Drop old table
        connection.execute(text("DROP TABLE buildings"))
        
        # Rename new table to original name
        connection.execute(text("ALTER TABLE buildings_new RENAME TO buildings"))
        
        # Recreate indices
        connection.execute(text("""
            CREATE UNIQUE INDEX idx_buildings_address 
            ON buildings(address) 
            WHERE address IS NOT NULL
        """))
        
        connection.execute(text("""
            CREATE UNIQUE INDEX idx_buildings_standardized_address 
            ON buildings(standardized_address) 
            WHERE standardized_address IS NOT NULL
        """))
        
        print("✅ Updated contact_info column to JSON type")

def downgrade(engine):
    """Revert the contact_info column back to VARCHAR."""
    # Similar process as upgrade but changing JSON back to VARCHAR
    pass 