import sys
import os
import argparse
import asyncio
import json
from typing import Any, Dict

# Setup path so we can import 'app'
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(backend_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Now we can import our engine components
try:
    from app.nodes.factory import NodeFactory
    from app.nodes.base import NodeSchema, BaseNode
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)

async def test_node(node_type: str, input_data: Any = None, config: Dict[str, Any] = None):
    print(f"\n[TEST] Testing Node: {node_type}")
    print("-" * 50)

    # 1. Instantiate Node
    factory = NodeFactory()
    node = factory.get_node(node_type, config or {})
    
    if not node:
        print(f"[-] Error: Node type '{node_type}' not found in registry.")
        return

    print(f"[+] Node Instantiated: {node.__class__.__name__}")

    # 2. Validate Schema (Node Law check)
    print("\n[SCHEMA] Phase 2: Node Law Compliance")
    try:
        schema = node.get_schema()
        print(f"  - Node Type: {schema.node_type}")
        print(f"  - Version: {schema.version}")
        print(f"  - Category: {schema.category}")
        
        if schema.version == "0.0.0" or schema.category == "legacy":
            print("  ! WARNING: Node is in Legacy Mode (Compliance Failure)")
        else:
            print("  + Schema Validated")
            
        print(f"  - Required Credentials: {schema.credentials_required}")
    except Exception as e:
        print(f"  - Schema Validation Failed: {str(e)}")

    # 3. Execution Check
    print("\n[EXEC] Phase 5: Structured Execution")
    try:
        # Mock Context
        context = {
            "execution_id": "test-execution-123",
            "user_id": "test-user",
            "variables": {}
        }
        
        # Use a real string if input_data is not provided
        test_input = input_data if input_data is not None else "Hello, node test!"
        
        print(f"  - Input Trace: {str(test_input)[:100]}...")
        
        # Run node
        result = await node.run(test_input, context)
        
        # Check Structured Output
        print("\n[RESULT] Result Payload:")
        print(format_json(result))
        
        if isinstance(result, dict) and "status" in result:
            status = result.get("status")
            if status == "success":
                print("\n[DONE] Execution COMPLETE (Structured Output: COMPLIANT)")
            elif status == "error":
                print(f"\n[DONE] Execution RETURNED ERROR (Structured Output: COMPLIANT)")
                print(f"   Error: {result.get('error')}")
            else:
                print(f"\n[?] Unknown Status Format: {status}")
        else:
            print("\n[!] WARNING: Output is NOT structured (Compliance Failure)")
            print("   Expected: {'status': 'success|error', 'data': ..., 'error': ...}")
            
    except Exception as e:
        print(f"\n[CRASH] Execution CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automation Studio - Node Test Harness")
    parser.add_argument("--node", required=True, help="Registry ID of the node to test")
    parser.add_argument("--input", default=None, help="Input data (string or JSON)")
    parser.add_argument("--config", default="{}", help="Config as JSON string")
    
    args = parser.parse_args()
    
    # Parse input and config
    try:
        test_input = json.loads(args.input) if args.input and (args.input.startswith('{') or args.input.startswith('[')) else args.input
        config = json.loads(args.config)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        sys.exit(1)
        
    asyncio.run(test_node(args.node, test_input, config))
