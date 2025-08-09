"""Database models package."""
from app.db.base_class import Base
from app.models.user import User
from app.models.goal import Goal, GoalType, GoalStatus
from app.models.training import (
    TrainingPlan, 
    Workout, 
    WorkoutLog, 
    WorkoutType, 
    WorkoutIntensity, 
    TrainingPhase
)
from app.models.nutrition import (
    NutritionGoal,
    MealPlan,
    Recipe,
    Meal,
    MealType,
    DietaryRestriction
)

# Import all models here for Alembic to detect them
__all__ = [
    "Base", 
    "User", 
    "Goal", 
    "GoalType", 
    "GoalStatus",
    "TrainingPlan", 
    "Workout", 
    "WorkoutLog", 
    "WorkoutType", 
    "WorkoutIntensity", 
    "TrainingPhase",
    "NutritionGoal",
    "MealPlan",
    "Recipe",
    "Meal",
    "MealType",
    "DietaryRestriction"
]
