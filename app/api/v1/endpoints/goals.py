"""
Goals API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.goal import GoalType
from app.repositories.goal import goal_repository
from app.schemas.goal import Goal, GoalCreate, GoalUpdate, GoalSummary, TriathlonGoalCreate
from app.services.ai_training_generator import generate_ai_training_plan

router = APIRouter()


@router.get("/", response_model=List[GoalSummary])
def read_goals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve user's goals.
    """
    goals = goal_repository.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return goals


@router.post("/", response_model=Goal)
def create_goal(
    *,
    db: Session = Depends(get_db),
    goal_in: GoalCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new goal with AI-generated training plan.
    """
    # Check if user has an active goal (one goal at a time)
    active_goal = goal_repository.get_active_goal(db, user_id=current_user.id)
    if active_goal:
        raise HTTPException(
            status_code=400,
            detail="You already have an active goal. Please complete or pause it before creating a new one."
        )
    
    # Create goal using the general method (not just triathlon)
    goal = goal_repository.create_goal(db, user_id=current_user.id, goal_in=goal_in)
    
    # Generate AI training plan for any goal type
    try:
        training_plan = generate_ai_training_plan(db, goal, current_user)
        goal.status = "active"  # Activate the goal
        db.commit()
        db.refresh(goal)
    except Exception as e:
        # If training plan generation fails, we still have the goal
        print(f"Training plan generation failed: {e}")
    
    return goal


@router.post("/triathlon", response_model=Goal)
def create_triathlon_goal(
    *,
    db: Session = Depends(get_db),
    goal_in: TriathlonGoalCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new triathlon goal with specific setup.
    """
    # Check if user has an active goal
    active_goal = goal_repository.get_active_goal(db, user_id=current_user.id)
    if active_goal:
        raise HTTPException(
            status_code=400,
            detail="You already have an active goal. Please complete or pause it before creating a new one."
        )
    
    # Convert to GoalCreate format
    goal_data = goal_in.dict()
    goal_data["goal_type"] = "triathlon"
    goal_create = GoalCreate(**goal_data)
    
    goal = goal_repository.create_triathlon_goal(db, user_id=current_user.id, goal_in=goal_create)
    return goal


@router.get("/active", response_model=Goal)
def read_active_goal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's active goal.
    """
    goal = goal_repository.get_active_goal(db, user_id=current_user.id)
    if goal is None:
        raise HTTPException(status_code=404, detail="No active goal found")
    return goal


@router.get("/{goal_id}", response_model=Goal)
def read_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific goal by ID.
    """
    goal = goal_repository.get(db, id=goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check if goal belongs to current user
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return goal


@router.put("/{goal_id}", response_model=Goal)
def update_goal(
    *,
    db: Session = Depends(get_db),
    goal_id: int,
    goal_in: GoalUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a goal.
    """
    goal = goal_repository.get(db, id=goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check if goal belongs to current user
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    goal = goal_repository.update(db, db_obj=goal, obj_in=goal_in)
    return goal


@router.post("/{goal_id}/activate", response_model=Goal)
def activate_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activate a goal (deactivates other goals).
    """
    goal = goal_repository.get(db, id=goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check if goal belongs to current user
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    goal = goal_repository.activate_goal(db, goal=goal)
    return goal


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a goal.
    """
    goal = goal_repository.get(db, id=goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check if goal belongs to current user
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    goal = goal_repository.remove(db, id=goal_id)
    return {"message": "Goal deleted successfully"}
