from typing import Dict, Any, List, Tuple

class GraphValidator:
    """
    Validates a Studio Workflow Graph before saving or execution.
    Prevents common user errors and architectural flaws.
    """

    @staticmethod
    def validate(graph_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Runs a suite of checks on the graph.
        :return: (is_valid, list_of_errors)
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        errors = []

        if not nodes:
            return False, ["Workflow graph is empty. Add at least one node."]

        # 1. Start Node Check
        # Every workflow must have a starting point (Trigger or Input)
        trigger_nodes = [n for n in nodes if n.get('data', {}).get('category') in ['Triggers', 'AI Services & Agents', 'Input/Output']]
        chat_inputs = [n for n in nodes if n.get('data', {}).get('id') == 'chatInput']
        
        if not chat_inputs and not trigger_nodes:
            errors.append("Validation Error: No entry point found. Add a 'Chat Input' or a 'Trigger' node.")

        # 2. Infinite Loop Check (Cycle Detection)
        if GraphValidator._has_cycles(nodes, edges):
            errors.append("Architecture Error: Infinite loop detected in the graph flow.")

        # 3. Dangling Internal Nodes
        # Non-trigger nodes should usually have at least one input edge
        internal_nodes = [n for n in nodes if n.get('data', {}).get('id') != 'chatInput']
        for node in internal_nodes:
            node_id = node['id']
            has_input = any(e for e in edges if e['target'] == node_id)
            if not has_input:
                # Warning instead of error? Let's keep it as error for strict mode.
                errors.append(f"Logic Warning: Node '{node.get('data', {}).get('label')}' is not connected to any input.")

        # 4. Required Config Check (Basic)
        for node in nodes:
            node_data = node.get('data', {})
            # This would require checking node_library.json for 'required: true' fields
            # For now, we skip but note it for Phase 2.
            pass

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
