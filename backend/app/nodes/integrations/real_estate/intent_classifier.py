from typing import Any, Dict, Optional
from ...base import BaseNode
from ...models.litellm.litellm_node import LiteLLMNode
import json

class IntentClassifierNode(BaseNode):
    """
    Classifies user intent for real estate interactions.
    Determines if user wants to SEARCH_RENTAL, LIST_PROPERTY, or GENERAL_INQUIRY.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract user message
        user_message = None
        if isinstance(input_data, str):
            user_message = input_data
        elif isinstance(input_data, dict):
            user_message = input_data.get("user_message") or input_data.get("text")
        
        if not user_message:
            user_message = self.config.get("user_message")
            
        if not user_message:
            return {
                "intent": "GENERAL_INQUIRY",
                "confidence": 0.0,
                "error": "No user message provided"
            }
        
        # Use LiteLLM for classification
        llm_node = LiteLLMNode(config=self.config)
        llm = await llm_node.get_langchain_object()
        
        classification_prompt = f"""You are an intent classifier for a Moroccan real estate assistant.

Analyze this user message and classify it into ONE of these intents:
- SEARCH_RENTAL: User is looking to rent/find a property (Tenant)
- LIST_PROPERTY: User wants to list/advertise their property (Owner)
- PARTNER_INQUIRY: User wants to collaborate, invest, offer services, or become a partner (Partner)
- GENERAL_INQUIRY: General questions

User message: "{user_message}"

Respond ONLY with valid JSON in this exact format:
{{"intent": "SEARCH_RENTAL|LIST_PROPERTY|PARTNER_INQUIRY|GENERAL_INQUIRY", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

        try:
            response = llm.invoke(classification_prompt)
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            # Clean markdown code blocks if present
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text.strip())
            
            intent = result.get("intent", "GENERAL_INQUIRY")
            
            # OVERRIDE: If LLM is unsure but we see a clear property portal link
            if any(x in user_message.lower() for x in ["avito.ma", "mubawab.ma", "sarouty.ma"]):
                intent = "LIST_PROPERTY"

            return {
                "intent": intent,
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", ""),
                "text": user_message,
                "status": "success"
            }
            
        except Exception as e:
            # Fallback: simple keyword matching
            message_lower = user_message.lower()
            
            # Check for listing indicators
            if any(keyword in message_lower for keyword in ["avito", "mubawab", "http", "www.", "lister", "vendre", "louer mon", "annonces", "bien", "immobili"]):
                return {
                    "intent": "LIST_PROPERTY",
                    "confidence": 0.7,
                    "reasoning": "Contains property listing URL or keywords (Fallback)",
                    "text": user_message,
                    "status": "success"
                }
            
            # Check for search indicators
            if any(keyword in message_lower for keyword in ["cherche", "besoin", "recherche", "trouver", "appartement", "studio", "villa", "rent", "buy", "apartment", "search", "looking for"]):
                return {
                    "intent": "SEARCH_RENTAL",
                    "confidence": 0.7,
                    "reasoning": "Contains property search keywords",
                    "status": "success"
                }
            
            return {
                "intent": "GENERAL_INQUIRY",
                "confidence": 0.5,
                "reasoning": f"Fallback classification due to error: {str(e)}",
                "status": "success"
            }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
