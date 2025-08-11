#!/usr/bin/env python3
"""
Add a test workout for today so we can test the feedback system.
"""

import sys
from datetime import date
from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.user import User
from app.models.goal import Goal
from app.models.training import TrainingPlan, Workout, WorkoutType, WorkoutIntensity, TrainingPhase

def add_test_workout():
    """Add a test workout for today."""
    
    print("Adding test workout for today...")
    
    # Create database session
    db = Session(engine)
    
    try:
        # Find the first user and their active goal
        user = db.query(User).first()
        if not user:
            print("No user found. Please create an account first.")
            return False
        
        # Find active goal
        goal = db.query(Goal).filter(Goal.user_id == user.id).first()
        if not goal:
            print("No goal found. Please create a goal first.")
            return False
        
        # Find training plan
        plan = db.query(TrainingPlan).filter(TrainingPlan.goal_id == goal.id).first()
        if not plan:
            print("No training plan found. Please create a goal first.")
            return False
        
        # Get today's day of week (0=Monday, 6=Sunday) 
        today = date.today()
        day_of_week = today.weekday()  # Monday = 0
        
        print(f"Today is {today.strftime('%A')} (day_of_week = {day_of_week})")
        
        # Create a test workout for today (always uses today's date)
        test_workout = Workout(
            training_plan_id=plan.id,
            week_number=1,  # Week 1
            day_of_week=day_of_week,
            scheduled_date=today,  # Set specific date to today
            name=f"Test Feedback System - {today.strftime('%A')}",
            description="Test workout to try the new adaptive feedback system",
            instructions="Complete this workout and provide feedback using the new rating system! Rate the difficulty, your energy level, and how much you enjoyed it. Your feedback will be used to adapt future workouts.",
            workout_type=WorkoutType.RUN,
            phase=TrainingPhase.BASE,
            intensity=WorkoutIntensity.MODERATE,
            duration_minutes=30,
            distance_miles=2.0,
            weekly_focus="Testing the adaptive feedback and rolling plan generation system"
        )
        
        db.add(test_workout)
        db.commit()
        db.refresh(test_workout)
        
        print(f"SUCCESS: Added test workout: {test_workout.name}")
        print(f"   - Type: {test_workout.workout_type.value}")
        print(f"   - Intensity: {test_workout.intensity.value}")
        print(f"   - Duration: {test_workout.duration_minutes} minutes")
        print(f"   - Week {test_workout.week_number}, Day {test_workout.day_of_week}")
        print(f"   - ID: {test_workout.id}")
        
        return True
        
    except Exception as e:
        print(f"Error adding test workout: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = add_test_workout()
    if success:
        print("\nReady to test! Go to the Training page and you should see today's workout.")
        print("   Complete it and try the feedback modal with different ratings!")
    sys.exit(0 if success else 1)