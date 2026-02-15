import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

async def patch():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        print("Adding stack_trace column to nodeexecution...")
        await conn.execute(text("ALTER TABLE nodeexecution ADD COLUMN IF NOT EXISTS stack_trace TEXT;"))
    await engine.dispose()
    print("Done")

if __name__ == "__main__":
    asyncio.run(patch())
