"""Application settings using Pydantic.

Provides configuration management for security, CORS, and deployment settings.
"""
import os
from typing import List
from pydantic import BaseModel, validator


class Settings(BaseModel):
    """Application settings with validation."""

    # Security settings
    JWT_SECRET: str = "dev-secret-change-in-production"
    DEV_MODE: bool = True

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "sqlite:///./storage/app.db"

    # External APIs
    GOOGLE_API_KEY: str = ""

    # Rate limiting
    RATE_LIMIT_GENERATE: int = 60  # per minute
    RATE_LIMIT_DEFAULT: int = 300  # per minute

    def __init__(self, **data):
        # Load from environment variables
        env_data = {}
        for field_name in self.__fields__:
            env_value = os.getenv(field_name)
            if env_value is not None:
                if field_name == 'DEV_MODE':
                    env_data[field_name] = env_value.lower() in ('true', '1', 'yes')
                elif field_name == 'ALLOWED_ORIGINS':
                    env_data[field_name] = [origin.strip() for origin in env_value.split(',') if origin.strip()]
                elif field_name in ('RATE_LIMIT_GENERATE', 'RATE_LIMIT_DEFAULT'):
                    env_data[field_name] = int(env_value)
                else:
                    env_data[field_name] = env_value

        # Merge environment data with provided data
        merged_data = {**env_data, **data}
        super().__init__(**merged_data)

        # Validate JWT secret in production
        if not self.DEV_MODE and (not self.JWT_SECRET or len(self.JWT_SECRET) < 32 or self.JWT_SECRET == "dev-secret-change-in-production"):  # pragma: allowlist secret
            raise ValueError("JWT_SECRET must be at least 32 characters in production mode")


# Global settings instance
settings = Settings()
