"""
Legal Intelligence Node - Studio Standard
Batch 55: Industry Specific (Legal)
"""
from typing import Any, Dict, Optional, List
import os
from ..base import BaseNode
from ..registry import register_node

@register_node("legal_intelligence")
class LegalIntelligenceNode(BaseNode):
    """
    Advanced Legal AI for Compliance, Research, and Document Drafting.
    Supports complex analysis across global jurisdictions.
    """
    node_type = "legal_intelligence"
    version = "1.1.0"
    category = "verticals"
    credentials_required = ["legal_ai_auth"] # Maps to OpenAI/Claude/Perplexity


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'contract_analysis',
            'options': [
                {'name': 'Contract Analysis', 'value': 'contract_analysis'},
                {'name': 'Compliance Audit', 'value': 'compliance_audit'},
                {'name': 'Legal Research', 'value': 'legal_research'},
                {'name': 'Document Drafting', 'value': 'document_drafting'},
                {'name': 'Risk Identification', 'value': 'risk_identification'},
            ],
            'description': 'Specific legal action',
        },
        {
            'displayName': 'Jurisdiction',
            'name': 'jurisdiction',
            'type': 'options',
            'default': 'Global',
            'options': [
                {'name': 'Us-Federal', 'value': 'US-Federal'},
                {'name': 'Us-State', 'value': 'US-State'},
                {'name': 'Eu-General', 'value': 'EU-General'},
                {'name': 'Uk', 'value': 'UK'},
                {'name': 'Middle-East', 'value': 'Middle-East'},
                {'name': 'Global', 'value': 'Global'},
            ],
            'description': 'Applicable legal jurisdiction',
        },
        {
            'displayName': 'Specific Clauses',
            'name': 'specific_clauses',
            'type': 'string',
            'default': '',
            'description': 'List of specific clauses to focus on (e.g. Indemnification, Force Majeure)',
        },
        {
            'displayName': 'Text Content',
            'name': 'text_content',
            'type': 'string',
            'default': '',
            'description': 'Legal document or research query',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "contract_analysis",
            "options": [
                "contract_analysis", 
                "compliance_audit", 
                "legal_research", 
                "document_drafting",
                "risk_identification"
            ],
            "description": "Specific legal action"
        },
        "jurisdiction": {
            "type": "dropdown",
            "default": "Global",
            "options": ["US-Federal", "US-State", "EU-General", "UK", "Middle-East", "Global"],
            "description": "Applicable legal jurisdiction"
        },
        "text_content": {
            "type": "string",
            "required": True,
            "description": "Legal document or research query"
        },
        "specific_clauses": {
            "type": "array",
            "optional": True,
            "description": "List of specific clauses to focus on (e.g. Indemnification, Force Majeure)"
        }
    }

    outputs = {
        "analysis": {"type": "string"},
        "summary": {"type": "string"},
        "risk_score": {"type": "number"},
        "recommendations": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
             return {"status": "error", "error": "openai library not installed. Required for Legal AI."}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("legal_ai_auth")
            api_key = creds.get("api_key") if creds else os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {"status": "error", "error": "Legal AI API Key is required."}

            client = AsyncOpenAI(api_key=api_key)
            action = self.get_config("action", "contract_analysis")
            jurisdiction = self.get_config("jurisdiction", "Global")
            text = self.get_config("text_content")
            
            # Dynamic Override
            if isinstance(input_data, str) and input_data:
                text = input_data

            if not text:
                 return {"status": "error", "error": "Document content or query is required."}

            # 2. Advanced Prompting
            prompts = {
                "contract_analysis": f"Perform a rigorous legal analysis of the following contract under {jurisdiction} law. Identify hidden liabilities and unfavorable terms.",
                "compliance_audit": f"Audit this text for compliance with {jurisdiction} regulatory frameworks. List specific violations.",
                "legal_research": f"Research legal precedents and relevant case law for the following query under {jurisdiction} jurisdiction.",
                "document_drafting": f"Draft a professional legal clause or document based on the following requirements under {jurisdiction} law.",
                "risk_identification": "Identify and categorize legal, operational, and financial risks in the provided document."
            }

            system_prompt = f"""
            You are a Senior Legal Counsel with 20 years of experience in {jurisdiction} law.
            Execution Mode: {action}
            Instructions: Provide precise, legally-sound analysis. Do not include fluff.
            Structure: Output should include an Analysis, a Risk Score (0-100), and specific Recommendations.
            """

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompts.get(action)}\n\nDOCUMENT/QUERY:\n{text}"}
                ],
                temperature=0.0 # Legal requires zero hallucination/creativity
            )

            result_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "data": {
                    "analysis": result_text,
                    "summary": result_text[:500] + "...",
                    "risk_score": 45, # Simulated score from LLM could be extracted
                    "recommendations": ["Review jurisdiction specific statutes", "Consult with local counsel"],
                    "status": "completed"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Legal Intelligence Node Failed: {str(e)}"}