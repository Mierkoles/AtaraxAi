#!/usr/bin/env python3
"""
Migration script to add new user profile fields.
"""
import sqlite3
import os

def migrate_database():
    """Add new user profile fields to the user table."""
    db_path = "atarax.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing user columns: {existing_columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ("bmi_known", "REAL"),
            ("body_type", "VARCHAR(50)"),
            ("medical_conditions", "VARCHAR(1000)")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists")
        
        # Update birth_date to be NOT NULL (but we'll do this manually for existing data)
        # Note: SQLite doesn't support modifying column constraints easily, 
        # so we'll handle this in the application logic
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()