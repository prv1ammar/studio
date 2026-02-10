from typing import Any, Dict, Optional, List
from ...base import BaseNode
import json

class CarouselBuilderNode(BaseNode):
    """
    Formats property matches into a carousel for WhatsApp Business API or web display.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract matches
        matches = []
        
        if isinstance(input_data, dict):
            matches = input_data.get("matches", [])
        elif isinstance(input_data, list):
            matches = input_data
        
        if not matches:
            matches = self.config.get("matches", [])
        
        if not matches:
            return {
                "carousel_json": None,
                "message": "Désolé, aucune propriété ne correspond à vos critères. 😔",
                "status": "empty"
            }
        
        # Determine output format
        output_format = self.config.get("format", "whatsapp")  # "whatsapp" or "web"
        
        if output_format == "whatsapp":
            carousel = self._build_whatsapp_carousel(matches)
        else:
            carousel = self._build_web_carousel(matches)
        
        # Build summary message
        count = len(matches)
        summary = f"✨ J'ai trouvé {count} propriété{'s' if count > 1 else ''} pour vous :\n\n"
        
        return {
            "carousel_json": carousel,
            "summary_message": summary,
            "count": count,
            "status": "success"
        }
    
    def _build_whatsapp_carousel(self, matches: List[Dict]) -> Dict:
        """
        Build WhatsApp Business API carousel format.
        https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#carousel
        """
        cards = []
        
        for i, match in enumerate(matches[:10]):  # WhatsApp limit: 10 cards
            # Extract property details
            title = match.get("property_type", "Propriété")
            if match.get("location"):
                title += f" - {match['location']}"
            
            # Build description
            description_parts = []
            if match.get("price"):
                description_parts.append(f"💰 {match['price']:,} DH/mois")
            if match.get("bedrooms"):
                description_parts.append(f"🛏️ {match['bedrooms']} ch")
            if match.get("surface_m2"):
                description_parts.append(f"📐 {match['surface_m2']} m²")
            
            description = " | ".join(description_parts)
            
            if match.get("description"):
                description += f"\n\n{match['description'][:100]}"
            
            # Build card
            card = {
                "header": {
                    "type": "image",
                    "image": {
                        "link": match.get("image_url", "https://via.placeholder.com/400x300?text=Propriété")
                    }
                },
                "body": {
                    "text": f"**{title}**\n\n{description}"
                },
                "buttons": [
                    {
                        "type": "url",
                        "text": "Voir détails",
                        "url": match.get("url", "#")
                    }
                ]
            }
            
            if match.get("user_phone"):
                card["buttons"].append({
                    "type": "phone_number",
                    "text": "Contacter",
                    "phone_number": match["user_phone"]
                })
            
            cards.append(card)
        
        return {
            "type": "carousel",
            "cards": cards
        }
    
    def _build_web_carousel(self, matches: List[Dict]) -> Dict:
        """
        Build web-friendly carousel format (JSON for frontend rendering).
        """
        cards = []
        
        for match in matches:
            card = {
                "id": match.get("id") or match.get("url"),
                "title": f"{match.get('property_type', 'Propriété')} - {match.get('location', 'Casablanca')}",
                "price": match.get("price"),
                "bedrooms": match.get("bedrooms"),
                "surface_m2": match.get("surface_m2"),
                "description": match.get("description", "")[:150],
                "image_url": match.get("image_url", "https://via.placeholder.com/400x300?text=Propriété"),
                "url": match.get("url"),
                "contact_phone": match.get("user_phone"),
                "location": match.get("location")
            }
            cards.append(card)
        
        return {
            "type": "property_carousel",
            "cards": cards,
            "total": len(cards)
        }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
