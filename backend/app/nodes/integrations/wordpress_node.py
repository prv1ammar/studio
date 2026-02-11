import aiohttp
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import base64

class WordPressConfig(NodeConfig):
    base_url: Optional[str] = Field(None, description="WordPress Site URL (e.g. https://example.com)")
    username: Optional[str] = Field(None, description="WP Username")
    app_password: Optional[str] = Field(None, description="WP Application Password")
    credentials_id: Optional[str] = Field(None, description="WordPress Credentials ID")
    post_status: str = Field("publish", description="Default status for new posts (publish, draft, private)")

@register_node("wordpress_node")
class WordPressNode(BaseNode):
    node_id = "wordpress_node"
    config_model = WordPressConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        base_url = creds.get("base_url") if creds else self.get_config("base_url")
        username = creds.get("username") if creds else self.get_config("username")
        app_password = creds.get("app_password") if creds else self.get_config("app_password")

        if not base_url or not username or not app_password:
            return {"error": "WordPress URL, Username, and Application Password are required."}

        # Format URL
        base_url = base_url.rstrip('/')
        api_url = f"{base_url}/wp-json/wp/v2/posts"

        # Auth Header (Basic Auth with Application Password)
        auth_string = f"{username}:{app_password}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "Content-Type": "application/json"
        }

        # 2. Payload Preparation
        payload = {
            "title": "New Studio Automation Post",
            "content": str(input_data),
            "status": self.get_config("post_status")
        }

        if isinstance(input_data, dict):
            payload["title"] = input_data.get("title", payload["title"])
            payload["content"] = input_data.get("content", payload["content"])
            payload["status"] = input_data.get("status", payload["status"])

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, headers=headers) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                        return {"error": f"WordPress API Error: {result.get('message')}", "code": result.get('code')}
                    return {
                        "status": "success",
                        "post_id": result.get("id"),
                        "link": result.get("link")
                    }
        except Exception as e:
            return {"error": f"WordPress Node Failed: {str(e)}"}
