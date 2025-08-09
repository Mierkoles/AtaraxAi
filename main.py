"""
AtaraxAi - Main application entry point
"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.database import create_tables

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AtaraxAi - Athletic Training & Nutrition Platform",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Setup templates
    templates = Jinja2Templates(directory="templates")

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.on_event("startup")
    async def startup_event():
        """Initialize database tables on startup."""
        create_tables()

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Root endpoint - serve main application."""
        return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.APP_NAME})

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "app": settings.APP_NAME}

    return app

app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
