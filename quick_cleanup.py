#!/usr/bin/env python3
"""
Quick database cleanup script - no confirmation required.
"""

import sys
from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.user import User
from app.models.goal import Goal
from app.models.training import TrainingPlan, Workout, WorkoutLog

def quick_cleanup():
    """Remove all data from the database without confirmation."""
    
    print("Starting quick database cleanup...")
    
    # Create database session
    db = Session(engine)
    
    try:
        # Delete in order to respect foreign key constraints
        
        # 1. Delete WorkoutLog entries
        workout_logs_count = db.query(WorkoutLog).count()
        if workout_logs_count > 0:
            print(f"   Deleting {workout_logs_count} workout logs...")
            db.query(WorkoutLog).delete()
        
        # 2. Delete Workouts
        workouts_count = db.query(Workout).count()
        if workouts_count > 0:
            print(f"   Deleting {workouts_count} workouts...")
            db.query(Workout).delete()
        
        # 3. Delete TrainingPlans
        training_plans_count = db.query(TrainingPlan).count()
        if training_plans_count > 0:
            print(f"   Deleting {training_plans_count} training plans...")
            db.query(TrainingPlan).delete()
        
        # 4. Delete Goals
        goals_count = db.query(Goal).count()
        if goals_count > 0:
            print(f"   Deleting {goals_count} goals...")
            db.query(Goal).delete()
        
        # 5. Delete Users
        users_count = db.query(User).count()
        if users_count > 0:
            print(f"   Deleting {users_count} users...")
            db.query(User).delete()
        
        # Commit all deletions
        db.commit()
        
        print("Database cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = quick_cleanup()
    sys.exit(0 if success else 1)