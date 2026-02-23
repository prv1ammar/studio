import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Resolve .env from the project root (3 levels up from this file)
_project_root = Path(__file__).resolve().parents[3]
_env_path = _project_root / ".env"

# Force load .env into environment variables BEFORE Settings class is defined
# This helps ensure local .env values are available
if _env_path.exists():
    load_dotenv(_env_path, override=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_PASSWORD: str = ""
    REDIS_DB: str = "0"

    @property
    def REDIS_URL(self) -> str:
        # Use credentials directly from fields
        if self.REDIS_PASSWORD:
            auth = f":{self.REDIS_PASSWORD}@"
        else:
            auth = ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    WORKFLOW_TIMEOUT: int = 3600  # 1 hour
    API_BASE_URL: str = "http://localhost:8001"
    STUDIO_REGION: str = "us-east-1"
    
    # Auth Settings
    SECRET_KEY: str = "super-secret-studio-key-replace-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    
    # Encryption
    ENCRYPTION_KEY: str = "u-1L6_R_5XWp_A5r9zR8hX1Bv-x4S8S3Wd5l_Uq9jW8=" # 32-byte b64 key
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/studio"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Phase 4: Performance & Scalability
    NODE_EXECUTION_TIMEOUT: int = 30  # seconds per node
    MAX_CONCURRENT_JOBS_PER_USER: int = 5
    MAX_CONCURRENT_JOBS_PER_WORKSPACE: int = 10
    WORKER_CONCURRENCY: int = 10  # Jobs per worker process
    CACHE_TTL: int = 300  # Redis cache TTL in seconds
    ENABLE_RESULT_CACHING: bool = True

settings = Settings()
