from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NodeData(BaseModel):
    id: Optional[str] = "unknown"
    label: Optional[str] = "Node"
    description: Optional[str] = None
    color: Optional[str] = None
    inputs: Optional[List[Any]] = []
    outputs: Optional[List[Any]] = []
    fields: Optional[List[Any]] = []
    
    # Allow ANY dynamic field without validation
    class Config:
        extra = "allow"

class WorkflowNode(BaseModel):
    id: str
    type: str
    data: NodeData
    position: Optional[Dict[str, Any]] = None
    class Config:
        extra = "allow"

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    class Config:
        extra = "allow"

class WorkflowGraph(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    class Config:
        extra = "allow"

class ExecutionRequest(BaseModel):
    message: str
    graph: WorkflowGraph
    class Config:
        extra = "allow"
