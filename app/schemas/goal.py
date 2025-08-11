"""
Goal Pydantic schemas.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.goal import GoalType, GoalStatus


# Shared properties
class GoalBase(BaseModel):
    """Base goal schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    goal_type: Optional[GoalType] = None
    event_date: Optional[date] = None
    event_location: Optional[str] = None
    
    # Event distances (for running/cycling/triathlon)
    swim_distance_meters: Optional[float] = None
    bike_distance_miles: Optional[float] = None
    run_distance_miles: Optional[float] = None
    
    # Weight/body composition goals
    target_weight_lbs: Optional[float] = None
    current_weight_lbs: Optional[float] = None
    target_body_fat_percent: Optional[float] = None
    
    # Strength goals
    target_bench_press_lbs: Optional[float] = None
    target_squat_lbs: Optional[float] = None
    target_deadlift_lbs: Optional[float] = None
    
    # Current fitness baseline
    current_fitness_assessment: Optional[str] = None
    current_swim_ability: Optional[str] = None
    current_bike_ability: Optional[str] = None
    current_run_ability: Optional[str] = None
    
    # Target times (in minutes)
    target_swim_time: Optional[int] = None
    target_bike_time: Optional[int] = None
    target_run_time: Optional[int] = None
    target_total_time: Optional[int] = None
    
    # Training preferences
    preferred_workout_days: Optional[List[str]] = None
    available_equipment: Optional[List[str]] = None
    time_per_workout_minutes: Optional[int] = None
    workouts_per_week: Optional[int] = None
    
    # Personal information for AI training plan generation
    birth_date: Optional[date] = None
    medical_conditions: Optional[str] = None
    training_experience: Optional[str] = None
    
    # Training plan phases
    base_weeks: Optional[int] = None
    build_weeks: Optional[int] = None
    peak_weeks: Optional[int] = None
    taper_weeks: Optional[int] = None


# Properties to receive via API on creation
class GoalCreate(GoalBase):
    """Schema for creating a goal."""
    title: str
    goal_type: GoalType
    event_date: Optional[date] = None  # Some goals might not have events
    
    # Current fitness assessment (required for AI planning)
    current_fitness_assessment: str  # General fitness description


# Properties to receive via API on update
class GoalUpdate(GoalBase):
    """Schema for updating a goal."""
    status: Optional[GoalStatus] = None
    current_week: Optional[int] = None
    current_phase: Optional[str] = None


# Properties to return via API
class Goal(GoalBase):
    """Schema for returning goal data."""
    id: int
    user_id: int
    status: GoalStatus
    total_weeks: Optional[int]
    current_week: int
    current_phase: Optional[str]
    days_until_event: int
    weeks_until_event: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Goal with training plan preview
class GoalWithPlan(Goal):
    """Goal with training plan information."""
    has_training_plan: bool = False
    current_week_workouts: Optional[int] = None
    completed_workouts: Optional[int] = None


# Goal list item (summary)
class GoalSummary(BaseModel):
    """Summary schema for goal lists."""
    id: int
    title: str
    goal_type: GoalType
    status: GoalStatus
    event_date: Optional[date]
    days_until_event: int
    progress_percentage: float
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Triathlon goal specific schema
class TriathlonGoalCreate(BaseModel):
    """Schema for creating a triathlon goal with specific requirements."""
    title: str
    description: Optional[str] = None
    event_date: date
    event_location: Optional[str] = None
    
    # Triathlon distances
    swim_distance_meters: float = 750
    bike_distance_miles: float = 14.3
    run_distance_miles: float = 3.1
    
    # Current fitness assessment (required)
    current_swim_ability: str
    current_bike_ability: str  
    current_run_ability: str
    
    # Target times (optional)
    target_swim_time: Optional[int] = None
    target_bike_time: Optional[int] = None
    target_run_time: Optional[int] = None
    target_total_time: Optional[int] = None
