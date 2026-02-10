from typing import Any, Dict, Optional
from ...base import BaseNode
import re
import json

class LeadFormatterNode(BaseNode):
    """
    Formats scraped property data for Smart DB insertion.
    Parses markdown from RE Scraper and extracts structured fields.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract inputs
        markdown = None
        url = None
        user_phone = None
        
        # 1. Handle Input Data Sources
        if isinstance(input_data, dict):
            # Try to get markdown from various common keys
            markdown = input_data.get("markdown") or input_data.get("input") or input_data.get("text") or input_data.get("input_text")
            url = input_data.get("url")
            user_phone = input_data.get("user_phone")
            
            # If markdown is still a dict (from scraper nested output), extract recursively
            if isinstance(markdown, dict):
                print(f"DEBUG [LeadFormatter]: Markdown input is a dict, extracting content...")
                markdown = markdown.get("markdown") or markdown.get("content") or markdown.get("text") or json.dumps(markdown)
        elif isinstance(input_data, str):
            markdown = input_data
        
        # 2. FORCE STRING CONVERSION (Safety check for slicing)
        if markdown is None:
            markdown = ""
        
        if not isinstance(markdown, str):
            print(f"DEBUG [LeadFormatter]: Markdown is {type(markdown)}, forcing to string.")
            markdown = str(markdown)
            
        if not markdown.strip():
            return {
                "error": "No markdown content provided",
                "status": "failed"
            }
        
        # 3. Extract structured data from markdown
        formatted_lead = {
            "url": url,
            "source": "Avito" if "avito" in (url or "").lower() else "Mubawab" if "mubawab" in (url or "").lower() else "Unknown",
            "user_phone": user_phone,
            "raw_markdown": markdown[:500],  # This will now NEVER fail with 'unhashable type: slice'
            "status": "new"
        }
        
        # 4. Numeric Extractions (Robust Regex)
        # Extract price
        price_match = re.search(r'(\d+[\s\u202f,]*\d*)\s*(DH|MAD|Dhs)', markdown, re.IGNORECASE)
        if price_match:
            price_str = re.sub(r'\D', '', price_match.group(1))
            if price_str:
                formatted_lead["price"] = int(price_str)
        
        # Extract surface area
        surface_match = re.search(r'(\d+)\s*m[²2]', markdown, re.IGNORECASE)
        if surface_match:
            surface_str = re.sub(r'\D', '', surface_match.group(1))
            if surface_str:
                formatted_lead["surface_m2"] = int(surface_str)
        
        # Extract number of rooms/bedrooms
        rooms_match = re.search(r'(\d+)\s*(chambre|bedroom|pièce|room)', markdown, re.IGNORECASE)
        if rooms_match:
            rooms_str = re.sub(r'\D', '', rooms_match.group(1))
            if rooms_str:
                formatted_lead["bedrooms"] = int(rooms_str)
        
        # 5. Location Extraction
        neighborhoods = ["Maarif", "Gauthier", "Anfa", "Bourgogne", "Racine", "Oasis", "Palmier",
                        "Californie", "Ain Diab", "Sidi Maarouf", "Hay Hassani", "Derb Sultan",
                        "Bouskoura", "Belvédère", "2 Mars", "Beauséjour"]
        
        for neighborhood in neighborhoods:
            if neighborhood.lower() in markdown.lower():
                formatted_lead["location"] = neighborhood
                break
        
        # 6. Description Extraction
        lines = markdown.split('\n')
        description_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#') and not line.startswith('!')]
        if description_lines:
            formatted_lead["description"] = description_lines[0][:200]
        
        # 7. Property Type Extraction
        m_lower = markdown.lower()
        if "studio" in m_lower:
            formatted_lead["property_type"] = "Studio"
        elif "appartement" in m_lower or "apartment" in m_lower:
            formatted_lead["property_type"] = "Appartement"
        elif "villa" in m_lower:
            formatted_lead["property_type"] = "Villa"
        elif "maison" in m_lower:
            formatted_lead["property_type"] = "Maison"
        elif "bureau" in m_lower or "office" in m_lower:
            formatted_lead["property_type"] = "Bureau"
        
        # 8. Final Metadata
        from datetime import datetime
        formatted_lead["created_at"] = datetime.now().isoformat()
        
        return {
            "formatted_lead": formatted_lead,
            "status": "success"
        }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
