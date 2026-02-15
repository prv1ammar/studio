from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.nodes.factory import NODE_MAP
from app.nodes.registry import NodeRegistry
import importlib

router = APIRouter()

@router.get("/nodes")
async def list_node_reference():
    """
    Generates a dynamic documentation reference for all registered nodes.
    Scans both NODE_MAP and the Digital Registry.
    """
    reference = []
    
    # 1. Scan NODE_MAP (Legacy but explicit)
    for node_type, path in NODE_MAP.items():
        try:
            module_path, class_name = path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            node_class = getattr(module, class_name)
            
            reference.append({
                "id": node_type,
                "name": getattr(node_class, "name", node_type.replace("_", " ").title()),
                "category": getattr(node_class, "category", "General"),
                "version": getattr(node_class, "version", "1.0.0"),
                "description": node_class.__doc__.strip() if node_class.__doc__ else "No description available.",
                "inputs": getattr(node_class, "inputs", {}),
                "outputs": getattr(node_class, "outputs", {})
            })
        except:
            continue

    # 2. Filter duplicates (some nodes are in both registry and map)
    seen_ids = set()
    unique_ref = []
    for item in reference:
        if item["id"] not in seen_ids:
            unique_ref.append(item)
            seen_ids.add(item["id"])
            
    return unique_ref
