from typing import Any, Dict, Optional
from .base_agent import BaseAgentNode
from ..registry import register_node

@register_node("sql_agent_node")
class SQLAgentNode(BaseAgentNode):
    """
    Data Intelligence Agent.
    Converts Natural Language to SQL and executes it securely.
    Supports Postgres, MySQL, SQLite, etc.
    """
    node_type = "sql_agent_node"
    
    properties = [
        {
            'displayName': 'Connection String',
            'name': 'connection_string',
            'type': 'string',
            'placeholder': 'postgresql://user:pass@localhost/dbname',
            'description': 'SQLAlchemy connection string',
        },
        {
            'displayName': 'Max Iterations',
            'name': 'max_iterations',
            'type': 'number',
            'default': 15,
        }
    ]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain_community.agent_toolkits import create_sql_agent
            from langchain_community.utilities import SQLDatabase
            
            # 1. Resolve Dependencies
            llm = await self.get_llm_from_context(context)
            db_uri = self.get_config("connection_string")
            
            if not llm:
                return {"status": "error", "error": "LLM Required connection. SQL Agent needs a model to generate queries."}
            if not db_uri:
                return {"status": "error", "error": "Connection String Required. Provide a valid SQLAlchemy URI."}

            # 2. Connect to Database
            db = SQLDatabase.from_uri(db_uri)

            # 3. Initialize SQL Agent
            # Using 'openai-tools' agent type if possible, or fallback
            try:
                agent_executor = create_sql_agent(
                    llm, 
                    db=db, 
                    agent_type="openai-tools", 
                    verbose=True,
                    max_iterations=int(self.get_config("max_iterations", 15))
                )
            except:
                # Fallback for models that don't support openai-tools
                agent_executor = create_sql_agent(
                    llm, 
                    db=db, 
                    agent_type="zero-shot-react-description", 
                    verbose=True
                )

            # 4. Run
            query = str(input_data)
            response = await agent_executor.ainvoke({"input": query})

            return {
                "status": "success",
                "data": {
                    "text": response.get("output", ""),
                    "result": str(response)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"SQL Agent Error: {str(e)}"}
