import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

async def clean_user():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    
    email = "amalmanal239@gmail.com"
    
    async with engine.begin() as conn:
        try:
            print(f"Cleaning data for {email}...")
            
            # 1. Get User ID
            result = await conn.execute(text(f"SELECT id FROM \"user\" WHERE email = '{email}'"))
            user_id = result.scalar()
            
            if not user_id:
                print("User not found.")
                return

            print(f"Found User ID: {user_id}")
            
            # 2. Delete Audit Logs
            print("Deleting audit logs...")
            await conn.execute(text(f"DELETE FROM auditlog WHERE user_id = '{user_id}'"))
            
            # 3. Delete Workspace Memberships
            print("Deleting workspace memberships...")
            await conn.execute(text(f"DELETE FROM workspacemember WHERE user_id = '{user_id}'"))
            
            # 4. Delete Workspaces owned by user
            print("Deleting workspaces...")
            ws_res = await conn.execute(text(f"SELECT id FROM workspace WHERE owner_id = '{user_id}'"))
            ws_ids = ws_res.scalars().all()
            for ws_id in ws_ids:
                pass
                # await conn.execute(text(f"DELETE FROM workflow WHERE workspace_id = '{ws_id}'"))
                # Delete webhook endpoints (table name is likely webhookendpoint)
                # await conn.execute(text(f"DELETE FROM webhookendpoint WHERE workspace_id = '{ws_id}'"))
            
            await conn.execute(text(f"DELETE FROM workspace WHERE owner_id = '{user_id}'"))
            
            # 5. Delete User
            print("Deleting user...")
            await conn.execute(text(f"DELETE FROM \"user\" WHERE id = '{user_id}'"))
            
            print("Cleanup successful.")
            
        except Exception as e:
            print(f"Error cleaning user: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_user())
