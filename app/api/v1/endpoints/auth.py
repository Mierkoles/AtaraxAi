"""
Authentication API endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.security.deps import get_current_user
from app.db.database import get_db
from app.repositories.user import user_repository
from app.schemas.user import Token, User, UserCreate, UserLogin

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    User login endpoint.
    """
    user = user_repository.authenticate(
        db, username=user_credentials.username, password=user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register", response_model=User)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    """
    Register new user.
    """
    # Check if user with this email already exists
    user = user_repository.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    # Check if user with this username already exists
    user = user_repository.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists."
        )
    
    user = user_repository.create_user(db, user_in=user_in)
    return user


@router.get("/me", response_model=User)
def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    """
    return current_user


@router.post("/logout")
def logout():
    """
    User logout endpoint.
    Note: With JWT tokens, logout is typically handled client-side by discarding the token.
    For more secure implementations, you might want to maintain a blacklist of tokens.
    """
    return {"message": "Successfully logged out"}


# OAuth2 compatible endpoint for testing with Swagger UI
@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login endpoint for Swagger UI.
    """
    user = user_repository.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
