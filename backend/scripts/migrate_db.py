import asyncio
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Checking columns in 'credential' table...")
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'credential'"))
        columns = [r[0] for r in res]
        print(f"Columns found: {columns}")
        
        if 'workspace_id' not in columns:
            print("Adding missing 'workspace_id' column to 'credential' table...")
            # We'll make it nullable (optional) from the start
            await conn.execute(text("ALTER TABLE credential ADD COLUMN workspace_id VARCHAR"))
            # Make it a foreign key if you want, but the priority is making it work
            try:
                await conn.execute(text("ALTER TABLE credential ADD CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspace (id)"))
                print("Foreign key constraint added.")
            except Exception as e:
                print(f"Warning: Could not add foreign key constraint: {e}")
            
            print("Migration complete!")
        else:
            print("workspace_id column already exists. Ensuring it is nullable...")
            await conn.execute(text("ALTER TABLE credential ALTER COLUMN workspace_id DROP NOT NULL"))
            print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
