from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.core.credentials import cred_manager

class BaseNode(ABC):
    """
    Base class for all nodes in the Studio following a LangChain-style architecture.
    """
    node_id: str = "" # Unique identifier used for registration and graph mapping

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a config value with automatic fallback to environment variables.
        """
        val = self.config.get(key)
        if val is not None and val != "":
            return val
        
        import os
        env_val = os.getenv(key.upper())
        if env_val:
            return env_val
            
        return default

    def get_credential(self, key: str = "credentials_id") -> Optional[Dict[str, Any]]:
        """
        Retrieves the sensitive data associated with the credential ID provided in config.
        """
        cred_id = self.get_config(key)
        if not cred_id:
            return None
            
        cred_obj = cred_manager.get_credential(cred_id)
        if cred_obj:
            return cred_obj.get("data")
        return None

    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Main execution method for the node.
        :param input_data: Primary input (usually a string or dict).
        :param context: Optional dictionary containing graph data, global state, etc.
        """
        pass

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Optional method to return a LangChain object (LLM, Tool, Memory) 
        without full execution. Used for composition.
        """
        return None
