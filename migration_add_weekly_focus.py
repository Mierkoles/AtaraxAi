#!/usr/bin/env python3
"""
Migration script to add weekly_focus column to the workout table.
"""
import sqlite3
import os

def migrate_database():
    """Add weekly_focus column to workout table."""
    db_path = "atarax.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(workout)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'weekly_focus' not in columns:
            print("Adding weekly_focus column to workout table...")
            cursor.execute("ALTER TABLE workout ADD COLUMN weekly_focus TEXT")
        else:
            print("weekly_focus column already exists in workout table")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()