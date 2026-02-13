"""
Kubernetes Node - Studio Standard
Batch 83: Observability & SRE
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("kubernetes_node")
class KubernetesNode(BaseNode):
    """
    Orchestrate Kubernetes clusters, pods, and services via the K8s REST API.
    """
    node_type = "kubernetes_node"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["kubernetes_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_pods",
            "options": ["list_pods", "get_pod_logs", "list_services", "list_deployments", "patch_deployment"],
            "description": "Kubernetes action"
        },
        "namespace": {
            "type": "string",
            "default": "default",
            "description": "Target namespace"
        },
        "name": {
            "type": "string",
            "optional": True,
            "description": "Name of the resource (pod, deployment, etc.)"
        },
        "api_server": {
            "type": "string",
            "required": True,
            "description": "K8s API Server URL (e.g., https://1.2.3.4)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("kubernetes_auth")
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "Kubernetes Service Account Token is required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            api_server = self.get_config("api_server").rstrip("/")
            namespace = self.get_config("namespace", "default")
            action = self.get_config("action", "list_pods")

            # Disable SSL verification for internal k8s clusters if requested (config-based)
            connector = aiohttp.TCPConnector(ssl=False) if self.get_config("insecure", False) else None
            
            async with aiohttp.ClientSession(connector=connector) as session:
                if action == "list_pods":
                    url = f"{api_server}/api/v1/namespaces/{namespace}/pods"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "get_pod_logs":
                    pod_name = self.get_config("name") or str(input_data)
                    url = f"{api_server}/api/v1/namespaces/{namespace}/pods/{pod_name}/log"
                    async with session.get(url, headers=headers) as resp:
                        res_text = await resp.text()
                        return {"status": "success", "data": {"result": res_text}}

                elif action == "list_deployments":
                    url = f"{api_server}/apis/apps/v1/namespaces/{namespace}/deployments"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Kubernetes Node Failed: {str(e)}"}
