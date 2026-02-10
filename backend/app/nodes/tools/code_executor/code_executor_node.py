from ...base import BaseNode
from typing import Any, Dict, Optional

class CodeExecutorNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        code = self.config.get("code", "def main(inputs):\n    return inputs\n")
        try:
            local_vars = {"inputs": input_data, "result": None}
            # Restrict builtins slightly for safety if needed, 
            # though this is still raw exec
            exec_globals = {
                "__builtins__": __builtins__
            }
            exec(code, exec_globals, local_vars)
            
            if "main" in local_vars and callable(local_vars["main"]):
                return local_vars["main"](input_data)
            
            return local_vars.get("result", str(input_data))
        except Exception as e:
            return f"Code Execution Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        from langchain.tools import Tool
        
        async def code_tool_func(input_str: str):
            # We pass the agent's input string to our code logic
            return await self.execute(input_data={"agent_input": input_str}, context=context)

        return Tool(
            name=f"custom_logic_{self.config.get('id', 'unnamed')}",
            description="Executes custom python logic for processing. Use this for complex data transformations.",
            func=code_tool_func
        )
