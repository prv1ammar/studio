# 🛠️ Tutorial: How to Build a Resilient Node

This guide explains how to create a new node for the Studio Automation Platform using the standardized Phase 1 architecture.

---

## 1. The Standard Node Structure
Every node must inherit from `BaseNode` and implement the `execute` method.

```python
from app.nodes.base import BaseNode, NodeConfig
from pydantic import Field
from typing import Any, Dict, Optional

# 1. Define your Configuration Schema
class MyNodeConfig(NodeConfig):
    api_key: str = Field(..., description="API Key for the service")
    timeout: int = Field(30, description="Request timeout")

# 2. Implement the Node
class MyCustomNode(BaseNode):
    node_id = "my_custom_node"
    config_model = MyNodeConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Access validated config
        api_key = self.get_config("api_key")
        
        # Access credentials (if encrypted)
        # creds = self.get_credential("cred_id")
        
        # Your Logic Here
        result = f"Hello {input_data} with key {api_key}"
        
        return result
```

---

## 2. Key Features You Get Automatically

### 🔒 Security (AES-256 GCM)
If your node uses API keys or passwords, do not store them in plain text. Use `self.get_credential("cred_id")`. The system will automatically decrypt the data at runtime using the master encryption key.

### ⏱️ Performance Tracking
The `AgentEngine` automatically wraps your node in a `run()` method. This tracks:
- Execution time
- Success/Failure status
- Error traces

This data is available in the **Dashboard API** (`/stats`).

### 📦 Large Data Handling
If your node produces a massive output (e.g., >50KB), the engine will automatically move it to `StorageManager` and pass a reference (`ref://uuid`). You don't need to do anything; the engine resolves these references automatically for the next node.

### 🔄 Automatic Retries
If your node fails (throws an exception), the engine will automatically retry it based on the `retry_count` in the node's configuration.

---

## 3. Best Practices
1. **Never use `print()`**: Use the system logger (available in context) or standardize returns.
2. **Pydantic is Mandatory**: Always define a `config_model` to prevent runtime errors.
3. **Handle Errors Gracefully**: Return a dictionary with an `"error"` key if you want the engine to potentially continue or log a clean failure.

---

## 4. Registration
Add your node to `backend/app/nodes/factory.py` in the `NODE_MAP` to make it visible to the studio.
