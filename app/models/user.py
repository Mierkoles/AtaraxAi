"""
User model.
"""
from datetime import datetime, date
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Date, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    """User model with athletic profile."""
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Athletic profile
    birth_date = Column(Date, nullable=True)
    height_inches = Column(Float, nullable=True)  # Height in inches
    weight_lbs = Column(Float, nullable=True)     # Weight in pounds
    fitness_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    
    # System fields
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    goals = relationship("Goal", back_populates="user")
    workout_logs = relationship("WorkoutLog", back_populates="user")
    
    @property
    def age(self) -> int:
        """Calculate age from birth date."""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return 0
    
    @property
    def bmi(self) -> float:
        """Calculate BMI."""
        if self.height_inches and self.weight_lbs:
            height_m = self.height_inches * 0.0254
            weight_kg = self.weight_lbs * 0.453592
            return weight_kg / (height_m ** 2)
        return 0.0
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
