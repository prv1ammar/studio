import os
import sys

# Get absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
sys.path.append(project_root)

from backend.engine import engine
import asyncio

async def test_chain():
    print("--- TESTING MULTI-NODE CHAIN ---")
    
    # Mock Graph: Input -> Orchestrator -> FAQ -> Output
    graph = {
        "nodes": [
            {"id": "input-1", "type": "agentNode", "data": {"id": "chatInput", "label": "User Input"}},
            {"id": "agent-1", "type": "orchestrator_node", "data": {"id": "orchestrator", "label": "Router"}},
            {"id": "agent-2", "type": "faq_node", "data": {"id": "faq", "label": "Knowledge Specialist"}},
            {"id": "output-1", "type": "agentNode", "data": {"id": "chatOutput", "label": "Final Response"}}
        ],
        "edges": [
            {"id": "e1", "source": "input-1", "target": "agent-1"}, # Input to Router
            {"id": "e2", "source": "agent-1", "target": "agent-2"}, # Router to FAQ
            {"id": "e3", "source": "agent-2", "target": "output-1"} # FAQ to Output
        ]
    }
    
    test_message = "What are the clinic hours?"
    print(f"User: {test_message}")
    
    response = await engine.process_workflow(graph, test_message)
    print(f"\nFinal Engine Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_chain())
