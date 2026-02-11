import stripe
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class StripeConfig(NodeConfig):
    api_key: Optional[str] = Field(None, description="Stripe Secret API Key")
    credentials_id: Optional[str] = Field(None, description="Stripe Credentials ID")
    action: str = Field("create_customer", description="Action (create_customer, create_payment_intent, list_charges)")

@register_node("stripe_node")
class StripeNode(BaseNode):
    node_id = "stripe_node"
    config_model = StripeConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")

        if not api_key:
            return {"error": "Stripe API Key is required."}

        stripe.api_key = api_key
        action = self.get_config("action")

        try:
            if action == "create_customer":
                # input_data should be a dict with email, name, etc.
                params = input_data if isinstance(input_data, dict) else {"email": str(input_data)}
                customer = stripe.Customer.create(**params)
                return customer.to_dict()

            elif action == "create_payment_intent":
                # input_data should have amount and currency
                params = input_data if isinstance(input_data, dict) else {}
                if "amount" not in params or "currency" not in params:
                     return {"error": "Amount and currency are required for payment intents."}
                
                intent = stripe.PaymentIntent.create(**params)
                return intent.to_dict()

            elif action == "list_charges":
                limit = input_data if isinstance(input_data, int) else 10
                charges = stripe.Charge.list(limit=limit)
                return [c.to_dict() for c in charges.data]

            return {"error": f"Unsupported Stripe action: {action}"}

        except stripe.error.StripeError as e:
            return {"error": f"Stripe API Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Stripe Node Failed: {str(e)}"}
