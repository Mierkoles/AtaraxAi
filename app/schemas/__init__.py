"""Pydantic schemas package."""
from app.schemas.user import (
    User, 
    UserCreate, 
    UserUpdate, 
    UserLogin, 
    UserProfile, 
    Token, 
    TokenData
)
from app.schemas.goal import (
    Goal, 
    GoalCreate, 
    GoalUpdate, 
    GoalSummary, 
    GoalWithPlan, 
    TriathlonGoalCreate
)
from app.schemas.training import (
    TrainingPlan,
    TrainingPlanCreate,
    Workout,
    WorkoutCreate,
    WorkoutLog,
    WorkoutLogCreate,
    WorkoutLogUpdate,
    DailyWorkout,
    WeeklyPlan,
    TrainingStats
)

__all__ = [
    # User schemas
    "User", 
    "UserCreate", 
    "UserUpdate", 
    "UserLogin", 
    "UserProfile", 
    "Token", 
    "TokenData",
    # Goal schemas
    "Goal", 
    "GoalCreate", 
    "GoalUpdate", 
    "GoalSummary", 
    "GoalWithPlan", 
    "TriathlonGoalCreate",
    # Training schemas
    "TrainingPlan",
    "TrainingPlanCreate",
    "Workout",
    "WorkoutCreate",
    "WorkoutLog",
    "WorkoutLogCreate",
    "WorkoutLogUpdate",
    "DailyWorkout",
    "WeeklyPlan",
    "TrainingStats"
]
