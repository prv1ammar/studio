from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("openai_functions_agent_node")
class OpenAIFunctionsAgentNode(BaseAgentNode):
    """
    Classic OpenAI Functions agent.
    Optimized for older GPT-4/3.5 models that use the 'functions' parameter.
    """
    node_type = "openai_functions_agent_node"
    
    properties = [
        {
            'displayName': 'System Instruct',
            'name': 'system_prompt',
            'type': 'string',
            'default': 'You are a helpful assistant.',
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.agents import AgentExecutor, create_openai_functions_agent
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
            agent = create_openai_functions_agent(llm, tools, prompt)
            
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
            return {"status": "error", "error": f"OpenAI Functions Agent Error: {str(e)}"}
