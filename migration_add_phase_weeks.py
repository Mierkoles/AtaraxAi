#!/usr/bin/env python3
"""
Migration script to add phase week columns to the goal table.
"""
import sqlite3
import os

def migrate_database():
    """Add phase week columns to goal table."""
    db_path = "atarax.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(goal)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = ['base_weeks', 'build_weeks', 'peak_weeks', 'taper_weeks']
        
        for column in new_columns:
            if column not in columns:
                print(f"Adding column {column} to goal table...")
                cursor.execute(f"ALTER TABLE goal ADD COLUMN {column} INTEGER")
            else:
                print(f"Column {column} already exists in goal table")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()