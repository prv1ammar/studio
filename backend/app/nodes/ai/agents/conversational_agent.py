from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("conversational_agent_node")
class ConversationalAgentNode(BaseAgentNode):
    """
    Chat-optimized agent with built-in memory support.
    Ideal for interactive bots.
    """
    node_type = "conversational_agent_node"
    
    properties = [
        {
            'displayName': 'System Instructions',
            'name': 'system_prompt',
            'type': 'string',
            'default': 'You are a warm and helpful AI assistant.',
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.agents import AgentExecutor, create_json_chat_agent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
            
            # 1. Resolve Dependencies
            llm = await self.get_llm_from_context(context)
            tools = await self.get_tools_from_context(context)
            chat_history = await self.get_memory_from_context(context) or []

            if not llm:
                return {"status": "error", "error": "LLM Required connection."}

            # 2. Build Prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_config("system_prompt")),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # 3. Initialize Agent
            # Note: JSON Chat Agent is more robust for general LLMs
            agent = create_json_chat_agent(llm, tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=True, 
                handle_parsing_errors=True
            )

            # 4. Run
            query = str(input_data)
            response = await agent_executor.ainvoke({
                "input": query,
                "chat_history": chat_history
            })

            return {
                "status": "success",
                "data": {
                    "text": response.get("output", ""),
                    "history_length": len(chat_history)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Conversational Agent Error: {str(e)}"}
