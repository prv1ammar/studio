import os
import json
import uuid
from typing import Dict, Any, List
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# System Prompt for the Copilot
SYSTEM_PROMPT = """
You are an expert AI Agent Architect for "Studio Tyboo".
Your task is to generate a functional JSON workflow graph based on a user's natural language request.

### Output Format
You must return a valid JSON object with the following structure:
{
  "nodes": [
    {
      "id": "node_1",
      "type": "agentNode",
      "position": { "x": 0, "y": 0 },
      "data": { 
        "id": "chatInput", 
        "label": "Chat Input",
        "inputs": [],
        "outputs": [{"name": "message", "type": "Text"}]
      }
    }
  ],
  "edges": [
    {
      "id": "e1-2",
      "source": "node_1",
      "target": "node_2"
    }
  ]
}

### Important: Node IDs
Each node MUST have a 'type' field set to "agentNode" EXACTLY.
The internal tool identifier (e.g., 'openaiModel', 'chatInput', 'mainAgent') MUST be placed inside 'data.id'.


### Available Nodes (Examples)
- **Input**: `{"type": "chatInput", "data": {"label": "Chat Input"}}`
- **LLM**: `{"type": "openaiModel", "data": {"label": "OpenAI Model"}}`
- **Output**: `{"type": "chatOutput", "data": {"label": "Chat Output"}}`
- **Prompt**: `{"type": "promptTemplate", "data": {"label": "Prompt Template"}}`
- **Knowledge Base**: `{"type": "faq", "data": {"label": "Knowledge"}}`
- **Vector Store**: `{"type": "supabaseStore", "data": {"label": "Supabase"}}`
- **Search**: `{"type": "WebSearch", "data": {"label": "Google Search"}}`
- **Notion**: `{"type": "NotionPageContent", "data": {"label": "Notion Reader"}}`

### Rules
1. Always start with a `chatInput` node.
2. Always end with a `chatOutput` node.
3. Connect nodes logically (Input -> Prompt -> LLM -> Output).
4. Lay out nodes horizontally (x: 0, x: 300, x: 600, etc.).
5. Response MUST be pure JSON, no markdown formatting.
"""

class CopilotAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if (OpenAI and self.api_key) else None

    def generate_flow(self, user_request: str) -> Dict[str, Any]:
        """
        Generates a flow graph from a user request.
        """
        if not self.client:
            return self._mock_response(user_request)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Or gpt-3.5-turbo if preferred
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Create a flow that: {user_request}"}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Copilot generation error: {e}")
            return self._mock_response(user_request)

    def _mock_response(self, user_request: str) -> Dict[str, Any]:
        """
        Fallback mock response if no API key or error.
        Generates a simple LLM chain.
        """
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        id3 = str(uuid.uuid4())
        id4 = str(uuid.uuid4())

        return {
            "nodes": [
                {
                    "id": id1,
                    "type": "agentNode",
                    "position": {"x": 50, "y": 200},
                    "data": {
                        "label": "Chat Input", 
                        "id": "chatInput",
                        "inputs": [],
                        "outputs": [{"name": "message", "type": "Text"}],
                        "icon": "MessageSquare",
                        "color": "#4f46e5"
                    }
                },
                {
                    "id": id2,
                    "type": "agentNode",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "Instruction", 
                        "id": "promptTemplate",
                        "inputs": [{"name": "variables", "type": "Any"}],
                        "outputs": [{"name": "prompt", "type": "Text"}],
                        "fields": [{"name": "template", "value": "Answer: {input}"}],
                        "icon": "PenTool",
                        "color": "#f59e0b"
                    }
                },
                {
                    "id": id3,
                    "type": "agentNode",
                    "position": {"x": 800, "y": 200},
                    "data": {
                        "label": "GPT-4 Processor", 
                        "id": "openaiModel",
                        "inputs": [{"name": "input", "type": "Text"}],
                        "outputs": [{"name": "response", "type": "Text"}],
                        "icon": "Cpu",
                        "color": "#10a37f"
                    }
                },
                {
                    "id": id4,
                    "type": "agentNode",
                    "position": {"x": 1200, "y": 200},
                    "data": {
                        "label": "Final Output", 
                        "id": "chatOutput",
                        "inputs": [{"name": "message", "type": "Text"}],
                        "outputs": [],
                        "icon": "LogOut",
                        "color": "#4f46e5"
                    }
                }
            ],

            "edges": [
                {"id": f"e{id1}-{id2}", "source": id1, "target": id2},
                {"id": f"e{id2}-{id3}", "source": id2, "target": id3},
                {"id": f"e{id3}-{id4}", "source": id3, "target": id4}
            ]
        }
