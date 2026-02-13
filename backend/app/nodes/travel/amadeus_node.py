"""
Amadeus Node - Studio Standard
Batch 72: Travel & Hospitality
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("amadeus_node")
class AmadeusNode(BaseNode):
    """
    Automate flight and hotel discovery via the Amadeus Self-Service API.
    """
    node_type = "amadeus_node"
    version = "1.0.0"
    category = "travel"
    credentials_required = ["amadeus_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_flights",
            "options": ["search_flights", "search_hotels", "list_locations", "get_status"],
            "description": "Amadeus action"
        },
        "origin": {
            "type": "string",
            "optional": True,
            "description": "IATA code (e.g. NYC, LON)"
        },
        "destination": {
            "type": "string",
            "optional": True
        },
        "departure_date": {
            "type": "string",
            "optional": True,
            "description": "YYYY-MM-DD"
        },
        "city_code": {
            "type": "string",
            "optional": True,
            "description": "City IATA code for hotel search"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("amadeus_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_secret = creds.get("api_secret") if creds else self.get_config("api_secret")
            
            if not api_key or not api_secret:
                return {"status": "error", "error": "Amadeus API Key and Secret are required."}

            async with aiohttp.ClientSession() as session:
                # 1. Get Access Token
                auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
                auth_data = {
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret
                }
                async with session.post(auth_url, data=auth_data) as auth_resp:
                    auth_json = await auth_resp.json()
                    access_token = auth_json.get("access_token")
                
                if not access_token:
                    return {"status": "error", "error": "Failed to retrieve Amadeus access token."}

                headers = {"Authorization": f"Bearer {access_token}"}
                base_url = "https://test.api.amadeus.com/v2" # Using test environment
                action = self.get_config("action", "search_flights")

                if action == "search_flights":
                    url = f"{base_url}/shopping/flight-offers"
                    params = {
                        "originLocationCode": self.get_config("origin") or "NYC",
                        "destinationLocationCode": self.get_config("destination") or "LON",
                        "departureDate": self.get_config("departure_date") or "2024-12-01",
                        "adults": 1
                    }
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "search_hotels":
                    # Note: Hotel search usually uses V1 or specific V3 endpoints
                    url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
                    params = {"cityCode": self.get_config("city_code") or "PAR"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Amadeus Node Failed: {str(e)}"}
