"""
Training Pydantic schemas.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.training import WorkoutType, WorkoutIntensity, TrainingPhase


# Training Plan Schemas
class TrainingPlanBase(BaseModel):
    """Base training plan schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    total_weeks: Optional[int] = None
    base_weeks: Optional[int] = None
    build_weeks: Optional[int] = None
    peak_weeks: Optional[int] = None
    taper_weeks: Optional[int] = None
    weekly_swim_sessions: Optional[int] = None
    weekly_bike_sessions: Optional[int] = None
    weekly_run_sessions: Optional[int] = None
    weekly_strength_sessions: Optional[int] = None


class TrainingPlanCreate(TrainingPlanBase):
    """Schema for creating a training plan."""
    name: str
    total_weeks: int


class TrainingPlan(TrainingPlanBase):
    """Schema for returning training plan data."""
    id: int
    goal_id: int
    is_generated: bool
    generated_at: Optional[date]
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Workout Schemas
class WorkoutBase(BaseModel):
    """Base workout schema."""
    name: Optional[str] = None
    workout_type: Optional[WorkoutType] = None
    intensity: Optional[WorkoutIntensity] = None
    phase: Optional[TrainingPhase] = None
    duration_minutes: Optional[int] = None
    distance_miles: Optional[float] = None
    description: Optional[str] = None
    instructions: Optional[str] = None


class WorkoutCreate(WorkoutBase):
    """Schema for creating a workout."""
    name: str
    workout_type: WorkoutType
    intensity: WorkoutIntensity
    week_number: int
    day_of_week: int


class Workout(WorkoutBase):
    """Schema for returning workout data."""
    id: int
    training_plan_id: int
    week_number: int
    day_of_week: int
    scheduled_date: Optional[date]
    is_completed: bool
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Workout Log Schemas
class WorkoutLogBase(BaseModel):
    """Base workout log schema."""
    completed_date: Optional[date] = None
    actual_duration_minutes: Optional[int] = None
    actual_distance_miles: Optional[float] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    calories_burned: Optional[int] = None
    perceived_exertion: Optional[int] = None
    energy_level: Optional[int] = None
    enjoyment_level: Optional[int] = None
    notes: Optional[str] = None
    weather_conditions: Optional[str] = None


class WorkoutLogCreate(WorkoutLogBase):
    """Schema for creating a workout log."""
    workout_id: Optional[int] = None
    completed_date: date
    actual_duration_minutes: int


class WorkoutLogUpdate(WorkoutLogBase):
    """Schema for updating a workout log."""
    pass


class WorkoutLog(WorkoutLogBase):
    """Schema for returning workout log data."""
    id: int
    user_id: int
    goal_id: int
    workout_id: Optional[int]
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Combined schemas for dashboard views
class DailyWorkout(BaseModel):
    """Daily workout view for dashboard."""
    date: date
    workouts: List[Workout]
    completed_count: int
    total_count: int


class WeeklyPlan(BaseModel):
    """Weekly training plan view."""
    week_number: int
    start_date: date
    phase: TrainingPhase
    workouts: List[Workout]
    total_duration: int
    total_distance: float


class WorkoutProgress(BaseModel):
    """Workout progress tracking."""
    workout: Workout
    log: Optional[WorkoutLog]
    is_overdue: bool
    days_since_scheduled: int


# Training analytics
class TrainingStats(BaseModel):
    """Training statistics."""
    total_workouts_planned: int
    total_workouts_completed: int
    completion_rate: float
    total_training_time: int
    total_distance: float
    current_streak: int
    longest_streak: int
    average_weekly_hours: float


class PhaseProgress(BaseModel):
    """Training phase progress."""
    phase: TrainingPhase
    weeks_completed: int
    weeks_total: int
    progress_percentage: float
    next_phase: Optional[TrainingPhase]
    phase_description: str
