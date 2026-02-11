import json

print("=== FIXING EDGE CASES ===\n")

# Load the node library
with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    lib = json.load(f)

# Fix nodes with no inputs (these are typically source nodes)
edge_case_fixes = []

for category, nodes in lib.items():
    for node in nodes:
        node_id = node.get('id', 'UNKNOWN')
        
        # chatInput - Source node, no inputs needed, but should have proper output
        if node_id == 'chatInput':
            if not node.get('outputs'):
                node['outputs'] = [
                    {
                        "name": "message",
                        "display_name": "User Message",
                        "types": ["Message", "Text"]
                    }
                ]
                edge_case_fixes.append(f"Added output to {category}/{node_id}")
        
        # data_source_MockDataGenerator - Data generator, no inputs needed
        if node_id == 'data_source_MockDataGenerator':
            if not node.get('inputs'):
                node['inputs'] = [
                    {
                        "name": "num_rows",
                        "display_name": "Number of Rows",
                        "type": "number",
                        "required": False,
                        "default": 10,
                        "description": "Number of mock data rows to generate"
                    }
                ]
                edge_case_fixes.append(f"Added input to {category}/{node_id}")
        
        # datastax_AssistantsListAssistants - List operation, no inputs needed
        if node_id == 'datastax_AssistantsListAssistants':
            if not node.get('inputs'):
                node['inputs'] = [
                    {
                        "name": "limit",
                        "display_name": "Limit",
                        "type": "number",
                        "required": False,
                        "default": 100,
                        "description": "Maximum number of assistants to list"
                    }
                ]
                edge_case_fixes.append(f"Added input to {category}/{node_id}")
        
        # chatOutput - Sink node, no outputs needed, but should have proper input
        if node_id == 'chatOutput':
            if not node.get('inputs'):
                node['inputs'] = [
                    {
                        "name": "message",
                        "display_name": "Message to Display",
                        "type": "handle",
                        "required": True,
                        "types": ["Message", "Text", "Data"],
                        "description": "The message to display to the user"
                    }
                ]
                edge_case_fixes.append(f"Added input to {category}/{node_id}")
        
        # flow_controls_RunFlow - Action node, triggers a flow
        if node_id == 'flow_controls_RunFlow':
            if not node.get('outputs'):
                node['outputs'] = [
                    {
                        "name": "status",
                        "display_name": "Execution Status",
                        "types": ["Text", "Data"]
                    }
                ]
                edge_case_fixes.append(f"Added output to {category}/{node_id}")
        
        # llm_operations_SmartRouter - Router node
        if node_id == 'llm_operations_SmartRouter':
            if not node.get('outputs'):
                node['outputs'] = [
                    {
                        "name": "routed_output",
                        "display_name": "Routed Output",
                        "types": ["Message", "Text"]
                    }
                ]
                edge_case_fixes.append(f"Added output to {category}/{node_id}")

# Save the fixed library
with open('backend/data/node_library.json', 'w', encoding='utf-8') as f:
    json.dump(lib, f, indent=2, ensure_ascii=False)

print(f"Edge case fixes applied: {len(edge_case_fixes)}")
for fix in edge_case_fixes:
    print(f"  - {fix}")

print(f"\nUpdated node library saved.")
