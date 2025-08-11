#!/usr/bin/env python3
"""
Database cleanup script to remove all users, goals, workouts, and related data.

This script deletes data in the correct order to respect foreign key constraints:
1. WorkoutLog (depends on User, Goal, Workout)
2. Workout (depends on TrainingPlan)
3. TrainingPlan (depends on Goal)
4. Goal (depends on User)
5. User (base table)
"""

import sys
from sqlalchemy.orm import Session
from app.db.database import engine, get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.training import TrainingPlan, Workout, WorkoutLog


def cleanup_database():
    """Remove all data from the database."""
    
    print("Starting database cleanup...")
    
    # Create database session
    db = Session(engine)
    
    try:
        # Delete in order to respect foreign key constraints
        
        # 1. Delete WorkoutLog entries (depends on User, Goal, Workout)
        workout_logs_count = db.query(WorkoutLog).count()
        if workout_logs_count > 0:
            print(f"   Deleting {workout_logs_count} workout logs...")
            db.query(WorkoutLog).delete()
        
        # 2. Delete Workouts (depends on TrainingPlan)
        workouts_count = db.query(Workout).count()
        if workouts_count > 0:
            print(f"   Deleting {workouts_count} workouts...")
            db.query(Workout).delete()
        
        # 3. Delete TrainingPlans (depends on Goal)
        training_plans_count = db.query(TrainingPlan).count()
        if training_plans_count > 0:
            print(f"   Deleting {training_plans_count} training plans...")
            db.query(TrainingPlan).delete()
        
        # 4. Delete Goals (depends on User)
        goals_count = db.query(Goal).count()
        if goals_count > 0:
            print(f"   Deleting {goals_count} goals...")
            db.query(Goal).delete()
        
        # 5. Delete Users (base table)
        users_count = db.query(User).count()
        if users_count > 0:
            print(f"   Deleting {users_count} users...")
            db.query(User).delete()
        
        # Commit all deletions
        db.commit()
        
        print("Database cleanup completed successfully!")
        print("   All users, goals, training plans, workouts, and logs have been removed.")
        
        # Verify cleanup
        remaining_users = db.query(User).count()
        remaining_goals = db.query(Goal).count()
        remaining_plans = db.query(TrainingPlan).count()
        remaining_workouts = db.query(Workout).count()
        remaining_logs = db.query(WorkoutLog).count()
        
        print(f"\nVerification:")
        print(f"   Users remaining: {remaining_users}")
        print(f"   Goals remaining: {remaining_goals}")
        print(f"   Training plans remaining: {remaining_plans}")
        print(f"   Workouts remaining: {remaining_workouts}")
        print(f"   Workout logs remaining: {remaining_logs}")
        
        if (remaining_users == 0 and remaining_goals == 0 and 
            remaining_plans == 0 and remaining_workouts == 0 and remaining_logs == 0):
            print("Cleanup verification successful - database is empty!")
        else:
            print("WARNING: Some data may still remain in the database.")
            
    except Exception as e:
        print(f"ERROR during cleanup: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()
    
    return True


def confirm_cleanup():
    """Ask user for confirmation before deleting data."""
    
    print("WARNING: This will permanently delete ALL data from the database!")
    print("   This includes:")
    print("   - All user accounts")
    print("   - All fitness goals")
    print("   - All training plans")
    print("   - All workouts")
    print("   - All workout logs")
    print()
    
    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ").strip()
    
    if response == "YES":
        return True
    else:
        print("Cleanup cancelled.")
        return False


def main():
    """Main function to run the cleanup."""
    
    print("AtaraxAi Database Cleanup Utility")
    print("=" * 50)
    
    # Check if --force flag is provided to skip confirmation
    if "--force" in sys.argv:
        print("Force mode enabled - skipping confirmation")
        proceed = True
    else:
        proceed = confirm_cleanup()
    
    if proceed:
        success = cleanup_database()
        if success:
            print("\nDatabase cleanup completed successfully!")
            return 0
        else:
            print("\nDatabase cleanup failed!")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())