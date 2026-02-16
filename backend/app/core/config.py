import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: str = os.getenv("REDIS_DB", "0")

    @property
    def REDIS_URL(self) -> str:
        if os.getenv("REDIS_URL"):
            return os.getenv("REDIS_URL")
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    WORKFLOW_TIMEOUT: int = 3600  # 1 hour
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8001")
    STUDIO_REGION: str = os.getenv("STUDIO_REGION", "us-east-1")
    
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
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
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

