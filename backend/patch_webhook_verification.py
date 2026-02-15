import asyncio
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from sqlalchemy import text
from app.db.session import engine

async def patch_webhook_verification():
    async with engine.begin() as conn:
        print("Starting Database Path: Adding verification_type to WebhookEndpoint...")
        try:
            # Check if column exists
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='webhookendpoint' AND column_name='verification_type'"))
            if not result.fetchone():
                await conn.execute(text("ALTER TABLE webhookendpoint ADD COLUMN verification_type VARCHAR DEFAULT 'generic'"))
                print("SUCCESS: Added verification_type column to webhookendpoint table.")
            else:
                print("INFO: verification_type column already exists.")
        except Exception as e:
            print(f"ERROR patching database: {e}")

if __name__ == "__main__":
    asyncio.run(patch_webhook_verification())
