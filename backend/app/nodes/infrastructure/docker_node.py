"""
Docker Infrastructure Node - Studio Standard
Batch 45: DevOps & Infrastructure
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("docker_node")
class DockerNode(BaseNode):
    """
    Manage Docker containers and images.
    Requires the 'docker' python package.
    """
    node_type = "docker_node"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = [] # Usually local or env-based

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_containers",
            "options": [
                "list_containers", 
                "start_container", 
                "stop_container", 
                "list_images",
                "pull_image"
            ],
            "description": "Action to perform on Docker"
        },
        "target_id": {
            "type": "string",
            "optional": True,
            "description": "Container ID or Image Name"
        },
        "all_containers": {
            "type": "boolean",
            "default": False,
            "description": "Show all containers (even stopped ones)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import docker
        except ImportError:
            return {"status": "error", "error": "Docker library not installed. Run: pip install docker"}

        try:
            client = docker.from_env()
            action = self.get_config("action", "list_containers")
            target_id = self.get_config("target_id") or (input_data if isinstance(input_data, str) else None)
            
            result_data = None
            
            if action == "list_containers":
                show_all = self.get_config("all_containers", False)
                containers = client.containers.list(all=show_all)
                result_data = [
                    {
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": str(c.image),
                        "ports": c.ports
                    } for c in containers
                ]

            elif action == "start_container":
                if not target_id:
                    return {"status": "error", "error": "Container ID is required to start."}
                container = client.containers.get(target_id)
                container.start()
                result_data = {"id": container.short_id, "status": "started"}

            elif action == "stop_container":
                if not target_id:
                    return {"status": "error", "error": "Container ID is required to stop."}
                container = client.containers.get(target_id)
                container.stop()
                result_data = {"id": container.short_id, "status": "stopped"}

            elif action == "list_images":
                images = client.images.list()
                result_data = [
                    {
                        "id": img.short_id,
                        "tags": img.tags,
                        "size": img.attrs.get("Size")
                    } for img in images
                ]

            elif action == "pull_image":
                if not target_id:
                    return {"status": "error", "error": "Image name (target_id) is required to pull."}
                image = client.images.pull(target_id)
                result_data = {"id": image.short_id, "tags": image.tags}

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": {
                    "result": result_data,
                    "count": len(result_data) if isinstance(result_data, list) else 1
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Docker Node Failed: {str(e)}"}
