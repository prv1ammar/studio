import json
import logging
from typing import Any, Dict, Optional, List, Type
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node, NodeRegistry
from app.core.credentials import cred_manager

# Conditional imports for LangChain
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import Tool
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

logger = logging.getLogger(__name__)

class AutonomousAgentConfig(NodeConfig):
    system_prompt: str = Field(
        "You are an autonomous studio assistant. Use the provided tools to solve the user's request. "
        "If you don't have a tool for a specific task, explain it to the user.",
        description="Behavior instructions for the agent"
    )
    model_provider: str = Field("openai", description="openai or google")
    model_name: str = Field("gpt-4o", description="Model identifier")
    credentials_id: Optional[str] = Field(None, description="LLM API Key Credentials ID")
    allowed_tools: List[str] = Field(default_factory=list, description="IDs of nodes allowed as tools. Empty for all.")
    max_iterations: int = Field(5, description="Maximum tool-use loops")

@register_node("autonomous_agent")
class AutonomousAgentNode(BaseNode):
    config_model = AutonomousAgentConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if not HAS_LANGCHAIN:
            return {"error": "LangChain dependencies missing. Please install langchain-openai and langchain-google-genai."}

        # 1. Setup LLM
        creds = await self.get_credential("credentials_id")
        api_key = creds.get("api_key") or creds.get("token") if creds else None
        
        provider = self.get_config("model_provider", "openai").lower()
        model_name = self.get_config("model_name", "gpt-4o")
        
        if not api_key:
            return {"error": f"API Key for {provider} is required in credentials_id."}

        try:
            if provider == "openai":
                llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=0)
            elif provider == "google":
                llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0)
            else:
                return {"error": f"Unsupported provider: {provider}"}
        except Exception as e:
            return {"error": f"Failed to initialize LLM: {str(e)}"}

        # 2. Build Tools from NodeRegistry
        tools = await self._build_tools(context)
        
        # 3. Setup Agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_config("system_prompt")),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            max_iterations=self.get_config("max_iterations")
        )

        # 4. Run
        user_input = input_data if isinstance(input_data, str) else json.dumps(input_data)
        
        try:
            result = await agent_executor.ainvoke({"input": user_input})
            return result["output"]
        except Exception as e:
            logger.error(f"Agent Execution Error: {e}")
            return {"error": f"Agent failed: {str(e)}"}

    async def _build_tools(self, context: Optional[Dict[str, Any]]) -> List[Tool]:
        all_nodes = NodeRegistry.get_all_nodes()
        allowed = self.get_config("allowed_tools", [])
        
        tools = []
        
        for node_id, node_class in all_nodes.items():
            # Skip self and abstract/utility nodes
            if node_id == "autonomous_agent" or node_id in ["BaseNode", "GoogleNode"]:
                continue
            
            # Apply whitelist if present
            if allowed and node_id not in allowed:
                continue

            # Create a tool wrapper
            # We need to capture node_id and node_class in the closure
            def create_tool(nid=node_id, ncls=node_class):
                async def tool_func(tool_input: str) -> str:
                    try:
                        # Parse input if it looks like JSON
                        try:
                            # Many nodes expect specific config. 
                            # For now, we pass tool_input as the 'input_data' to execute.
                            # The 'raw_config' of the tool node is empty or derived from context if possible.
                            input_val = json.loads(tool_input)
                        except:
                            input_val = tool_input
                            
                        # PROBLEM: Most nodes need CONFIG, not just input_data.
                        # For an autonomous agent, it might need to "configure" the node too.
                        # Simplification: We assume the node is pre-configured or handles generic input.
                        node_instance = ncls(config={}) 
                        # We inject context for credential access
                        res = await node_instance.execute(input_val, context)
                        return json.dumps(res) if not isinstance(res, str) else res
                    except Exception as e:
                        return f"Error executing {nid}: {str(e)}"
                
                return Tool(
                    name=nid,
                    func=tool_func, # sync wrapper usually needed but ainvoke works
                    coroutine=tool_func,
                    description=f"Executes the '{nid}' node. Input should be a JSON string or text."
                )

            tools.append(create_tool())
            
        return tools
