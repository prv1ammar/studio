from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class LegalConfig(NodeConfig):
    operation: str = Field("contract_analysis", description="Operation: contract_analysis, compliance_check, risk_assessment")
    model: str = Field("gpt-4-turbo", description="LLM Model for analysis")
    jurisdiction: str = Field("US", description="Legal jurisdiction (US, EU, UK)")
    api_key: Optional[str] = Field(None, description="OpenAI API Key (Optional Override)")

@register_node("legal_node")
class LegalNode(BaseNode):
    """
    Vertical Node for Legal Automation.
    Specialized in analyzing legal documents, checking compliance, and assessing risk.
    """
    node_id = "legal_node"
    config_model = LegalConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        operation = self.get_config("operation")
        jurisdiction = self.get_config("jurisdiction")
        
        # LLM Integration
        import os
        from openai import AsyncOpenAI

        api_key = self.get_config("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "Missing OpenAI API Key. Please configure it in the node or environment."}

        client = AsyncOpenAI(api_key=api_key)
        model = self.get_config("model")
        
        system_prompt = f"""You are an elite Legal AI Assistant specialized in {jurisdiction} Law.
        Perform the requested operation with high precision.
        """
        
        user_content = ""
        if operation == "contract_analysis":
            system_prompt += "Analyze the provided contract text. Identify key clauses, missing terms, and potential risks."
            user_content = f"Contract Text:\n{input_data}"
        elif operation == "compliance_check":
            system_prompt += "Check the provided text/policy for compliance gaps against standard regulations (e.g., GDPR, CCPA) within the jurisdiction."
            user_content = f"Policy Text:\n{input_data}"
        elif operation == "risk_assessment":
            system_prompt += "Assess legal risks in the given scenario or document. Provide a risk level (Low/Medium/High) and mitigation steps."
            user_content = f"Scenario:\n{input_data}"
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return {
                "status": "success",
                "operation": operation,
                "jurisdiction": jurisdiction,
                "analysis": content,
                "model_used": model
            }
        except Exception as e:
            return {"error": f"Legal AI Analysis Failed: {str(e)}"}
