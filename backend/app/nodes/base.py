from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
import time
from pydantic import BaseModel, ValidationError
from app.core.credentials import cred_manager

class NodeConfig(BaseModel):
    """Base Pydantic model for node configuration."""
    pass

class BaseNode(ABC):
    """
    Base class for all nodes in the Studio.
    Provides standardized configuration, credential management, and performance tracking.
    """
    node_id: str = "" 
    config_model: Optional[Type[BaseModel]] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.raw_config = config or {}
        self.config = self._validate_config(self.raw_config)
        self.metrics = {
            "execution_time": 0.0,
            "success": False,
            "error": None
        }

    def _validate_config(self, config: Dict[str, Any]) -> Any:
        """Parses config into a Pydantic model if config_model is defined."""
        if self.config_model:
            try:
                return self.config_model(**config)
            except ValidationError as e:
                # Log error or handle it
                print(f"⚠️ Validation error for {self.node_id}: {e}")
        return config

    def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieves a config value with fallback to environment variables."""
        # Check Pydantic model first
        if isinstance(self.config, BaseModel):
            val = getattr(self.config, key, None)
        else:
            val = self.config.get(key)
            
        if val is not None and val != "":
            return val
        
        import os
        env_val = os.getenv(key.upper())
        if env_val:
            return env_val
            
        return default

    async def get_credential(self, key: str = "credentials_id") -> Optional[Dict[str, Any]]:
        """Retrieves sensitive data associated with the credential ID."""
        cred_id = self.get_config(key)
        if not cred_id:
            return None
            
        cred_obj = await cred_manager.get_credential(cred_id)
        if cred_obj:
            return cred_obj.get("data")
        return None

    async def run(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Standardized execution wrapper that tracks metrics.
        """
        start_time = time.time()
        try:
            result = await self.execute(input_data, context)
            self.metrics["success"] = True
            return result
        except Exception as e:
            self.metrics["success"] = False
            self.metrics["error"] = str(e)
            raise e
        finally:
            self.metrics["execution_time"] = time.time() - start_time

    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Actual logic implementation for the node."""
        pass

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None

class LangflowComponentAdapter(BaseNode):
    """
    Adapter to run legacy Langflow/LFX Component classes within the Studio ecosystem.
    """
    def __init__(self, component_class: Type[Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.component_class = component_class
        # Extract metadata from legacy class
        self.display_name = getattr(component_class, "display_name", component_class.__name__)
        self.description = getattr(component_class, "description", "")
        self.icon = getattr(component_class, "icon", "Box")
        self.node_id = getattr(component_class, "node_id", component_class.__name__)

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Prepare initialization parameters from config
        # Map our config to the component's expected inputs
        init_params = {}
        if isinstance(self.config, dict):
            init_params.update(self.config)
        
        # 2. Instantiate the legacy component
        try:
            instance = self.component_class(**init_params)
        except Exception as e:
            return {"error": f"Failed to initialize component {self.node_id}: {str(e)}"}

        # 3. Handle execution logic based on component type
        # Check for common Langflow/LFX execution methods
        try:
            if hasattr(instance, "run_model") and callable(instance.run_model):
                # Many integration components use run_model
                result = instance.run_model()
                # If it returns a list of Data objects, serialize them
                if isinstance(result, list):
                    return [item.data if hasattr(item, "data") else item for item in result]
                return result
            
            elif hasattr(instance, "build_model") and callable(instance.build_model):
                # Model components (LLMs, Embeddings) use build_model
                return instance.build_model()
            
            elif hasattr(instance, "run") and callable(instance.run):
                # Generic component run method
                import asyncio
                if asyncio.iscoroutinefunction(instance.run):
                    return await instance.run()
                return instance.run()
            
            return {"error": f"Component {self.node_id} has no supported execution method (run_model/build_model/run)."}
        except Exception as e:
            return {"error": f"Execution failed in {self.node_id}: {str(e)}"}
