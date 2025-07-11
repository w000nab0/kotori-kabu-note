#!/usr/bin/env python3
"""Manual table creation script"""

from app.core.database import engine
from app.models.database import Base

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()