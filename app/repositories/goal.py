"""
Goal repository implementation.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models.goal import Goal, GoalStatus, GoalType
from app.repositories.base import BaseRepository
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalRepository(BaseRepository[Goal, GoalCreate, GoalUpdate]):
    """Goal repository with goal-specific methods."""
    
    def __init__(self):
        super().__init__(Goal)
    
    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Goal]:
        """Get goals for a specific user."""
        return (
            db.query(Goal)
            .filter(Goal.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_active_goal(self, db: Session, *, user_id: int) -> Optional[Goal]:
        """Get the active goal for a user (one goal at a time)."""
        return (
            db.query(Goal)
            .filter(Goal.user_id == user_id)
            .filter(Goal.status == GoalStatus.ACTIVE)
            .first()
        )
    
    def get_upcoming_events(self, db: Session, *, days_ahead: int = 30) -> List[Goal]:
        """Get goals with events in the next N days."""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        return (
            db.query(Goal)
            .filter(Goal.event_date <= cutoff_date)
            .filter(Goal.event_date >= date.today())
            .filter(Goal.status.in_([GoalStatus.ACTIVE, GoalStatus.PLANNING]))
            .order_by(Goal.event_date)
            .all()
        )
    
    def create_goal(self, db: Session, *, user_id: int, goal_in: GoalCreate) -> Goal:
        """Create any type of goal with AI planning."""
        # Calculate training weeks based on event date or default
        if goal_in.event_date:
            days_until_event = (goal_in.event_date - date.today()).days
            total_weeks = max(4, min(32, days_until_event // 7))  # 4-32 weeks
        else:
            # No event date - default to 12 weeks for general goals
            total_weeks = 12
        
        goal_data = goal_in.dict()
        goal_data["user_id"] = user_id
        goal_data["total_weeks"] = total_weeks
        goal_data["current_phase"] = "planning"
        goal_data["status"] = GoalStatus.PLANNING
        
        goal = Goal(**goal_data)
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal
    
    def create_triathlon_goal(self, db: Session, *, user_id: int, goal_in: GoalCreate) -> Goal:
        """Create a triathlon goal with training plan calculation."""
        # Use the general create_goal method
        return self.create_goal(db, user_id=user_id, goal_in=goal_in)
    
    def activate_goal(self, db: Session, *, goal: Goal) -> Goal:
        """Activate a goal and deactivate others for the same user."""
        # Deactivate other goals for this user
        db.query(Goal).filter(
            Goal.user_id == goal.user_id,
            Goal.id != goal.id,
            Goal.status == GoalStatus.ACTIVE
        ).update({"status": GoalStatus.PAUSED})
        
        # Activate this goal
        goal.status = GoalStatus.ACTIVE
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal
    
    def advance_week(self, db: Session, *, goal: Goal) -> Goal:
        """Advance goal to next week and update phase if needed."""
        goal.current_week += 1
        
        # Update phase based on week progression
        if goal.total_weeks:
            progress = goal.current_week / goal.total_weeks
            if progress < 0.4:
                goal.current_phase = "base"
            elif progress < 0.7:
                goal.current_phase = "build"
            elif progress < 0.9:
                goal.current_phase = "peak"
            else:
                goal.current_phase = "taper"
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal
    
    def complete_goal(self, db: Session, *, goal: Goal) -> Goal:
        """Mark goal as completed."""
        goal.status = GoalStatus.COMPLETED
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal
    
    def get_goals_by_type(self, db: Session, *, goal_type: GoalType) -> List[Goal]:
        """Get all goals of a specific type."""
        return db.query(Goal).filter(Goal.goal_type == goal_type).all()


# Create a global instance
goal_repository = GoalRepository()
