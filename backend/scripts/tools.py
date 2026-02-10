from typing import Any, Dict, List, Callable
from agent_booking.tools import (
    create_booking_tool, 
    get_booking_tool, 
    update_booking_tool, 
    cancel_booking_tool,
    list_bookings_tool
)
from agent_FAQ.agent_FAQ.tools import retrieve_faq_context

class ToolRegistry:
    """
    Central hub for registering and retrieving tools that can be injected into agents.
    Mirrors the 'Tools' library in Langflow.
    """
    
    def __init__(self):
        # Preset tools based on existing agent capabilities
        self._tools: Dict[str, Callable] = {
            "create_booking": create_booking_tool,
            "get_booking": get_booking_tool,
            "update_booking": update_booking_tool,
            "cancel_booking": cancel_booking_tool,
            "list_bookings": list_bookings_tool,
            "retrieve_faq": retrieve_faq_context,
        }
        
        # Add External Integrations
        self._register_external_tools()

    def _register_external_tools(self):
        """Placeholders for Phase 4 external integrations."""
        
        def web_search(query: str) -> str:
            """Simple placeholder for Web Search integration."""
            return f"Searched the web for: {query}. (Tavily/Google Search integration pending API key)"
            
        def supabase_db(action: str, table: str, data: Dict[str, Any] = None) -> str:
            """Simple placeholder for Supabase integration."""
            return f"Database {action} on {table} performed successfully."

        self._tools["web_search"] = web_search
        self._tools["supabase_db"] = supabase_db

    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)

    def get_all_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_tools_by_names(self, names: List[str]) -> List[Callable]:
        return [self._tools[n] for n in names if n in self._tools]

# Singleton registry
tool_registry = ToolRegistry()
