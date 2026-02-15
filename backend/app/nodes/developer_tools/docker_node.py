"""
Docker Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("docker_node")
class DockerNode(BaseNode):
    """
    Docker integration for container management.
    """
    node_type = "docker_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["docker_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_containers",
            "options": ["list_containers", "inspect_container", "start_container", "stop_container"],
            "description": "Docker action"
        },
        "container_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("docker_auth")
            docker_host = creds.get("docker_host", "http://localhost:2375") # Usually socket or tcp
            
            if not docker_host:
                return {"status": "error", "error": "Docker Host URL required"}

            action = self.get_config("action", "list_containers")

            # Assuming exposing Docker API over HTTP/TCP for simple management or socket proxy
            # Direct socket access via aiohttp requires UnixConnector (linux) or named pipe (windows).
            # Simplified for TCP HTTP access.
            
            async with aiohttp.ClientSession() as session:
                if action == "list_containers":
                    url = f"{docker_host}/containers/json"
                    async with session.get(url) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Docker API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "inspect_container":
                    container_id = self.get_config("container_id")
                    if not container_id: return {"status": "error", "error": "container_id required"}
                    
                    url = f"{docker_host}/containers/{container_id}/json"
                    async with session.get(url) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "start_container":
                    container_id = self.get_config("container_id")
                    if not container_id: return {"status": "error", "error": "container_id required"}
                    
                    url = f"{docker_host}/containers/{container_id}/start"
                    async with session.post(url) as resp:
                         if resp.status not in [204, 304]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Docker Start Error {resp.status}: {error_text}"}
                         return {"status": "success", "data": {"result": f"Container {container_id} started"}}

                elif action == "stop_container":
                    container_id = self.get_config("container_id")
                    if not container_id: return {"status": "error", "error": "container_id required"}
                    
                    url = f"{docker_host}/containers/{container_id}/stop"
                    async with session.post(url) as resp:
                         return {"status": "success", "data": {"result": f"Container {container_id} stopped"}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Docker Node Failed: {str(e)}"}
