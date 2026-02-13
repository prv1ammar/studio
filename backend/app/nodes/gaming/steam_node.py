"""
Steam Node - Studio Standard
Batch 76: Gaming & Meta
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("steam_node")
class SteamNode(BaseNode):
    """
    Access player statistics and game data via the Steam Web API.
    """
    node_type = "steam_node"
    version = "1.0.0"
    category = "gaming"
    credentials_required = ["steam_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_player_summary",
            "options": ["get_player_summary", "list_games", "get_achievements", "search_user"],
            "description": "Steam action"
        },
        "steam_id": {
            "type": "string",
            "optional": True,
            "description": "64-bit Steam community ID"
        },
        "app_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the game/app"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("steam_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Steam Web API Key is required."}

            base_url = "https://api.steampowered.com"
            action = self.get_config("action", "get_player_summary")

            async with aiohttp.ClientSession() as session:
                if action == "get_player_summary":
                    s_id = self.get_config("steam_id") or str(input_data)
                    url = f"{base_url}/ISteamUser/GetPlayerSummaries/v0002/"
                    params = {"key": api_key, "steamids": s_id}
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        players = res_data.get("response", {}).get("players", [])
                        return {"status": "success", "data": {"result": players[0] if players else {}}}

                elif action == "list_games":
                    s_id = self.get_config("steam_id") or str(input_data)
                    url = f"{base_url}/IPlayerService/GetOwnedGames/v0001/"
                    params = {"key": api_key, "steamid": s_id, "format": "json", "include_appinfo": "true"}
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("response", {})}}

                elif action == "get_achievements":
                    s_id = self.get_config("steam_id")
                    a_id = self.get_config("app_id") or str(input_data)
                    url = f"{base_url}/ISteamUserStats/GetPlayerAchievements/v0001/"
                    params = {"key": api_key, "steamid": s_id, "appid": a_id}
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("playerstats", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Steam Node Failed: {str(e)}"}
