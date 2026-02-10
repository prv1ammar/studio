import json
from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_classic.memory import ConversationBufferMemory

@register_node("universalAgent")
class UniversalAgentNode(BaseNode):
    """
    Standardized, Universal Agent Node that dynamically orchestrates tasks
    based on connected LLM, Tools, and Prompts in the Studio graph.
    """
    
    async def _get_connected_nodes(self, context: Dict[str, Any]):
        graph_data = context.get("graph_data", {})
        edges = graph_data.get("edges", [])
        nodes = graph_data.get("nodes", [])
        node_id = context.get("node_id")
        precursor_ids = [e["source"] for e in edges if e["target"] == node_id]
        return [n for n in nodes if n["id"] in precursor_ids]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        if not context:
            return "Error: Context required for agent composition."
            
        # 0. NUCLEAR INPUT CLEANING (Ensure string for LLM)
        if isinstance(input_data, dict):
            input_data = (
                input_data.get("input") or 
                input_data.get("input_data") or 
                input_data.get("input_text") or 
                input_data.get("text") or 
                input_data.get("message") or 
                json.dumps(input_data)
            )
        clean_input = str(input_data)
            
        try:
            from ..factory import NodeFactory
            factory = NodeFactory()
            precursors = await self._get_connected_nodes(context)
            
            llm = None
            tools = []
            memory_obj = None
            dynamic_prompt = None
            
            # 1. Resolve Dependencies
            for p_node in precursors:
                p_type_orig = str(p_node.get("data", {}).get("id") or p_node.get("type"))
                p_type_check = p_type_orig.lower()
                
                # SKIP Flow Control nodes (Engine handles these, not Agent dependencies)
                if any(x in p_type_check for x in ["router", "conditional", "logic", "flow"]):
                    continue
                
                p_instance = factory.get_node(p_type_orig, p_node.get("data", {}))
                if not p_instance: continue
                
                child_context = {**context, "node_id": p_node["id"]}
                obj = await p_instance.get_langchain_object(child_context)
                
                if not obj:
                    if hasattr(p_instance, "execute"):
                        obj = await p_instance.execute(clean_input, child_context)
                
                if not obj: continue
                
                if isinstance(obj, list) and obj:
                     if hasattr(obj[0], "run"): tools.extend(obj)
                     continue
                
                if hasattr(obj, "run"): tools.append(obj)
                elif hasattr(obj, "invoke") and hasattr(obj, "generate"): llm = obj
                elif hasattr(obj, "save_context"): memory_obj = obj
                elif isinstance(obj, BaseChatMessageHistory):
                    memory_obj = ConversationBufferMemory(chat_memory=obj, return_messages=True, memory_key="chat_history", output_key="output")
                elif isinstance(obj, str): dynamic_prompt = obj

            if not llm:
                return "Error: No LLM connected."

            agent_pattern = self.config.get("agent_pattern", "standard").lower()
            system_prompt = dynamic_prompt or self.config.get("system_prompt") or "You are a professional assistant."
            
            # Tier 1: SIMPLE
            if agent_pattern == "simple" or not tools:
                from langchain_core.output_parsers import StrOutputParser
                lc_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ])
                chain = lc_prompt | llm | StrOutputParser()
                return await chain.ainvoke({"input": clean_input, "chat_history": context.get("chat_history", [])})

            # Tier 2 & 3: TOOL-BASED
            try:
                if agent_pattern == "planner":
                    from langchain_classic.agents import create_react_agent, AgentExecutor
                    react_prompt = None
                    try:
                        from langchain import hub
                        react_prompt = hub.pull("hwchase17/react")
                    except:
                        pass
                    
                    if not react_prompt:
                         react_prompt = ChatPromptTemplate.from_template(
                             "Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\n"
                             "Use the following format:\n\nQuestion: {input}\nThought: you should always think about what to do\n"
                             "Action: the action to take, one of [{tool_names}]\nAction Input: input to the action\n"
                             "Observation: result of the action\n... (Thought/Action/Action Input/Observation repeats)\n"
                             "Thought: I now know the final answer\nFinal Answer: final answer\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}"
                         )
                    agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt)
                else:
                    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
                    lc_prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad"),
                    ])
                    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=lc_prompt)

                executor = AgentExecutor(agent=agent, tools=tools, memory=memory_obj, verbose=True, handle_parsing_errors=True)
                res = await executor.ainvoke({"input": clean_input, "chat_history": context.get("chat_history", [])})
                return res.get("output", "No response.")

            except Exception as e:
                print(f"[Universal Agent] Fallback triggered: {e}")
                return await llm.ainvoke(clean_input)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Agent Error: {str(e)}"

# Register legacy IDs
from ..registry import NodeRegistry
NodeRegistry.bulk_register([
    "langchainAgent", "faq_node", "availability_node", "booking_node", 
    "patient_node", "orchestrator_node", "configurable_node",
    "router_node", "easySpaceAgent", "mainAgent"
], UniversalAgentNode)
