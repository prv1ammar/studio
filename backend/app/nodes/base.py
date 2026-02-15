from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, List, Tuple
import time
from pydantic import BaseModel, ValidationError, Field
from app.core.credentials import cred_manager

# Phase 2: Node Law - Mandatory Schema
class NodeSchema(BaseModel):
    node_type: str
    version: str = "1.0.0"
    category: str  # trigger, action, logic, ai
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    credentials_required: List[str] = Field(default_factory=list)
    deprecated: bool = False

class NodeConfig(BaseModel):
    """Base Pydantic model for node configuration."""
    pass

class BaseNode(ABC):
    """
    Base class for all nodes in the Studio.
    Provides standardized configuration, credential management, and performance tracking.
    """
    # Metadata required by "Node Law"
    node_type: str = ""
    version: str = "1.0.0"
    category: str = "custom"
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    credentials_required: List[str] = []
    deprecated: bool = False

    node_id: str = "" 
    config_model: Optional[Type[BaseModel]] = None
    input_model: Optional[Type[BaseModel]] = None
    output_model: Optional[Type[BaseModel]] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.raw_config = config.copy() if config else {}
        self.config = self._validate_config(self.raw_config)
        self.metrics = {
            "execution_time": 0.0,
            "success": False,
            "error": None,
            "input_size": 0,
            "output_size": 0,
            "logs": []
        }

    def log(self, message: str):
        """Appends a timestamped log trace to the execution metrics."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.metrics["logs"].append(f"[{timestamp}] {message}")
        # Also print to stdout for real-time worker monitoring
        print(f"[{self.node_type}] {message}")

    def get_schema(self) -> NodeSchema:
        """Returns the node's schema in compliance with 'Node Law'."""
        try:
            return NodeSchema(
                node_type=self.node_type or self.__class__.__name__,
                version=self.version,
                category=self.category,
                inputs=self.inputs,
                outputs=self.outputs,
                credentials_required=self.credentials_required,
                deprecated=self.deprecated
            )
        except ValidationError:
            # Fallback for legacy components during migration
            return NodeSchema(
                node_type=self.node_id or self.__class__.__name__,
                version="0.0.0",
                category="legacy",
                inputs={},
                outputs={},
                credentials_required=[],
                deprecated=True
            )

    def _validate_config(self, config: Dict[str, Any]) -> Any:
        """Parses config into a Pydantic model if config_model is defined."""
        if self.config_model:
            try:
                return self.config_model(**config)
            except ValidationError as e:
                # Log error or handle it
                print(f" Validation error for config in {self.node_type}: {e}")
        return config

    def _validate_inputs(self, input_data: Any) -> Any:
        """Validates inputs against input_model if defined, or basic schema check."""
        if self.input_model:
            try:
                # Handle cases where input_data might be a single value instead of a dict
                if not isinstance(input_data, dict):
                    # Try to find the first required field or 'input' field to map it
                    # For now, let's assume it should be a dict if a model is provided
                    pass
                return self.input_model(**input_data)
            except ValidationError as e:
                raise ValueError(f"Input validation failed for {self.node_type}: {str(e)}")
        
        # Basic check for required fields in the 'inputs' dictionary
        if isinstance(input_data, dict):
            for name, spec in self.inputs.items():
                if spec.get("required") and name not in input_data:
                    # Check if it's in config as a fallback
                    if not self.get_config(name):
                        raise ValueError(f"Missing required input: '{name}' for node {self.node_type}")
        
        return input_data

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

    async def validate_credentials(self):
        """
        Comprehensive pre-flight check for credentials.
        Verifies existence, DB presence, and decryption capability.
        """
        for cred_key in self.credentials_required:
            cred_id = self.get_config(cred_key)
            if not cred_id:
                # If not in config directly, check for 'creds_id' or 'credentials_id' generic fallback
                cred_id = self.get_config("credentials_id") or self.get_config("creds_id")
                
            if not cred_id:
                raise ValueError(f"Auth Error: Missing required credential '{cred_key}' for node '{self.node_type}'. Connect a credential in the settings.")
            
            # Verify DB presence and decryption
            cred_data = await self.get_credential(cred_key)
            if not cred_data:
                # Fallback to checking by common keys if the key itself isn't the cred_id
                cred_data = await cred_manager.get_credential(cred_id)
                
            if not cred_data:
                raise ValueError(f"Auth Error: Credential '{cred_id}' not found or decryption failed for node '{self.node_type}'.")
            
            # Node-specific type check could happen here if we had service types
            pass

    async def check_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Optional node-specific method to ping the service.
        Returns (is_connected, error_message).
        """
        return True, None

    async def run(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Standardized execution wrapper that tracks metrics and validates pre-conditions.
        """
        start_time = time.time()
        self.metrics["input_size"] = len(str(input_data))
        try:
            # 1. PRE-FLIGHT AUTH VALIDATION
            await self.validate_credentials()

            # 2. Validate Inputs
            validated_input = self._validate_inputs(input_data)

            # 3. Execute actual node logic
            result = await self.execute(validated_input, context)
            
            # 4. Success tracking
            self.metrics["success"] = True
            self.metrics["output_size"] = len(str(result))
            
            # 5. Output Validation (Optional)
            if self.output_model:
                try:
                    self.output_model(**result)
                except ValidationError as e:
                    print(f" Output validation warning for {self.node_type}: {e}")

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
