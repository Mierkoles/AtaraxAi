"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, goals

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
