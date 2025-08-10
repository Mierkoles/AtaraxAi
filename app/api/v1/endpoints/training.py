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
from app.schemas.training import TrainingPlan as TrainingPlanSchema, Workout as WorkoutSchema

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a workout as completed by creating a workout log entry.
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
    
    # Create workout log to mark as completed
    workout_log = WorkoutLog(
        user_id=current_user.id,
        goal_id=workout.training_plan.goal_id,
        workout_id=workout_id,
        completed_date=date.today(),
        actual_duration_minutes=workout.duration_minutes or 30
    )
    
    db.add(workout_log)
    db.commit()
    
    return {"message": "Workout marked as completed", "workout_id": workout_id}
