#!/usr/bin/env python3
"""
Create Alembic migration for goal enhancement fields.
"""
import subprocess
import sys

def create_migration():
    """Create a migration for the new goal fields."""
    
    print("Creating Alembic migration for goal enhancement fields...")
    
    try:
        # Create the migration
        result = subprocess.run([
            'alembic', 'revision', '--autogenerate', '-m', 'Add personal info fields to goals'
        ], capture_output=True, text=True, cwd='C:\\Dev\\repos\\AtaraxAi')
        
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print("Migration output:")
            print(result.stdout)
        else:
            print("❌ Error creating migration:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure it's installed.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    """Main function."""
    success = create_migration()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())