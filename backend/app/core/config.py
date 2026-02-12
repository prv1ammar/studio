import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    WORKFLOW_TIMEOUT: int = 3600  # 1 hour
    
    # Auth Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-studio-key-replace-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "u-1L6_R_5XWp_A5r9zR8hX1Bv-x4S8S3Wd5l_Uq9jW8=") # 32-byte b64 key
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/studio")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Phase 4: Performance & Scalability
    NODE_EXECUTION_TIMEOUT: int = int(os.getenv("NODE_EXECUTION_TIMEOUT", "30"))  # seconds per node
    MAX_CONCURRENT_JOBS_PER_USER: int = int(os.getenv("MAX_CONCURRENT_JOBS_PER_USER", "5"))
    MAX_CONCURRENT_JOBS_PER_WORKSPACE: int = int(os.getenv("MAX_CONCURRENT_JOBS_PER_WORKSPACE", "10"))
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "10"))  # Jobs per worker process
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # Redis cache TTL in seconds
    ENABLE_RESULT_CACHING: bool = os.getenv("ENABLE_RESULT_CACHING", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
