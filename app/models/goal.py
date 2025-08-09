"""
Athletic Goal model.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class GoalType(enum.Enum):
    """Types of athletic goals."""
    TRIATHLON = "triathlon"
    MARATHON = "marathon"
    HALF_MARATHON = "half_marathon"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    GENERAL_FITNESS = "general_fitness"


class GoalStatus(enum.Enum):
    """Goal status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Goal(Base):
    """Athletic goal model."""
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Goal details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(SQLEnum(GoalType), nullable=False)
    status = Column(SQLEnum(GoalStatus), default=GoalStatus.PLANNING)
    
    # Event details
    event_date = Column(Date, nullable=False)
    event_location = Column(String(255), nullable=True)
    
    # Triathlon specific distances (in meters/miles as appropriate)
    swim_distance_meters = Column(Float, nullable=True)
    bike_distance_miles = Column(Float, nullable=True)
    run_distance_miles = Column(Float, nullable=True)
    
    # Current fitness baseline
    current_swim_ability = Column(String(255), nullable=True)
    current_bike_ability = Column(String(255), nullable=True)
    current_run_ability = Column(String(255), nullable=True)
    
    # Target times (in minutes)
    target_swim_time = Column(Integer, nullable=True)
    target_bike_time = Column(Integer, nullable=True)
    target_run_time = Column(Integer, nullable=True)
    target_total_time = Column(Integer, nullable=True)
    
    # Training plan phases
    total_weeks = Column(Integer, nullable=True)
    current_week = Column(Integer, default=1)
    current_phase = Column(String(100), nullable=True)  # base, build, peak, taper
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="goals")
    training_plans = relationship("TrainingPlan", back_populates="goal")
    workout_logs = relationship("WorkoutLog", back_populates="goal")
    
    @property
    def days_until_event(self) -> int:
        """Calculate days until event."""
        if self.event_date:
            return (self.event_date - date.today()).days
        return 0
    
    @property
    def weeks_until_event(self) -> int:
        """Calculate weeks until event."""
        return max(0, self.days_until_event // 7)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate training progress percentage."""
        if self.total_weeks and self.current_week:
            return min(100.0, (self.current_week / self.total_weeks) * 100)
        return 0.0
    
    def __repr__(self):
        return f"<Goal(id={self.id}, title='{self.title}', type='{self.goal_type.value}')>"
