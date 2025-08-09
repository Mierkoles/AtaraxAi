"""
Test user endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.db.database import get_db
from app.db.base_class import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_user():
    """Test creating a new user."""
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data


def test_read_users():
    """Test reading users list."""
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_duplicate_user():
    """Test creating a user with duplicate email."""
    user_data = {
        "email": "duplicate@example.com",
        "full_name": "First User"
    }
    
    # Create first user
    response1 = client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post("/api/v1/users/", json=user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


def test_read_user_not_found():
    """Test reading a non-existent user."""
    response = client.get("/api/v1/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
