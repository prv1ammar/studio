import stripe
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("stripe_action")
class StripeNode(BaseNode):
    """Integrates with Stripe for payments and customer management."""
    node_type = "stripe_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["stripe_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'create_customer',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'JSON payload for Stripe request',
        },
    ]
    inputs = {
        "action": {"type": "string", "enum": ["create_customer", "create_payment_intent", "list_charges"], "default": "create_customer"},
        "data": {"type": "any", "description": "JSON payload for Stripe request"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Auth Retrieval
        creds = await self.get_credential("stripe_auth")
        api_key = creds.get("api_key") or creds.get("secret_key") if creds else self.get_config("api_key")

        if not api_key:
            return {"status": "error", "error": "Stripe API Key is required.", "data": None}

        stripe.api_key = api_key
        action = self.get_config("action", "create_customer")

        try:
            if action == "create_customer":
                # input_data should be a dict with email, name, etc.
                params = input_data if isinstance(input_data, dict) else {"email": str(input_data)}
                customer = stripe.Customer.create(**params)
                return {
                    "status": "success",
                    "data": customer.to_dict()
                }

            elif action == "create_payment_intent":
                # input_data should have amount and currency
                params = input_data if isinstance(input_data, dict) else {}
                if "amount" not in params or "currency" not in params:
                     return {"status": "error", "error": "Amount and currency are required for payment intents.", "data": None}
                
                intent = stripe.PaymentIntent.create(**params)
                return {
                    "status": "success",
                    "data": intent.to_dict()
                }

            elif action == "list_charges":
                limit = input_data if isinstance(input_data, int) else 10
                charges = stripe.Charge.list(limit=limit)
                return {
                    "status": "success",
                    "data": {
                        "charges": [c.to_dict() for c in charges.data],
                        "has_more": charges.has_more
                    }
                }

            return {"status": "error", "error": f"Unsupported Stripe action: {action}", "data": None}

        except stripe.error.StripeError as e:
            return {"status": "error", "error": f"Stripe API Error: {str(e)}", "data": None}
        except Exception as e:
            return {"status": "error", "error": f"Stripe Node Failed: {str(e)}", "data": None}