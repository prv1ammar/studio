import json

LIBRARY_PATH = "backend/data/node_library.json"

def fix_missing_types():
    """Add missing type definitions to input ports."""
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Define fixes for missing types
    fixes = {
        "AI Services & Agents": {
            "realEstateScraperNode": {
                "url": ["Text", "Data"]
            },
            "notificationNode": {
                "message": ["Text", "Message", "Data"]
            }
        },
        "Logic & Flow": {
            "flow_controls_ConditionalRouter": {
                "input_text": ["Text", "Data", "Message"]
            }
        },
        "Productivity": {
            "github_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "pipedrive_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "wordpress_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "mailchimp_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "telegram_node": {
                "message": ["Text", "Message", "Data"]
            },
            "salesforce_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "hubspot_node": {
                "input_data": ["Text", "Data", "Object"]
            },
            "gmail_send_message": {
                "message": ["Text", "Message", "Data"]
            },
            "notion_page_creator": {
                "title": ["Text", "Data"]
            },
            "discord_node": {
                "message": ["Text", "Message", "Data"]
            },
            "slack_send_message": {
                "message": ["Text", "Message", "Data"]
            },
            "google_sheets_writer": {
                "data_to_write": ["Data", "Object", "Array", "Text"]
            },
            "google_sheets_reader": {
                "input_range": ["Text", "Data"]
            }
        },
        "Search & Scraping": {
            "google_BigQueryExecutorComponent": {
                "query": ["Text", "Data"]
            },
            "gmailNode": {
                "input_data": ["Text", "Data", "Object"]
            }
        }
    }
    
    fixed_count = 0
    
    for category, nodes_fixes in fixes.items():
        if category not in data:
            print(f"⚠️  Category '{category}' not found")
            continue
            
        for node_id, input_fixes in nodes_fixes.items():
            # Find the node
            node = None
            for n in data[category]:
                if n.get("id") == node_id:
                    node = n
                    break
            
            if not node:
                print(f"⚠️  Node '{node_id}' not found in category '{category}'")
                continue
            
            # Fix inputs
            for input_obj in node.get("inputs", []):
                input_name = input_obj.get("name")
                if input_name in input_fixes:
                    if "types" not in input_obj:
                        input_obj["types"] = input_fixes[input_name]
                        fixed_count += 1
                        print(f"✓ Fixed {category}/{node_id}/input/{input_name}")
    
    # Save the fixed library
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fixed {fixed_count} missing type definitions. Library saved.")

if __name__ == "__main__":
    fix_missing_types()
