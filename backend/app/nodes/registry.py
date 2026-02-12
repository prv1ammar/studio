import importlib
import pkgutil
import inspect
import os
import sys
from typing import Dict, Type, Any, Optional, List
from .base import BaseNode

def register_node(node_id: str):
    """
    Decorator to explicitly register a node with a specific ID.
    """
    def decorator(cls):
        cls.node_id = node_id
        NodeRegistry._nodes[node_id] = cls
        return cls
    return decorator

class NodeRegistry:
    """
    Automated registry for nodes. Scans the app.nodes directory and 
    registers all classes inheriting from BaseNode.
    """
    _nodes: Dict[str, Type[BaseNode]] = {}
    _is_scanned = False

    @classmethod
    def scan_and_register(cls):
        """
        Scans the app.nodes package for classes inheriting from BaseNode.
        """
        if cls._is_scanned:
            return
        
        # Start scanning from the app.nodes directory
        # We need the parent of the current directory to scan the 'nodes' package
        nodes_dir = os.path.dirname(os.path.abspath(__file__))
        package_root = os.path.abspath(os.path.join(nodes_dir, "..", ".."))
        
        if package_root not in sys.path:
            sys.path.append(package_root)
        
        # Add agents directory for legacy agent imports
        agents_path = os.path.join(package_root, "app", "agents")
        if agents_path not in sys.path:
            sys.path.append(agents_path)

        # Scan all directories in nodes root
        module_count = 0
        for root, dirs, files in os.walk(nodes_dir):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py", "base.py", "registry.py"]:
                    # Optimization: Only import if the file looks like a Node
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Now also scan for legacy Components
                            if not any(x in content for x in ["BaseNode", "@register_node", "Component", "LCModelComponent"]):
                                continue
                    except Exception as e:
                        print(f"NodeRegistry Error reading {file}: {e}")
                        continue

                    # Convert file path to module path
                    rel_path = os.path.relpath(file_path, package_root)
                    module_name = rel_path.replace(os.sep, ".").replace(".py", "")
                    
                    try:
                        module = importlib.import_module(module_name)
                        module_count += 1
                        cls._extract_nodes_from_module(module)
                    except (ImportError, ModuleNotFoundError) as e:
                        # Common for legacy components with niche dependencies
                        pass
                    except Exception as e:
                        # print(f"NodeRegistry Warning: Error loading {module_name}: {e}")
                        pass

        cls._is_scanned = True
        print(f"NodeRegistry: Scanned {module_count} modules. Registered {len(cls._nodes)} nodes.")

    @classmethod
    def _extract_nodes_from_module(cls, module):
        import inspect
        from .base import LangflowComponentAdapter
        count = 0
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__name__ in ["BaseNode", "Component", "LCModelComponent", "LangflowComponentAdapter"]:
                continue
            
            # Use MRO to check for BaseNode OR Component inheritance
            try:
                mro_names = [base.__name__ for base in inspect.getmro(obj)]
                
                # 1. Native BaseNode
                if "BaseNode" in mro_names:
                    node_id = getattr(obj, "node_id", None) or obj.__name__
                    if node_id not in cls._nodes:
                        cls._nodes[node_id] = obj
                        count += 1
                        
                # 2. Legacy Component (Langflow/LFX)
                elif any(x in mro_names for x in ["Component", "LCModelComponent"]):
                    # We wrap the legacy component class in our adapter
                    # We use the class name or display_name as the ID
                    node_id = getattr(obj, "name", None) or getattr(obj, "display_name", obj.__name__)
                    
                    if node_id not in cls._nodes:
                        # Create a factory that returns an instance of the adapter for THIS specific class
                        # Because our system expects a class that can be instantiated with config
                        class DynamicAdapter(LangflowComponentAdapter):
                            def __init__(self, config=None):
                                super().__init__(obj, config)
                        
                        DynamicAdapter.__name__ = f"Adapter_{obj.__name__}"
                        cls._nodes[node_id] = DynamicAdapter
                        count += 1
                        
            except Exception:
                continue
        return count

    @classmethod
    def get_node_class(cls, node_type: str) -> Optional[Type[BaseNode]]:
        if not cls._is_scanned:
            cls.scan_and_register()
        return cls._nodes.get(node_type)

    @classmethod
    def bulk_register(cls, node_ids: List[str], node_class: Type[BaseNode]):
        """Registers multiple IDs for the same class."""
        for nid in node_ids:
            cls._nodes[nid] = node_class

    @classmethod
    def get_all_nodes(cls) -> Dict[str, Type[BaseNode]]:
        if not cls._is_scanned:
            cls.scan_and_register()
        return cls._nodes
