import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class RecoveryStrategy(BaseModel):
    strategy: str = Field(description="One of 'retry', 'fail_over', 'skip', 'abort'")
    reason: str = Field(description="Human readable explanation")
    delay: Optional[int] = Field(default=0)
    config_patch: Optional[Dict[str, Any]] = Field(default=None)

class SelfHealingAgent:
    """
    The brain of Phase 7. Analyzes node failures and suggests recovery strategies.
    Uses LangChain to reason about complex failures.
    """
    
    def __init__(self):
        self.enabled = True
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.parser = JsonOutputParser(pydantic_object=RecoveryStrategy)

    async def analyze_and_suggest(self, node_type: str, error_message: str, config: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """
        Analyzes a failure and returns a strategy using LangChain reasoning.
        """
        if not self.enabled:
            return {"strategy": "abort", "reason": "Self-healing disabled."}

        # 1. Immediate Logic for known patterns (Fast path)
        error_lower = error_message.lower()
        if "rate limit" in error_lower or "429" in error_lower:
             return {"strategy": "retry", "delay": min(2 ** attempt, 30), "reason": "Rate limit detected (Fast Logic)"}

        # 2. AI-Driven Reasoning (LangChain Path)
        prompt = ChatPromptTemplate.from_template(
            "Analyze the following node execution failure and suggest a recovery strategy.\n"
            "Node Type: {node_type}\n"
            "Error: {error}\n"
            "Config: {config}\n"
            "Attempt: {attempt}\n\n"
            "{format_instructions}"
        )
        
        chain = prompt | self.llm | self.parser
        
        try:
            result = await chain.ainvoke({
                "node_type": node_type,
                "error": error_message,
                "config": json.dumps(config),
                "attempt": attempt,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f" Self-Healing Reasoner Failed: {e}")
            return {"strategy": "retry", "delay": 2, "reason": "Fallback retry due to reasoner failure."}

self_healing = SelfHealingAgent()

