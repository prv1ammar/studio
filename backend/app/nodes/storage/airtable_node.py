import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class AirtableConfig(NodeConfig):
    base_id: str = Field(..., description="The ID of the Airtable Base")
    table_name: str = Field(..., description="The name or ID of the Table")
    credentials_id: Optional[str] = Field(None, description="Airtable Personal Access Token ID")

@register_node("airtable_reader")
class AirtableReaderNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        base_id = self.get_config("base_id")
        table_name = self.get_config("table_name")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("api_key") if creds_data else None
        
        if not token:
            return {"error": "Airtable Access Token is required."}
            
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status >= 400:
                    text = await response.text()
                    return {"error": f"Airtable Error {response.status}: {text}"}
                return await response.json()

@register_node("airtable_writer")
class AirtableWriterNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        base_id = self.get_config("base_id")
        table_name = self.get_config("table_name")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("api_key") if creds_data else None
        
        if not token:
            return {"error": "Airtable Access Token is required."}
            
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Format records for Airtable API
        # Airtable expects {"records": [{"fields": {...}}]}
        records = []
        if isinstance(input_data, list):
            for item in input_data:
                fields = item if isinstance(item, dict) else {"content": str(item)}
                records.append({"fields": fields})
        else:
            fields = input_data if isinstance(input_data, dict) else {"content": str(input_data)}
            records.append({"fields": fields})

        payload = {"records": records[:10]} # Airtable limit is 10 per batch

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status >= 400:
                    text = await response.text()
                    return {"error": f"Airtable Error {response.status}: {text}"}
                return await response.json()
