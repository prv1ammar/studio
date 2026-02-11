import pytest
import asyncio
from backend.app.core.engine import AgentEngine
from backend.app.nodes.base import BaseNode
from typing import Any, Dict, Optional

class MockSuccessNode(BaseNode):
    node_id = "mockSuccess"
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        return f"Processed: {input_data}"

class MockSplitterNode(BaseNode):
    node_id = "mockSplitter"
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        return {"a": "left", "b": "right"}

@pytest.mark.asyncio
async def test_simple_sequential_workflow():
    engine = AgentEngine()
    
    # Overwrite factory for testing
    from backend.app.nodes.factory import NodeFactory
    test_factory = NodeFactory()
    test_factory.get_node = lambda n_type, config=None: MockSuccessNode(config) if n_type == "mockSuccess" else None
    engine.node_factory = test_factory
    
    graph = {
        "nodes": [
            {"id": "n1", "data": {"id": "chatInput", "label": "Start"}},
            {"id": "n2", "data": {"id": "mockSuccess", "label": "Processor"}}
        ],
        "edges": [
            {"source": "n1", "target": "n2"}
        ]
    }
    
    result = await engine.process_workflow(graph, "hello")
    assert "Processed: hello" in result

@pytest.mark.asyncio
async def test_branching_workflow():
    engine = AgentEngine()
    
    from backend.app.nodes.factory import NodeFactory
    test_factory = NodeFactory()
    def get_test_node(n_type, config=None):
        if n_type == "mockSplitter": return MockSplitterNode(config)
        if n_type == "mockSuccess": return MockSuccessNode(config)
        return None
        
    test_factory.get_node = get_test_node
    engine.node_factory = test_factory
    
    graph = {
        "nodes": [
            {"id": "n1", "data": {"id": "chatInput"}},
            {"id": "n2", "data": {"id": "mockSplitter"}},
            {"id": "n3", "data": {"id": "mockSuccess", "label": "Path A"}}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3", "sourceHandle": "b"}
        ]
    }
    
    result = await engine.process_workflow(graph, "trigger")
    # Path B ('b' handle) returns 'right'
    assert "Processed: right" in result

if __name__ == "__main__":
    asyncio.run(test_simple_sequential_workflow())
    asyncio.run(test_branching_workflow())
    print("✅ All engine integration tests passed!")
