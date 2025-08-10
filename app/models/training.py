"""
Training and workout models.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class WorkoutType(enum.Enum):
    """Types of workouts."""
    SWIM = "swim"
    BIKE = "bike"
    RUN = "run"
    STRENGTH = "strength"
    REST = "rest"
    CROSS_TRAINING = "cross_training"
    BRICK = "brick"  # Combined bike + run


class WorkoutIntensity(enum.Enum):
    """Workout intensity levels."""
    RECOVERY = "recovery"
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    VERY_HARD = "very_hard"


class TrainingPhase(enum.Enum):
    """Training phases."""
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    RECOVERY = "recovery"


class TrainingPlan(Base):
    """Training plan model."""
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goal.id"), nullable=False)
    
    # Plan details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_weeks = Column(Integer, nullable=False)
    
    # Phase distribution (in weeks)
    base_weeks = Column(Integer, default=0)
    build_weeks = Column(Integer, default=0)
    peak_weeks = Column(Integer, default=0)
    taper_weeks = Column(Integer, default=0)
    
    # Weekly training volume targets
    weekly_swim_sessions = Column(Integer, default=2)
    weekly_bike_sessions = Column(Integer, default=2)
    weekly_run_sessions = Column(Integer, default=3)
    weekly_strength_sessions = Column(Integer, default=1)
    
    # Generated plan
    is_generated = Column(Boolean, default=False)
    generated_at = Column(Date, nullable=True)  # Keep this as Date since it only stores date
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    goal = relationship("Goal", back_populates="training_plans")
    workouts = relationship("Workout", back_populates="training_plan")
    
    def __repr__(self):
        return f"<TrainingPlan(id={self.id}, name='{self.name}')>"


class Workout(Base):
    """Individual workout model."""
    
    id = Column(Integer, primary_key=True, index=True)
    training_plan_id = Column(Integer, ForeignKey("trainingplan.id"), nullable=False)
    
    # Workout details
    name = Column(String(255), nullable=False)
    workout_type = Column(SQLEnum(WorkoutType), nullable=False)
    intensity = Column(SQLEnum(WorkoutIntensity), nullable=False)
    phase = Column(SQLEnum(TrainingPhase), nullable=False)
    
    # Scheduling
    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    scheduled_date = Column(Date, nullable=True)
    
    # Workout details
    duration_minutes = Column(Integer, nullable=True)
    distance_miles = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Swim specific
    pool_length_yards = Column(Integer, nullable=True)
    total_yards = Column(Integer, nullable=True)
    
    # Bike specific
    target_cadence = Column(Integer, nullable=True)
    target_power = Column(Integer, nullable=True)
    
    # Run specific
    target_pace_minutes = Column(Float, nullable=True)
    
    # Strength specific
    exercises = Column(Text, nullable=True)  # JSON string of exercises
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    training_plan = relationship("TrainingPlan", back_populates="workouts")
    workout_log = relationship("WorkoutLog", back_populates="workout", uselist=False)
    
    @property
    def is_completed(self) -> bool:
        """Check if workout is completed."""
        return self.workout_log is not None
    
    def __repr__(self):
        return f"<Workout(id={self.id}, name='{self.name}', type='{self.workout_type.value}')>"


class WorkoutLog(Base):
    """Workout completion log."""
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goal.id"), nullable=False)
    workout_id = Column(Integer, ForeignKey("workout.id"), nullable=True)
    
    # Completion details
    completed_date = Column(Date, nullable=False)
    actual_duration_minutes = Column(Integer, nullable=True)
    actual_distance_miles = Column(Float, nullable=True)
    
    # Performance metrics
    average_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    calories_burned = Column(Integer, nullable=True)
    
    # Subjective measures (1-10 scale)
    perceived_exertion = Column(Integer, nullable=True)
    energy_level = Column(Integer, nullable=True)
    enjoyment_level = Column(Integer, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    weather_conditions = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="workout_logs")
    goal = relationship("Goal", back_populates="workout_logs")
    workout = relationship("Workout", back_populates="workout_log")
    
    def __repr__(self):
        return f"<WorkoutLog(id={self.id}, date='{self.completed_date}')>"
