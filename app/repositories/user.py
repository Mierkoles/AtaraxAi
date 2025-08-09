"""
User repository implementation.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.security.auth import get_password_hash, verify_password


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository with additional user-specific methods."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()
    
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
        """Create a new user with hashed password."""
        user_data = user_in.dict()
        password = user_data.pop("password")
        user_data["hashed_password"] = get_password_hash(password)
        
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser
    
    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """Update user password."""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
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
