"""
Application configuration management.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App Info
    APP_NAME: str = "AtaraxAi"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "sqlite:///./atarax.db"
    
    # AI/LLM Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    USE_MOCK_CLAUDE: bool = False  # Set to True to use mock Claude service for testing
    
    # Azure Configuration
    AZURE_SQL_SERVER: Optional[str] = None
    AZURE_SQL_DATABASE: Optional[str] = None
    AZURE_SQL_USERNAME: Optional[str] = None
    AZURE_SQL_PASSWORD: Optional[str] = None
    
    # Azure Key Vault
    AZURE_KEY_VAULT_URL: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    
    @property
    def azure_sql_url(self) -> Optional[str]:
        """Construct Azure SQL connection URL."""
        if all([self.AZURE_SQL_SERVER, self.AZURE_SQL_DATABASE, 
                self.AZURE_SQL_USERNAME, self.AZURE_SQL_PASSWORD]):
            return (
                f"mssql+pyodbc://{self.AZURE_SQL_USERNAME}:{self.AZURE_SQL_PASSWORD}"
                f"@{self.AZURE_SQL_SERVER}/{self.AZURE_SQL_DATABASE}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
            )
        return None
    
    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL (Azure SQL if configured, otherwise SQLite)."""
        azure_url = self.azure_sql_url
        return azure_url if azure_url else self.DATABASE_URL
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
