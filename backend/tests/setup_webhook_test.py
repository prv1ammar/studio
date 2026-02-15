import asyncio
from app.db.session import async_session
from app.db.models import Workflow, Workspace, User
from sqlmodel import select
import json

async def setup_test_webhook_workflow():
    async with async_session() as session:
        # Get a workspace or create one
        result = await session.execute(select(Workspace).limit(1))
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            print("No workspace found. Please run the app and create one first.")
            return

        definition = {
            "nodes": [
                {
                    "id": "node_webhook",
                    "type": "agentNode",
                    "data": {
                        "id": "webhook_trigger",
                        "label": "Test Webhook",
                        "webhook_id": "test-webhook-123",
                        "category": "Triggers"
                    }
                },
                {
                    "id": "node_log",
                    "type": "agentNode",
                    "data": {
                        "id": "chatOutput",
                        "label": "Log Output",
                        "category": "AI Services & Agents"
                    }
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "node_webhook",
                    "sourceHandle": "body",
                    "target": "node_log",
                    "targetHandle": "output_message"
                }
            ]
        }

        new_wf = Workflow(
            name="Test Webhook Workflow",
            description="Testing the incoming webhook gateway",
            workspace_id=workspace.id,
            definition=definition
        )
        
        session.add(new_wf)
        await session.commit()
        print(f"Created Test Workflow with ID: {new_wf.id}")
        print(f"Webhook ID: test-webhook-123")

if __name__ == "__main__":
    asyncio.run(setup_test_webhook_workflow())
