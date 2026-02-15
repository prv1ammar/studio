import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

async def test_db():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {db_url}")
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            print("Successfully connected to the database!")
    except Exception as e:
        print(f"Failed to connect: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db())
