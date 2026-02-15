from typing import Any, Dict, Optional
from app.nodes.base import BaseNode
from app.nodes.factory import register_node
from pydantic import BaseModel, Field

class WebhookTriggerConfig(BaseModel):
    webhook_id: str = Field(..., description="The unique ID of the webhook endpoint in the Studio")
    http_method: str = Field(default="POST", description="Expected HTTP method (POST, GET)")
    response_mode: str = Field(default="immediate", description="How to respond to the caller (immediate, on_finish)")
    verification_type: Optional[str] = Field(default="generic", description="Security mode: generic, stripe, github, slack")
    secret: Optional[str] = Field(default=None, description="Signing secret for signature validation")

class WebhookTriggerInput(BaseModel):
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    query_params: Optional[Dict[str, Any]] = None

@register_node("webhook_trigger")
class WebhookTriggerNode(BaseNode):
    """
    Core Platform Trigger: Webhook.
    This node serves as the starting point for workflows triggered by external HTTP signals.
    """
    name = "Webhook Trigger"
    description = "React to external HTTP requests in real-time."
    category = "Triggers"
    node_type = "webhook_trigger"
    
    config_model = WebhookTriggerConfig
    input_model = WebhookTriggerInput

    async def execute(self, input_data: WebhookTriggerInput, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        The Webhook Trigger is unique: it mostly acts as a pass-through for 
        the data initially injected by the Webhook Gateway.
        """
        # Data is already in input_data from the Gateway
        return {
            "body": input_data.body,
            "headers": input_data.headers,
            "query_params": input_data.query_params,
            "received_at": context.get("received_at") if context else None
        }
