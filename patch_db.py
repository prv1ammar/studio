import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

async def patch_db():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    
    queries = [
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'free';",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS tier_limits JSONB DEFAULT '{}';",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'active';",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMP WITHOUT TIME ZONE;",
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS preferred_region VARCHAR(50) DEFAULT 'us-east-1';",
        "ALTER TABLE auditlog ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(50);"
    ]
    
    for q in queries:
        async with engine.begin() as conn:
            try:
                print(f"Executing: {q}")
                await conn.execute(text(q))
                print(" - Success")
            except Exception as e:
                print(f" - Error: {e}")
                
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(patch_db())
