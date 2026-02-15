import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
import os
from dotenv import load_dotenv
from app.db.models import User

async def check_users():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            result = await session.execute(select(User))
            users = result.scalars().all()
            print(f"Total users: {len(users)}")
            for u in users:
                print(f" - {u.email} ({u.full_name})")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    import sys
    # Add backend to path
    project_root = os.path.abspath(os.path.dirname(__file__))
    backend_path = os.path.join(project_root, "backend")
    sys.path.append(backend_path)
    asyncio.run(check_users())
