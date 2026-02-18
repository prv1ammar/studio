import json
from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory

@register_node("universal_agent")
class UniversalAgentNode(BaseNode):
    """
    Standardized, Universal Agent Node that dynamically orchestrates tasks
    based on connected LLM, Tools, and Prompts.
    """
    node_type = "universal_agent"
    version = "1.1.0"
    category = "agents"
    

    properties = [
        {
            'displayName': 'Agent Pattern',
            'name': 'agent_pattern',
            'type': 'string',
            'default': 'standard',
        },
        {
            'displayName': 'Input',
            'name': 'input',
            'type': 'string',
            'default': '',
            'description': 'User message or task',
        },
        {
            'displayName': 'System Prompt',
            'name': 'system_prompt',
            'type': 'string',
            'default': 'You are a professional assistant.',
        },
    ]
    inputs = {
        "system_prompt": {"type": "string", "default": "You are a professional assistant."},
        "agent_pattern": {"type": "string", "enum": ["simple", "standard", "planner"], "default": "standard"},
        "input": {"type": "string", "description": "User message or task"}
    }
    outputs = {
        "output": {"type": "string"},
        "chat_history": {"type": "array"},
        "status": {"type": "string"}
    }
    
    async def _get_connected_nodes(self, context: Dict[str, Any]):
        graph_data = context.get("graph_data", {})
        edges = graph_data.get("edges", [])
        nodes = graph_data.get("nodes", [])
        node_id = context.get("node_id")
        precursor_ids = [e["source"] for e in edges if e["target"] == node_id]
        return [n for n in nodes if n["id"] in precursor_ids]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not context:
            return {"status": "error", "error": "Context required for agent orchestration.", "data": None}
            
        # 1. Input Cleaning
        clean_input = str(input_data)
        if isinstance(input_data, dict):
            clean_input = (
                input_data.get("input") or 
                input_data.get("text") or 
                input_data.get("message") or 
                json.dumps(input_data)
            )
        elif not input_data:
            clean_input = self.get_config("input", "")

        try:
            from ..factory import NodeFactory
            factory = NodeFactory()
            precursors = await self._get_connected_nodes(context)
            
            llm = None
            tools = []
            memory_obj = None
            dynamic_prompt = None
            
            # 2. Resolve Dependencies
            for p_node in precursors:
                p_type_orig = str(p_node.get("data", {}).get("node_type") or p_node.get("data", {}).get("id") or p_node.get("type"))
                p_instance = factory.get_node(p_type_orig, p_node.get("data", {}))
                if not p_instance: continue
                
                child_context = {**context, "node_id": p_node["id"]}
                
                # Check for specific object getters
                if hasattr(p_instance, "get_langchain_object"):
                    obj = await p_instance.get_langchain_object(child_context)
                else:
                    # Fallback to execution if it's a tool-like node
                    exec_res = await p_instance.execute(clean_input, child_context)
                    obj = exec_res.get("data") if isinstance(exec_res, dict) else exec_res
                
                if not obj: continue
                
                # Assign types
                if hasattr(obj, "invoke") and hasattr(obj, "generate"): 
                    llm = obj
                elif hasattr(obj, "run") or (isinstance(obj, list) and obj and hasattr(obj[0], "run")):
                    if isinstance(obj, list): tools.extend(obj)
                    else: tools.append(obj)
                elif isinstance(obj, str): 
                    dynamic_prompt = obj

            if not llm:
                return {"status": "error", "error": "No LLM connected to Agent.", "data": None}

            pattern = self.get_config("agent_pattern", "standard")
            sys_prompt = dynamic_prompt or self.get_config("system_prompt", "You are a professional assistant.")
            chat_history = context.get("chat_history", [])

            # 3. Execution Patterns
            if pattern == "simple" or not tools:
                from langchain_core.output_parsers import StrOutputParser
                lc_prompt = ChatPromptTemplate.from_messages([
                    ("system", sys_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ])
                chain = lc_prompt | llm | StrOutputParser()
                output = await chain.ainvoke({"input": clean_input, "chat_history": chat_history})
                return {"status": "success", "data": {"output": output}}

            # Tool-based patterns
            from langchain_classic.agents import create_tool_calling_agent, create_react_agent, AgentExecutor
            if pattern == "planner":
                # Fallback React Prompt if Hub unavailable
                react_prompt = ChatPromptTemplate.from_template(
                    "Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\n"
                    "Use the following format:\n\nQuestion: {input}\nThought: you should always think about what to do\n"
                    "Action: the action to take, one of [{tool_names}]\nAction Input: input to the action\n"
                    "Observation: result of the action\n... (Thought/Action/Action Input/Observation repeats)\n"
                    "Thought: I now know the final answer\nFinal Answer: final answer\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}"
                )
                agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)
            else:
                lc_prompt = ChatPromptTemplate.from_messages([
                    ("system", sys_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=lc_prompt)

            executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
            res = await executor.ainvoke({"input": clean_input, "chat_history": chat_history})
            
            return {
                "status": "success", 
                "data": {
                    "output": res.get("output", "No response."),
                    "intermediate_steps": str(res.get("intermediate_steps", []))
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Agent Execution Failed: {str(e)}", "data": None}

# Register logic for legacy names to ensure backwards compatibility
from ..registry import NodeRegistry
NodeRegistry.bulk_register([
    "universalAgent", "langchainAgent", "faq_node", "orchestrator_node", "mainAgent"
], UniversalAgentNode)