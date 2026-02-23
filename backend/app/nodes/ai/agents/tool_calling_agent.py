from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("tool_calling_agent_node")
class ToolCallingAgentNode(BaseAgentNode):
    """
    Native tool-calling agent.
    Optimized for models like GPT-4o, Claude 3.5, and Gemini.
    """
    node_type = "tool_calling_agent_node"
    
    properties = [
        {
            'displayName': 'System Prompt',
            'name': 'system_prompt',
            'type': 'string',
            'default': 'You are a task-oriented assistant. Use tools when necessary to provide accurate info.',
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
            
            # 1. Resolve Dependencies
            llm = await self.get_llm_from_context(context)
            tools = await self.get_tools_from_context(context)
            
            if not llm:
                return {"status": "error", "error": "LLM Required connection."}

            # 2. Build Prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_config("system_prompt")),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # 3. Initialize Agent
            agent = create_tool_calling_agent(llm, tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=True
            )

            # 4. Run
            query = str(input_data)
            response = await agent_executor.ainvoke({"input": query})

            return {
                "status": "success",
                "data": {
                    "text": response.get("output", "")
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Tool Calling Agent Error: {str(e)}"}
