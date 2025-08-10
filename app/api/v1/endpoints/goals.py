"""
Goals API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.goal import GoalType, GoalStatus
from app.repositories.goal import goal_repository
from app.schemas.goal import Goal, GoalCreate, GoalUpdate, GoalSummary, TriathlonGoalCreate
from app.services.claude_training_generator import create_claude_training_plan

router = APIRouter()


@router.get("/", response_model=List[Goal])
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
    return [Goal.model_validate(goal) for goal in goals]


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
    
    # Generate AI-powered training plan with Claude
    try:
        training_plan = create_claude_training_plan(db, goal, current_user)
        goal.status = GoalStatus.ACTIVE  # Activate the goal
        db.commit()
        db.refresh(goal)
    except Exception as e:
        # If Claude fails, fall back to simple generator
        print(f"Claude training plan generation failed: {e}")
        print("Falling back to simple training generator...")
        try:
            from app.services.simple_training_generator import create_simple_training_plan
            training_plan = create_simple_training_plan(db, goal, current_user)
            goal.status = GoalStatus.ACTIVE  # Activate the goal
            db.commit()
            db.refresh(goal)
        except Exception as e2:
            print(f"Simple training plan generation also failed: {e2}")
            goal.status = GoalStatus.PLANNING  # Keep goal in planning state
            db.commit()
            db.refresh(goal)
    
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


@router.get("/dashboard", response_model=dict)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard data for user including active goal, completed goals, and onboarding status.
    This endpoint provides a comprehensive view for new users without active goals.
    """
    # Get active goal
    active_goal = goal_repository.get_active_goal(db, user_id=current_user.id)
    
    # Get all user goals to show completed ones
    all_goals = goal_repository.get_by_user(db, user_id=current_user.id)
    
    # Separate completed goals
    completed_goals = [goal for goal in all_goals if goal.status == GoalStatus.COMPLETED]
    
    # Determine user state
    is_new_user = len(all_goals) == 0
    has_completed_goals = len(completed_goals) > 0
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "email": current_user.email
        },
        "active_goal": Goal.model_validate(active_goal) if active_goal else None,
        "completed_goals": [Goal.model_validate(goal) for goal in completed_goals],
        "total_goals": len(all_goals),
        "is_new_user": is_new_user,
        "has_completed_goals": has_completed_goals,
        "onboarding_status": {
            "needs_first_goal": is_new_user,
            "show_goal_creation": not active_goal,
            "show_completed_goals": has_completed_goals
        }
    }


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


@router.put("/{goal_id}/pause", response_model=Goal)
def pause_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pause an active goal.
    """
    goal = goal_repository.get(db, id=goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal.status = GoalStatus.PAUSED
    db.commit()
    db.refresh(goal)
    return Goal.model_validate(goal)


@router.put("/{goal_id}/cancel", response_model=Goal)
def cancel_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a goal and mark it as cancelled.
    """
    goal = goal_repository.get(db, id=goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal.status = GoalStatus.CANCELLED
    db.commit()
    db.refresh(goal)
    return Goal.model_validate(goal)


@router.put("/{goal_id}/archive", response_model=Goal)
def archive_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive a completed goal.
    """
    goal = goal_repository.get(db, id=goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    if goal.status != GoalStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed goals can be archived")
    
    # For now, we'll just mark it as cancelled to hide it from normal view
    # In the future, you could add an 'archived' status to the enum
    goal.status = GoalStatus.CANCELLED
    db.commit()
    db.refresh(goal)
    return Goal.model_validate(goal)


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a goal and all associated training plans and workouts.
    """
    goal = goal_repository.get(db, id=goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check if goal belongs to current user
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        # Delete associated training plans and workouts first (cascade should handle this)
        from app.models.training import TrainingPlan, Workout
        
        # Delete workouts first
        training_plans = db.query(TrainingPlan).filter(TrainingPlan.goal_id == goal_id).all()
        for plan in training_plans:
            db.query(Workout).filter(Workout.training_plan_id == plan.id).delete()
        
        # Delete training plans
        db.query(TrainingPlan).filter(TrainingPlan.goal_id == goal_id).delete()
        
        # Delete the goal
        db.delete(goal)
        db.commit()
        
        return {"message": "Goal deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")
