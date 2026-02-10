import sys
import os
from typing import Dict, Any, List, Optional
import traceback
from app.nodes.factory import NodeFactory

# Root path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Backend path to support 'app.' imports
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Agents directory for legacy/utility support
agents_dir = os.path.join(project_root, "backend", "app", "agents")
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

from app.nodes.factory import NodeFactory
from app.core.validator import validator
from app.core.credentials import cred_manager

class AgentEngine:
    """
    Modular Agent Engine for the Automation Studio.
    Supports Graph Validation, Execution Context, and Resilience.
    """
    
    def __init__(self):
        self.node_factory = NodeFactory()

    async def execute_node(self, node_type: str, input_text: Any, config: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Any:
        """
        Loads and executes a node with Resilience (Retry logic).
        """
        node = self.node_factory.get_node(node_type, config)
        if not node:
             return {"error": f"Node type '{node_type}' not found."}
        
        # Resilience: Retry Logic
        max_retries = int(config.get("retry_count", 0)) if config else 0
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Add current attempt to context
                if context: context["attempt"] = attempt
                
                result = await node.execute(input_text, context)
                
                # If result is a dict with an 'error' key, we might want to retry
                if isinstance(result, dict) and "error" in result and attempt < max_retries:
                    last_error = result["error"]
                    print(f"🔄 Retrying node {node_type} (Attempt {attempt+1}/{max_retries}) due to internal error: {last_error}")
                    continue
                
                return result
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    print(f"🔄 Retrying node {node_type} (Attempt {attempt+1}/{max_retries}) due to exception: {last_error}")
                    continue
                
                print(f"❌ Node Execution Failed ({node_type}) after {attempt+1} attempts: {last_error}")
                return {"error": last_error}

    async def process_workflow(self, graph_data: Dict[str, Any], message: str, broadcaster=None) -> str:
        """
        Core workflow execution engine with Validation and Structured Context.
        """
        # 1. GRAPH VALIDATION
        is_valid, errors = validator.validate(graph_data)
        if not is_valid:
            error_msg = " | ".join(errors)
            if broadcaster: await broadcaster("error", "validation_failed", {"message": error_msg})
            return f"Validation Failed: {error_msg}"

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # 2. SEED EXECUTION CONTEXT
        execution_context = {
            "variables": {"initial_query": message},
            "node_outputs": {},
            "graph_metadata": {"node_count": len(nodes)},
            "engine": self
        }

        # 3. Identify Entry Point (Support 'chatInput')
        current_node = next((n for n in nodes if n.get('data', {}).get('id') == 'chatInput'), nodes[0])
        
        current_input = message
        visited = set()
        
        # Safety: Path limit
        for _ in range(50):
            node_id = current_node['id']
            if node_id in visited: break
            visited.add(node_id)
            
            node_data = current_node.get('data', {})
            reg_id = node_data.get('id')
            
            # Update Context for current hop
            execution_context["current_node_id"] = node_id
            
            # Broadcast node start
            if broadcaster: await broadcaster("node_start", node_id)
            
            # --- EXECUTE ---
            if reg_id == 'chatInput':
                result = current_input
            else:
                result = await self.execute_node(reg_id, current_input, config=node_data, context=execution_context)

            # Store in output history
            execution_context["node_outputs"][node_id] = result
            
            # Broadcast node completion
            if broadcaster: await broadcaster("node_end", node_id, {"output": str(result)[:200]})
            
            # Handle Critical Failures (unless 'continue_on_fail' is set)
            if isinstance(result, dict) and "error" in result:
                if not node_data.get("continue_on_fail"):
                    return f"Stopped at {node_data.get('label')}: {result['error']}"

            # --- TRAVERSAL ---
            # Determine next node based on handle matching or sequential edge
            next_edge = None
            
            # Priority: Handle-based routing (Success/Error/Data)
            if isinstance(result, dict):
                # Try to find an edge matching the key in results (e.g. 'success' port)
                available_ports = [k for k in result.keys()]
                next_edge = next((e for e in edges if e['source'] == node_id and e.get('sourceHandle') in available_ports), None)

            # Fallback: First sequential edge
            if not next_edge:
                next_edge = next((e for e in edges if e['source'] == node_id), None)

            if not next_edge: break
            
            next_node_id = next_edge['target']
            s_handle = next_edge.get('sourceHandle')
            t_handle = next_edge.get('targetHandle') or "input"

            # Prepare Input for Next Node
            if s_handle and isinstance(result, dict) and s_handle in result:
                current_input = result[s_handle]
            else:
                current_input = result

            current_node = next((n for n in nodes if n['id'] == next_node_id), None)
            if not current_node: break
            
        return str(result)
            
        return str(result)

# Instantiate and export the engine
engine = AgentEngine()

# Add registry property for compatibility with main.py
# (It expects engine.registry to exist)
from app.nodes.factory import NODE_MAP
engine.registry = NODE_MAP
