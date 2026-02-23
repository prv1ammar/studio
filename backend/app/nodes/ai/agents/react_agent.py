from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("react_agent_node")
class ReActAgentNode(BaseAgentNode):
    """
    Think -> Act -> Observe loop.
    A powerful reasoning agent that uses tools to solve steps sequentially.
    """
    node_type = "react_agent_node"
    
    properties = [
        {
            'displayName': 'System Prompt',
            'name': 'system_prompt',
            'type': 'string',
            'default': 'You are a helpful assistant. Answer the user question as best as you can. You have access to the following tools:',
        },
        {
            'displayName': 'Max Iterations',
            'name': 'max_iterations',
            'type': 'number',
            'default': 10,
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.agents import AgentExecutor, create_react_agent
            from langchain_core.prompts import PromptTemplate
            
            # 1. Resolve Dependencies
            llm = await self.get_llm_from_context(context)
            tools = await self.get_tools_from_context(context)
            
            if not llm:
                return {"status": "error", "error": "LLM Required. Please connect a model node to the agent."}
            if not tools:
                 # ReAct without tools is just a standard LLM call, but LangChain requires them
                 return {"status": "error", "error": "Tools Required. ReAct Agent needs tools to function."}

            # 2. Build Prompt
            # ReAct requires a prompt with specific variables: tools, tool_names, input, agent_scratchpad
            template = self.get_config("system_prompt") + """
            {tools}
            
            Use the following format:
            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question
            
            Begin!
            
            Question: {input}
            Thought: {agent_scratchpad}
            """
            prompt = PromptTemplate.from_template(template)

            # 3. Initialize Agent
            agent = create_react_agent(llm, tools, prompt)
            
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=True, 
                handle_parsing_errors=True,
                max_iterations=int(self.get_config("max_iterations", 10))
            )

            # 4. Run
            query = str(input_data)
            response = await agent_executor.ainvoke({"input": query})

            return {
                "status": "success",
                "data": {
                    "text": response.get("output", ""),
                    "intermediate_steps": str(response.get("intermediate_steps", []))
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"ReAct Agent Error: {str(e)}"}
