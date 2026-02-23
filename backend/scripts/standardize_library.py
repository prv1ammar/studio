import json
import os

def standardize_library():
    path = os.path.join("backend", "data", "node_library.json")
    with open(path, "r", encoding="utf-8") as f:
        lib = json.load(f)
        
    if "Native Integrations" not in lib:
        lib["Native Integrations"] = []
        
    # Define the missing core native nodes
    missing_natives = [
        {
            "id": "slack_node",
            "name": "Slack (Native)",
            "label": "Slack",
            "description": "Direct Slack integration for messages and channel management.",
            "category": "Native Integrations",
            "icon": "MessageSquare",
            "color": "#4a154b",
            "inputs": [
                {"name": "slack_auth", "display_name": "Slack Connection", "type": "credential", "required": True},
                {"name": "action", "display_name": "Action", "type": "select", "options": ["send_message", "read_history", "list_users"], "default": "send_message"},
                {"name": "channel_id", "display_name": "Channel ID", "type": "text", "required": True},
                {"name": "message_text", "display_name": "Message", "type": "textarea", "required": False}
            ],
            "outputs": [{"name": "data", "display_name": "Response", "types": ["Object"]}]
        },
        {
            "id": "gmail_node",
            "name": "Gmail (Native)",
            "label": "Gmail",
            "description": "Direct Gmail integration for sending and reading emails.",
            "category": "Native Integrations",
            "icon": "Mail",
            "color": "#ea4335",
            "inputs": [
                {"name": "google_oauth", "display_name": "Google Connection", "type": "credential", "required": True},
                {"name": "action", "display_name": "Action", "type": "select", "options": ["send_email", "read_emails", "create_draft"], "default": "send_email"},
                {"name": "recipient", "display_name": "To", "type": "text", "required": False},
                {"name": "subject", "display_name": "Subject", "type": "text", "required": False},
                {"name": "body", "display_name": "Message Body", "type": "textarea", "required": False}
            ],
            "outputs": [{"name": "data", "display_name": "Response", "types": ["Object"]}]
        },
        {
            "id": "notion_node",
            "name": "Notion (Native)",
            "label": "Notion",
            "description": "Direct Notion integration for pages and databases.",
            "category": "Native Integrations",
            "icon": "Box",
            "color": "#000000",
            "inputs": [
                {"name": "notion_auth", "display_name": "Notion Connection", "type": "credential", "required": True},
                {"name": "action", "display_name": "Action", "type": "select", "options": ["query_database", "create_page", "append_content", "search", "get_page"], "default": "query_database"},
                {"name": "target_id", "display_name": "Page/DB ID", "type": "text", "required": True}
            ],
            "outputs": [{"name": "data", "display_name": "Response", "types": ["Object"]}]
        },
        {
            "id": "telegram_action",
            "name": "Telegram (Native)",
            "label": "Telegram",
            "description": "Direct Telegram integration for bot messages.",
            "category": "Native Integrations",
            "icon": "Send",
            "color": "#0088cc",
            "inputs": [
                {"name": "telegram_auth", "display_name": "Telegram Bot Connection", "type": "credential", "required": True},
                {"name": "chat_id", "display_name": "Chat ID / @username", "type": "text", "required": True},
                {"name": "text", "display_name": "Message Text", "type": "textarea", "required": False}
            ],
            "outputs": [{"name": "data", "display_name": "Response", "types": ["Object"]}]
        }
    ]
    
    seen_ids = {n["id"] for n in lib["Native Integrations"]}
    for node in missing_natives:
        if node["id"] not in seen_ids:
            lib["Native Integrations"].append(node)
            seen_ids.add(node["id"])
            print(f"Restored {node['id']} to library.")

    # Cleanup: If old versions exist in other categories, we can keep them for backward compatibility
    # but the user said they "disappeared", so they probably want the new ones.
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)
        
    print("Standardization complete.")

if __name__ == "__main__":
    standardize_library()
