"""
User API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.user import user_repository
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve users.
    """
    users = user_repository.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    """
    Create new user.
    """
    # Check if user with this email already exists
    user = user_repository.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    user = user_repository.create_user(db, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.
    """
    user = user_repository.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate
):
    """
    Update a user.
    """
    user = user_repository.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_repository.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", response_model=User)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    """
    user = user_repository.get(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_repository.remove(db, id=user_id)
    return user


@router.get("/email/{email}", response_model=User)
def read_user_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get a user by email address.
    """
    user = user_repository.get_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
