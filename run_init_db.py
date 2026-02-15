import asyncio
from app.db.session import init_db
import os
from dotenv import load_dotenv

async def run_init():
    load_dotenv()
    print("Initializing database...")
    try:
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error during initialization: {e}")

if __name__ == "__main__":
    import sys
    # Add backend to path
    project_root = os.path.abspath(os.path.dirname(__file__))
    backend_path = os.path.join(project_root, "backend")
    sys.path.append(backend_path)
    asyncio.run(run_init())
