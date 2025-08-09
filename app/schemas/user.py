"""
User Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a user."""
    email: EmailStr
    full_name: Optional[str] = None


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating a user."""
    pass


# Properties to return via API
class User(UserBase):
    """Schema for returning user data."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True
