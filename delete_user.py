import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

async def delete_user():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    # Use statement_cache_size=0 for Supabase compatibility
    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    
    email = "amalmanal239@gmail.com"
    
    async with engine.begin() as conn:
        try:
            print(f"Deleting user {email}...")
            # Delete from workspace_member first due to FK constraints (if any, usually cascade but just in case)
            # Actually, we should check what tables reference user.
            # Assuming standard cascade or manual cleanup.
            # Let's try deleting from 'user' table directly.
            
            # Note: User table is "user" (quoted)
            await conn.execute(text(f"DELETE FROM \"user\" WHERE email = '{email}'"))
            print("User deleted successfully.")
        except Exception as e:
            print(f"Error deleting user: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(delete_user())
