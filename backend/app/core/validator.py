from typing import Dict, Any, List, Tuple
from app.nodes.registry import NodeRegistry

class GraphValidator:
    """
    Validates a Studio Workflow Graph before saving or execution.
    Prevents common user errors and architectural flaws.
    """

    def __init__(self):
        # We'll trigger a registry scan once when the validator is used
        pass

    def validate(self, graph_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Runs a suite of checks on the graph.
        :return: (is_valid, list_of_errors)
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        errors = []

        if not nodes:
            return False, ["Workflow graph is empty. Add at least one node."]

        # Ensure Registry is scanned
        NodeRegistry.scan_and_register()

        # 1. Trigger Check (Multiple Triggers)
        # V1 Constraint: Exactly one entry point
        triggers = []
        for node in nodes:
            node_type = node.get("data", {}).get("id")
            # Triggers are chatInput, webhook_trigger, or nodes in the Trigger category
            if node_type in ["chatInput", "webhook_trigger"] or node.get("data", {}).get("category") == "Triggers":
                triggers.append(node.get("data", {}).get("label", node_type))

        if not triggers:
            errors.append("Validation Error: No entry point found. Add a 'Chat Input' or a 'Trigger' node.")
        elif len(triggers) > 1:
            errors.append(f"Validation Error: Multiple entry points found ({', '.join(triggers)}). V1 only supports one trigger per workflow.")

        # 2. Infinite Loop Check (Cycle Detection)
        if self._has_cycles(nodes, edges):
            errors.append("Architecture Error: Infinite loop detected in the graph flow.")

        # 3. Node-Level Validation (Required Fields & Credentials)
        for node in nodes:
            node_id = node.get("id")
            node_data = node.get("data", {})
            node_type = node_data.get("id")
            node_label = node_data.get("label", node_id)
            
            # Skip validation for non-standard nodes
            if not node_type:
                continue

            cls = NodeRegistry.get_node_class(node_type)
            if not cls:
                # If we can't find the class, we skip strict validation 
                # (might be a legacy component handled by adapter)
                continue

            # a) Credentials Validation
            required_creds = getattr(cls, "credentials_required", [])
            node_creds = node_data.get("credentials", {})
            for cred_type in required_creds:
                # Check for direct key or a linked credential ID
                if not node_creds.get(cred_type) and not node_data.get(cred_type) and not node_data.get(f"{cred_type}_id"):
                    # Some nodes use 'api_key' or similar directly
                    if not node_data.get("api_key") and not node_data.get("apiKey"):
                        errors.append(f"Node '{node_label}': Missing required {cred_type} credentials.")

            # b) Required Inputs / Config Validation
            # Support both dict and model based inputs
            inputs_schema = getattr(cls, "inputs", {})
            for input_name, spec in inputs_schema.items():
                if isinstance(spec, dict) and spec.get("required"):
                    val = node_data.get(input_name)
                    # Check if it's connected as a handle
                    is_connected = any(e for e in edges if e["target"] == node_id and e.get("targetHandle") == input_name)
                    
                    if not val and not is_connected and spec.get("default") is None:
                        errors.append(f"Node '{node_label}': Missing required parameter '{input_name}'.")

        # 4. Dangling Internal Nodes
        for node in nodes:
            node_id = node['id']
            node_type = node.get('data', {}).get('id', '')
            
            # Skip entry points
            if node_type in ["chatInput", "webhook_trigger"] or node.get("data", {}).get("category") == "Triggers":
                continue
                
            has_input = any(e for e in edges if e['target'] == node_id)
            if not has_input:
                errors.append(f"Logic Warning: Node '{node.get('data', {}).get('label')}' is not connected to any input.")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def _has_cycles(nodes: List[Dict], edges: List[Dict]) -> bool:
        """Simple DFS to detect cycles in a directed graph."""
        adj = {n['id']: [] for n in nodes}
        for e in edges:
            if e['source'] in adj:
                adj[e['source']].append(e['target'])

        visited = set()
        path = set()

        def visit(u):
            if u in path: return True
            if u in visited: return False
            visited.add(u)
            path.add(u)
            for v in adj.get(u, []):
                if visit(v): return True
            path.remove(u)
            return False

        return any(visit(n['id']) for n in nodes)

validator = GraphValidator()

