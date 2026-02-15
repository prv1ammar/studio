import importlib.util
import sys
import types
from typing import Optional, Type, Dict, Any
from sqlmodel import select
from app.db.session import async_session
from app.db.models import PrivateNode
from .base import BaseNode

class PrivateRegistry:
    """
    Dynamic Registry for Custom Enterprise Nodes.
    Compiles Python code from the database into live Node classes.
    """
    _cache: Dict[str, Type[BaseNode]] = {}

    @classmethod
    async def get_node_class(cls, node_type: str, workspace_id: Optional[str] = None) -> Optional[Type[BaseNode]]:
        """
        Retrieves a custom node class from the DB and compiles it if not cached.
        """
        # 1. Check Cache
        cache_key = f"{workspace_id}:{node_type}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # 2. Fetch from DB
        async with async_session() as db:
            query = select(PrivateNode).where(PrivateNode.node_type == node_type)
            if workspace_id:
                query = query.where(PrivateNode.workspace_id == workspace_id)
            
            result = await db.execute(query)
            private_node = result.scalar_one_or_none()

            if not private_node or not private_node.enabled:
                return None

            # 3. Dynamic Compilation
            try:
                # Create a virtual module
                module_name = f"app.nodes.private.{node_type}"
                module = types.ModuleType(module_name)
                module.__file__ = f"<private_node:{node_type}>"
                
                # Execute the code in the module's namespace
                # We provide BaseNode and register_node to the namespace
                from .factory import register_node
                namespace = {
                    "BaseNode": BaseNode,
                    "register_node": register_node,
                    "__name__": module_name
                }
                
                exec(private_node.code, namespace)
                
                # Update module __dict__
                module.__dict__.update(namespace)
                sys.modules[module_name] = module

                # Find the class that inherits from BaseNode
                for name, attr in namespace.items():
                    if isinstance(attr, type) and issubclass(attr, BaseNode) and attr is not BaseNode:
                        cls._cache[cache_key] = attr
                        return attr

                print(f" PrivateRegistry Error: No BaseNode subclass found in private node '{node_type}'")
                return None

            except Exception as e:
                print(f" PrivateRegistry Compilation Error for '{node_type}': {e}")
                import traceback
                traceback.print_exc()
                return None

    @classmethod
    def invalidate_cache(cls, node_type: str, workspace_id: str):
        cache_key = f"{workspace_id}:{node_type}"
        if cache_key in cls._cache:
            del cls._cache[cache_key]
