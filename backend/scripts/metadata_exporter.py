import json
import logging
from langflow.interface.types import get_all_types_dict
from langflow.base.constants import NODE_TYPE_MAP

def export_langflow_metadata():
    """
    Extracts the full component library from Langflow internals.
    This includes all LLMs, Agents, Tools, Chains, and their schema.
    """
    try:
        # get_all_types_dict returns categories with their components and fields
        metadata = get_all_types_dict()
        
        # Add custom category for the user's specific agents
        metadata["Specialized Agents"] = {
            "FAQAgent": {
                "display_name": "Clinic FAQ Agent",
                "description": "Specialized in medical clinic FAQs.",
                "template": {
                    "system_prompt": {"type": "str", "multiline": True, "value": "You are a clinic assistant."},
                    "model_name": {"type": "str", "options": ["gpt-4o", "gpt-4o-mini"], "value": "gpt-4o-mini"}
                }
            },
            "BookingAgent": {
                "display_name": "Appointment Booking",
                "description": "Handles clinic bookings and schedules.",
                "template": {
                    "api_key": {"type": "str", "password": True},
                    "table_id": {"type": "str"}
                }
            }
        }
        
        with open("backend/langflow_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        print("Successfully exported Langflow metadata to backend/langflow_metadata.json")
    except Exception as e:
        print(f"Error exporting metadata: {e}")

if __name__ == "__main__":
    export_langflow_metadata()
