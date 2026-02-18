"""
Healthcare Intelligence Node - Studio Standard
Batch 55: Industry Specific (Healthcare)
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("healthcare_node")
class HealthcareNode(BaseNode):
    """
    Vertical Node for Healthcare automation.
    Specialized in Patient Triage, Intake Summarization, and Appointment Coordination.
    Designed with HIPAA-compliant data handling patterns in mind.
    """
    node_type = "healthcare_node"
    version = "1.0.0"
    category = "verticals"
    credentials_required = ["healthcare_ai_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'patient_triage',
            'options': [
                {'name': 'Patient Triage', 'value': 'patient_triage'},
                {'name': 'Intake Summary', 'value': 'intake_summary'},
                {'name': 'Scheduling Logic', 'value': 'scheduling_logic'},
                {'name': 'Medical Coding Assistance', 'value': 'medical_coding_assistance'},
            ],
            'description': 'Healthcare action',
        },
        {
            'displayName': 'Input Text',
            'name': 'input_text',
            'type': 'string',
            'default': '',
            'description': 'Patient description, symptoms, or intake notes',
            'required': True,
        },
        {
            'displayName': 'Priority Level',
            'name': 'priority_level',
            'type': 'options',
            'default': 'standard',
            'options': [
                {'name': 'Routine', 'value': 'routine'},
                {'name': 'Urgent', 'value': 'urgent'},
                {'name': 'Emergency', 'value': 'emergency'},
            ],
            'description': 'Pre-determined priority if available',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "patient_triage",
            "options": ["patient_triage", "intake_summary", "scheduling_logic", "medical_coding_assistance"],
            "description": "Healthcare action"
        },
        "input_text": {
            "type": "string",
            "required": True,
            "description": "Patient description, symptoms, or intake notes"
        },
        "priority_level": {
            "type": "dropdown",
            "default": "standard",
            "options": ["routine", "urgent", "emergency"],
            "description": "Pre-determined priority if available"
        }
    }

    outputs = {
        "analysis": {"type": "string"},
        "triage_category": {"type": "string"},
        "summary": {"type": "string"},
        "next_steps": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
             return {"status": "error", "error": "openai library not installed."}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("healthcare_ai_auth")
            api_key = creds.get("api_key") if creds else os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {"status": "error", "error": "Healthcare AI API Key is required."}

            client = AsyncOpenAI(api_key=api_key)
            action = self.get_config("action", "patient_triage")
            text = self.get_config("input_text")
            
            if isinstance(input_data, str) and input_data:
                text = input_data

            if not text:
                 return {"status": "error", "error": "Patient input text is required."}

            # 2. Healthcare Specific System Prompts
            # IMPORTANT: AI does not provide medical advice. This is for administrative triage/summarization.
            system_prompt = f"""
            You are a Healthcare Administrative Assistant. 
            Execution Task: {action}
            Context: Perform clerical and triage support based on patient inputs.
            Constraint: Do not provide definitive medical diagnoses. Use probabilistic triage language. 
            Focus on: Urgency, relevant symptoms, and scheduling priority.
            """

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Process the following patient intake notes:\n{text}"}
                ],
                temperature=0.2
            )

            result_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "data": {
                    "analysis": result_text,
                    "triage_category": "Urgent" if "fever" in text.lower() or "pain" in text.lower() else "Routine",
                    "summary": result_text[:300] + "...",
                    "next_steps": ["Assign to Nurse", "Request lab work", "Schedule follow-up"],
                    "status": "processed"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Healthcare Node Failed: {str(e)}"}