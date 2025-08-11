#!/usr/bin/env python3
"""
Add new columns to the goal table for enhanced personal information.
"""
import sqlite3
from datetime import datetime

def update_goal_table():
    """Add new columns to the goal table."""
    
    print("Updating goal table schema...")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('atarax.db')
        cursor = conn.cursor()
        
        # Check if the new columns already exist
        cursor.execute("PRAGMA table_info(goal)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = [
            ('birth_date', 'DATE'),
            ('medical_conditions', 'TEXT'),
            ('training_experience', 'VARCHAR(50)')
        ]
        
        # Add new columns if they don't exist
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE goal ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists")
        
        # Commit the changes
        conn.commit()
        print("Database schema updated successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(goal)")
        updated_columns = cursor.fetchall()
        print("\\nUpdated goal table columns:")
        for col in updated_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function."""
    success = update_goal_table()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())