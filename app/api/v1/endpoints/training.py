"""
Training and workout API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.training import TrainingPlan, Workout
from app.schemas.training import TrainingPlan as TrainingPlanSchema, Workout as WorkoutSchema, WorkoutCompletionRequest
from app.services.adaptive_training_generator import update_training_plan_rolling_window

router = APIRouter()


@router.get("/plans", response_model=List[TrainingPlanSchema])
def read_training_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all training plans for the current user.
    """
    plans = (
        db.query(TrainingPlan)
        .join(TrainingPlan.goal)
        .filter_by(user_id=current_user.id)
        .all()
    )
    return plans


@router.get("/plans/{plan_id}", response_model=TrainingPlanSchema)
def read_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific training plan by ID.
    """
    plan = (
        db.query(TrainingPlan)
        .join(TrainingPlan.goal)
        .filter(TrainingPlan.id == plan_id)
        .filter_by(user_id=current_user.id)
        .first()
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    
    return plan


@router.get("/workouts", response_model=List[WorkoutSchema])
def read_workouts(
    skip: int = 0,
    limit: int = 100,
    week: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workouts for the current user, optionally filtered by week.
    """
    query = (
        db.query(Workout)
        .join(Workout.training_plan)
        .join(TrainingPlan.goal)
        .filter_by(user_id=current_user.id)
    )
    
    if week is not None:
        query = query.filter(Workout.week_number == week)
    
    workouts = query.offset(skip).limit(limit).all()
    return workouts


@router.get("/workouts/current", response_model=List[WorkoutSchema])
def read_current_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workouts for the current week based on active goal.
    """
    from app.repositories.goal import goal_repository
    
    # Get active goal
    active_goal = goal_repository.get_active_goal(db, user_id=current_user.id)
    if not active_goal:
        return []
    
    # Get current week workouts
    current_week = active_goal.current_week or 1
    workouts = (
        db.query(Workout)
        .join(Workout.training_plan)
        .filter(TrainingPlan.goal_id == active_goal.id)
        .filter(Workout.week_number == current_week)
        .all()
    )
    
    return workouts


@router.get("/workouts/{workout_id}", response_model=WorkoutSchema)
def read_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific workout by ID.
    """
    workout = (
        db.query(Workout)
        .join(Workout.training_plan)
        .join(TrainingPlan.goal)
        .filter(Workout.id == workout_id)
        .filter_by(user_id=current_user.id)
        .first()
    )
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    return workout


@router.put("/workouts/{workout_id}/complete")
def complete_workout(
    workout_id: int,
    completion_data: WorkoutCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a workout as completed by creating a workout log entry with user feedback.
    """
    from app.models.training import WorkoutLog
    from datetime import date
    
    workout = (
        db.query(Workout)
        .join(Workout.training_plan)
        .join(TrainingPlan.goal)
        .filter(Workout.id == workout_id)
        .filter_by(user_id=current_user.id)
        .first()
    )
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    # Check if already completed
    if workout.is_completed:
        return {"message": "Workout already completed", "workout_id": workout_id}
    
    # Create workout log to mark as completed with feedback
    workout_log = WorkoutLog(
        user_id=current_user.id,
        goal_id=workout.training_plan.goal_id,
        workout_id=workout_id,
        completed_date=date.today(),
        actual_duration_minutes=completion_data.actual_duration_minutes or workout.duration_minutes or 30,
        perceived_exertion=completion_data.perceived_exertion,
        energy_level=completion_data.energy_level,
        enjoyment_level=completion_data.enjoyment_level,
        weather_conditions=completion_data.weather_conditions,
        notes=completion_data.notes
    )
    
    db.add(workout_log)
    db.commit()
    
    # After completing a workout, check if we need to update rolling plan
    try:
        # Get current week (simplified - you might want more sophisticated logic)
        from datetime import date
        goal = workout.training_plan.goal
        if goal.created_at:
            days_since_start = (date.today() - goal.created_at.date()).days
            current_week = max(1, (days_since_start // 7) + 1)
            
            # Update rolling plan if needed
            updated = update_training_plan_rolling_window(db, workout.training_plan, current_week)
            if updated:
                db.commit()  # Commit the new workouts
        
    except Exception as e:
        # Don't let plan update failures affect workout completion
        print(f"Warning: Failed to update rolling plan: {e}")
    
    return {
        "message": "Workout marked as completed with feedback", 
        "workout_id": workout_id,
        "feedback_collected": {
            "perceived_exertion": completion_data.perceived_exertion,
            "energy_level": completion_data.energy_level,
            "enjoyment_level": completion_data.enjoyment_level,
            "has_notes": bool(completion_data.notes)
        }
    }


@router.post("/plans/{plan_id}/update-rolling")
def update_rolling_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger an update of the rolling training plan window.
    """
    from datetime import date
    
    # Get the training plan
    plan = (
        db.query(TrainingPlan)
        .join(TrainingPlan.goal)
        .filter(TrainingPlan.id == plan_id)
        .filter_by(user_id=current_user.id)
        .first()
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    
    # Calculate current week
    if plan.goal.created_at:
        days_since_start = (date.today() - plan.goal.created_at.date()).days
        current_week = max(1, (days_since_start // 7) + 1)
    else:
        current_week = 1
    
    # Update rolling plan
    updated = update_training_plan_rolling_window(db, plan, current_week)
    
    if updated:
        db.commit()
        return {
            "message": "Training plan updated successfully",
            "plan_id": plan_id,
            "current_week": current_week,
            "new_workouts_generated": True
        }
    else:
        return {
            "message": "No updates needed",
            "plan_id": plan_id,
            "current_week": current_week,
            "new_workouts_generated": False
        }


@router.get("/plans/{plan_id}/adaptation-status")
def get_plan_adaptation_status(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get information about plan adaptations and feedback analysis.
    """
    from app.services.adaptive_training_generator import AdaptiveTrainingGenerator
    
    # Get the training plan
    plan = (
        db.query(TrainingPlan)
        .join(TrainingPlan.goal)
        .filter(TrainingPlan.id == plan_id)
        .filter_by(user_id=current_user.id)
        .first()
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    
    generator = AdaptiveTrainingGenerator()
    
    # Get max generated week
    max_week = generator._get_max_generated_week(db, plan_id)
    
    # Get feedback analysis
    feedback_data = generator._analyze_recent_feedback(db, current_user.id)
    
    # Calculate current week
    from datetime import date
    if plan.goal.created_at:
        days_since_start = (date.today() - plan.goal.created_at.date()).days
        current_week = max(1, (days_since_start // 7) + 1)
    else:
        current_week = 1
    
    return {
        "plan_id": plan_id,
        "current_week": current_week,
        "max_generated_week": max_week,
        "weeks_ahead": max_week - current_week,
        "rolling_window_size": generator.ROLLING_WEEKS,
        "needs_update": max_week - current_week < generator.ROLLING_WEEKS,
        "feedback_analysis": feedback_data,
        "adaptation_active": feedback_data.get("has_feedback", False)
    }
