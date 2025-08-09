"""
User Pydantic schemas.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    height_inches: Optional[float] = None
    weight_lbs: Optional[float] = None
    fitness_level: Optional[str] = None
    is_active: Optional[bool] = True


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a user."""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating a user."""
    password: Optional[str] = None


# Properties for authentication
class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserProfile(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    height_inches: Optional[float] = None
    weight_lbs: Optional[float] = None
    fitness_level: Optional[str] = None


# Properties to return via API
class User(UserBase):
    """Schema for returning user data."""
    id: int
    age: int
    bmi: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Authentication response
class Token(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str
    user: User


class TokenData(BaseModel):
    """Token data for validation."""
    username: Optional[str] = None
