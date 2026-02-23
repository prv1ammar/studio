from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("plan_execute_agent_node")
class PlanAndExecuteAgentNode(BaseAgentNode):
    """
    Reasoning architecture: Plan first, then solve each step.
    Handles complex multi-step tasks by breaking them down.
    """
    node_type = "plan_execute_agent_node"
    
    properties = [
        {
            'displayName': 'Planner Prompt',
            'name': 'planner_prompt',
            'type': 'string',
            'default': 'Break down the user request into a list of logical steps. Use the tools available to solve each step.',
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain_core.output_parsers import StrOutputParser
            
            # 1. Resolve Dependencies
            llm = await self.get_llm_from_context(context)
            tools = await self.get_tools_from_context(context)
            
            if not llm:
                return {"status": "error", "error": "LLM Required connection."}

            # 2. Phase 1: Planning
            planner_prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_config("planner_prompt")),
                ("human", "Request: {input}\n\nPlan the steps:")
            ])
            planner_chain = planner_prompt | llm | StrOutputParser()
            plan = await planner_chain.ainvoke({"input": str(input_data)})
            
            # 3. Phase 2: Execution 
            # We use a tool-calling agent to solve the whole plan
            exec_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an executor. Your task is to complete the following plan:\n\n" + plan),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_tool_calling_agent(llm, tools, exec_prompt)
            executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            response = await executor.ainvoke({"input": "Perform the plan described above."})

            return {
                "status": "success",
                "data": {
                    "text": response.get("output", ""),
                    "plan": plan
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Plan & Execute Error: {str(e)}"}
