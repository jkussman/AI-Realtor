"""
Initialize the database with the correct schema.
"""

import os
import sys
from sqlalchemy import create_engine
from db.models import Base
from db.database import DATABASE_URL

def init_db():
    """Initialize the database with all tables."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!") 