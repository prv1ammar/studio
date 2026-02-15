import sys
import os
import asyncio
import uuid
from datetime import datetime

# Add project root and backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import async_session
from app.db.models import Template, User
from sqlmodel import select

async def seed_templates():
    async with async_session() as db:
        # 1. Get an admin user to be the author
        res = await db.execute(select(User).where(User.role == "admin"))
        admin = res.scalar_one_or_none()
        
        if not admin:
            # Fallback to any user
            res = await db.execute(select(User).limit(1))
            admin = res.scalar_one_or_none()
            
        if not admin:
            print("Error: No users found in database. Please register a user first.")
            return

        templates_to_seed = [
            {
                "name": "RAG Chatbot (PDF Focus)",
                "description": "A pre-configured Retrieval-Augmented Generation pipeline. Upload a PDF, index it into a vector store, and chat with it.",
                "category": "AI Services",
                "tags": ["RAG", "LLM", "Memory"],
                "definition": {
                   "nodes": [
                       {"id": "1", "type": "chat_input", "data": {"label": "User Query"}},
                       {"id": "2", "type": "pdf_node", "data": {"label": "Knowledge Base"}},
                       {"id": "3", "type": "llm_node", "data": {"label": "AI Analyst", "prompt": "Answer based on context: {context}"}}
                   ],
                   "edges": [
                       {"id": "e1-3", "source": "1", "target": "3"},
                       {"id": "e2-3", "source": "2", "target": "3", "sourceHandle": "data"}
                   ]
                }
            },
            {
                "name": "E-commerce Support Bot",
                "description": "Automate customer support for Shopify/WooCommerce. Handles order tracking and FAQ.",
                "category": "Customer Support",
                "tags": ["Support", "Automation", "Shopify"],
                "definition": {
                   "nodes": [
                       {"id": "1", "type": "webhook_node", "data": {"label": "Customer Query"}},
                       {"id": "2", "type": "api_node", "data": {"label": "Order Lookup", "url": "https://api.shopify.com/v1/orders"}},
                       {"id": "3", "type": "ai_agent", "data": {"label": "Support Agent"}}
                   ],
                   "edges": [
                       {"id": "e1-2", "source": "1", "target": "2"},
                       {"id": "e2-3", "source": "2", "target": "3"}
                   ]
                }
            },
            {
                "name": "Social Media Auto-Poster",
                "description": "Takes a text prompt, generates an image, and posts it to Twitter/X and LinkedIn.",
                "category": "Marketing",
                "tags": ["Social Media", "DALL-E", "Automation"],
                "definition": {
                   "nodes": [
                       {"id": "1", "type": "scheduler", "data": {"cron": "0 9 * * *"}},
                       {"id": "2", "type": "llm_node", "data": {"label": "Content Creator"}},
                       {"id": "3", "type": "image_node", "data": {"label": "Image Gen"}},
                       {"id": "4", "type": "twitter_node", "data": {"label": "Post to X"}}
                   ],
                   "edges": [
                       {"id": "e1-2", "source": "1", "target": "2"},
                       {"id": "e2-3", "source": "2", "target": "3"},
                       {"id": "e3-4", "source": "3", "target": "4"}
                   ]
                }
            }
        ]

        for t_data in templates_to_seed:
            # Check if exists
            res = await db.execute(select(Template).where(Template.name == t_data["name"]))
            existing = res.scalar_one_or_none()
            
            if not existing:
                template = Template(
                    name=t_data["name"],
                    description=t_data["description"],
                    category=t_data["category"],
                    tags=t_data["tags"],
                    definition=t_data["definition"],
                    author_id=admin.id,
                    is_public=True
                )
                db.add(template)
                print(f"Adding template: {t_data['name']}")
        
        await db.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_templates())
