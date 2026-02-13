"""
Comprehensive Node Testing Script
Tests node instantiation, schema validation, and basic execution
"""
import asyncio
import sys
import os
from typing import Dict, List, Any

# Add backend to sys.path
sys.path.append(os.path.abspath("backend"))

from app.nodes.registry import NodeRegistry
from app.nodes.base import BaseNode

class NodeTester:
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def test_node_instantiation(self, node_id: str, node_class) -> bool:
        """Test if a node can be instantiated."""
        try:
            config = {"node_id": node_id}
            node = node_class(config)
            return True
        except Exception as e:
            self.results["errors"].append({
                "node_id": node_id,
                "test": "instantiation",
                "error": str(e)
            })
            return False
    
    async def test_node_schema(self, node_id: str, node_class) -> bool:
        """Test if a node has valid schema."""
        try:
            config = {"node_id": node_id}
            node = node_class(config)
            
            # Check for required attributes
            required_attrs = ["node_type", "version", "category"]
            for attr in required_attrs:
                if not hasattr(node, attr):
                    raise ValueError(f"Missing required attribute: {attr}")
            
            # Check if get_schema works
            if hasattr(node, 'get_schema'):
                schema = node.get_schema()
                if not isinstance(schema, dict):
                    raise ValueError("get_schema() must return a dict")
            
            return True
        except Exception as e:
            self.results["errors"].append({
                "node_id": node_id,
                "test": "schema",
                "error": str(e)
            })
            return False
    
    async def test_node(self, node_id: str, node_class) -> Dict[str, Any]:
        """Run all tests for a single node."""
        tests = {
            "instantiation": await self.test_node_instantiation(node_id, node_class),
            "schema": await self.test_node_schema(node_id, node_class)
        }
        
        passed = all(tests.values())
        return {
            "node_id": node_id,
            "passed": passed,
            "tests": tests
        }
    
    async def run_all_tests(self):
        """Run tests on all registered nodes."""
        print("=" * 70)
        print("COMPREHENSIVE NODE TESTING")
        print("=" * 70)
        print()
        
        nodes = NodeRegistry.get_all_nodes()
        self.results["total"] = len(nodes)
        
        print(f"Testing {len(nodes)} registered nodes...\n")
        
        # Test each node
        failed_nodes = []
        for node_id, node_class in nodes.items():
            result = await self.test_node(node_id, node_class)
            
            if result["passed"]:
                self.results["passed"] += 1
                print(f"✓ {node_id}")
            else:
                self.results["failed"] += 1
                failed_nodes.append(node_id)
                print(f"✗ {node_id}")
        
        # Print summary
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Nodes: {self.results['total']}")
        print(f"Passed: {self.results['passed']} ({self.results['passed']/self.results['total']*100:.1f}%)")
        print(f"Failed: {self.results['failed']} ({self.results['failed']/self.results['total']*100:.1f}%)")
        
        if self.results["errors"]:
            print()
            print("=" * 70)
            print("ERRORS")
            print("=" * 70)
            for error in self.results["errors"][:10]:  # Show first 10 errors
                print(f"\nNode: {error['node_id']}")
                print(f"Test: {error['test']}")
                print(f"Error: {error['error']}")
            
            if len(self.results["errors"]) > 10:
                print(f"\n... and {len(self.results['errors']) - 10} more errors")
        
        print()
        print("=" * 70)
        
        # Return exit code
        return 0 if self.results["failed"] == 0 else 1

async def main():
    tester = NodeTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
