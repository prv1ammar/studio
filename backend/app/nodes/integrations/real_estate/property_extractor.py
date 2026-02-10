from typing import Any, Dict, Optional
from ...base import BaseNode
from ...models.litellm.litellm_node import LiteLLMNode
import json
import re

class PropertyExtractorNode(BaseNode):
    """
    Extracts property search criteria from user messages.
    Returns: location, budget_max, bedrooms, property_type.
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
                "location": None,
                "budget_max": None,
                "bedrooms": None,
                "property_type": None,
                "error": "No user message provided",
                "status": "failed"
            }
        
        # Use LiteLLM for extraction
        llm_node = LiteLLMNode(config=self.config)
        llm = await llm_node.get_langchain_object()
        
        extraction_prompt = f"""You are a property search criteria extractor for Casablanca, Morocco.

Extract the following information from this user message:
- location: Neighborhood or area in Casablanca (e.g., "Maarif", "Gauthier", "Anfa")
- budget_max: Maximum monthly rent in Moroccan Dirhams (DH). Extract numbers only.
- bedrooms: Number of bedrooms (1, 2, 3, etc.)
- property_type: Type of property (Appartement, Studio, Villa, Maison, Bureau)

User message: "{user_message}"

Respond ONLY with valid JSON in this exact format:
{{"location": "string or null", "budget_max": number or null, "bedrooms": number or null, "property_type": "string or null"}}

If information is not mentioned, use null."""

        try:
            response = llm.invoke(extraction_prompt)
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean markdown code blocks if present
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text.strip())
            
            return {
                "location": result.get("location"),
                "budget_max": result.get("budget_max"),
                "bedrooms": result.get("bedrooms"),
                "property_type": result.get("property_type"),
                "status": "success"
            }
            
        except Exception as e:
            # Fallback: regex extraction
            message_lower = user_message.lower()
            
            # Extract budget (numbers followed by DH or MAD)
            budget_match = re.search(r'(\d+)\s*(dh|mad|dirham)', message_lower)
            budget = int(budget_match.group(1)) if budget_match else None
            
            # Extract bedrooms
            bedroom_match = re.search(r'(\d+)\s*(chambre|bedroom|ch)', message_lower)
            bedrooms = int(bedroom_match.group(1)) if bedroom_match else None
            
            # Extract location (common Casablanca neighborhoods)
            neighborhoods = ["maarif", "gauthier", "anfa", "bourgogne", "racine", "oasis", "palmier", 
                           "californie", "ain diab", "sidi maarouf", "hay hassani", "derb sultan"]
            location = None
            for neighborhood in neighborhoods:
                if neighborhood in message_lower:
                    location = neighborhood.title()
                    break
            
            # Extract property type
            property_type = None
            if "studio" in message_lower:
                property_type = "Studio"
            elif "appartement" in message_lower or "appart" in message_lower:
                property_type = "Appartement"
            elif "villa" in message_lower:
                property_type = "Villa"
            elif "maison" in message_lower:
                property_type = "Maison"
            
            return {
                "location": location,
                "budget_max": budget,
                "bedrooms": bedrooms,
                "property_type": property_type,
                "status": "success",
                "note": f"Fallback extraction used due to: {str(e)}"
            }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
