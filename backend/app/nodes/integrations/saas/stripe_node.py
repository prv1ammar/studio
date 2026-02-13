"""
Stripe Integration Node - Studio Standard
Batch 44: SaaS Integrations
"""
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("stripe_node")
class StripeNode(BaseNode):
    """
    Integrates with Stripe for payments and customer management.
    Supports: Create Customer, Create Payment Intent, List Charges.
    """
    node_type = "stripe_node"
    version = "1.1.0"
    category = "saas"
    credentials_required = ["stripe_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_customer",
            "options": ["create_customer", "create_payment_intent", "list_charges"],
            "description": "Stripe action to perform"
        },
        "payload": {
            "type": "json",
            "description": "Data for the action (e.g., {'email': 'user@example.com'})"
        }
    }

    outputs = {
        "result": {"type": "object"},
        "id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import stripe
        except ImportError:
            return {"status": "error", "error": "stripe library not installed. Run: pip install stripe"}

        try:
            # 1. Resolve Credentials
            creds = await self.get_credential("stripe_auth")
            api_key = None
            if creds:
                api_key = creds.get("api_key") or creds.get("secret_key")
            
            if not api_key:
                api_key = self.get_config("api_key")
                
            if not api_key:
                return {"status": "error", "error": "Stripe API Key is required."}

            stripe.api_key = api_key
            action = self.get_config("action", "create_customer")
            
            # Prepare Payload
            params = self.get_config("payload", {})
            if isinstance(input_data, dict):
                params.update(input_data)
            elif isinstance(input_data, str) and input_data:
                if action == "create_customer":
                    params["email"] = input_data
                elif action == "list_charges":
                    try:
                        params["limit"] = int(input_data)
                    except:
                        pass

            result_data = {}

            if action == "create_customer":
                customer = stripe.Customer.create(**params)
                result_data = customer.to_dict()
                result_data["id"] = customer.id

            elif action == "create_payment_intent":
                if "amount" not in params or "currency" not in params:
                     return {"status": "error", "error": "Amount and currency are required for payment intents."}
                
                intent = stripe.PaymentIntent.create(**params)
                result_data = intent.to_dict()
                result_data["id"] = intent.id

            elif action == "list_charges":
                limit = params.get("limit", 10)
                charges = stripe.Charge.list(limit=limit)
                result_data = {
                    "charges": [c.to_dict() for c in charges.data],
                    "total_count": len(charges.data),
                    "has_more": charges.has_more
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except stripe.error.StripeError as e:
            return {"status": "error", "error": f"Stripe API Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"Stripe execution failed: {str(e)}"}
