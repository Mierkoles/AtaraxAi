"""
User repository implementation.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository with additional user-specific methods."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100):
        """Get all active users."""
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        """Create a new user."""
        return self.create(db, obj_in=user_in)
    
    def activate_user(self, db: Session, *, user: User) -> User:
        """Activate a user."""
        user.is_active = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def deactivate_user(self, db: Session, *, user: User) -> User:
        """Deactivate a user."""
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


# Create a global instance
user_repository = UserRepository()
