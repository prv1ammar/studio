import requests
import time
import re
import json
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from backend.app.nodes.base import BaseNode

class ScraperInput(BaseModel):
    url: str = Field(description="The URL of the real estate listing (Avito/Mubawab) to scrape.")

class RealEstateScraperTool(BaseTool):
    name: str = "real_estate_scraper_tool"
    description: str = "Extracts structured data (ID, price, description) from Avito or Mubawab real estate links."
    args_schema: Type[BaseModel] = ScraperInput
    api_url: str = "https://agents-mcp-hackathon-web-scraper.hf.space/gradio_api/call/scrape_content"

    def _run(self, url: str) -> str:
        try:
            # 1. Initiate scrape
            payload = {"data": [url]}
            res = requests.post(self.api_url, json=payload)
            if res.status_code != 200:
                return f"Error: Failed to initiate scrape for {url}"
            
            event_id = res.json().get("event_id")
            if not event_id:
                return "Error: No event_id returned from scraper"

            # 2. Poll for results
            max_retries = 10
            for i in range(max_retries):
                poll_res = requests.get(f"{self.api_url}/{event_id}")
                if poll_res.status_code == 200:
                    content = poll_res.text
                    if "data:" in content:
                        data_match = re.search(r'data:\s*\[(.*)\]', content)
                        if data_match:
                            try:
                                data_json = json.loads(f"[{data_match.group(1)}]")
                                if data_json and isinstance(data_json[0], dict):
                                    markdown = data_json[0].get("markdown", "")
                                elif data_json and isinstance(data_json[0], str):
                                    markdown = data_json[0]
                                else:
                                    markdown = ""
                                return markdown
                            except Exception as json_err:
                                return f"Error: JSON parse failed: {str(json_err)}"
                time.sleep(1)
            return "Error: Scraping timed out"
        except Exception as e:
            return f"Error: {str(e)}"

class RealEstateScraperNode(BaseNode):
    """
    Specialized scraper for real estate links (Avito, Mubawab), wrapped as a LangChain tool.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tool = RealEstateScraperTool(
            api_url=self.config.get("api_url", "https://agents-mcp-hackathon-web-scraper.hf.space/gradio_api/call/scrape_content")
        )

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Robust input handling: check input_data first, then fallback to config
        url = None
        if isinstance(input_data, str):
            url = input_data
        elif isinstance(input_data, dict):
            url = input_data.get("url")
        
        # Final fallback to node configuration
        if not url:
            url = self.config.get("url")
            
        if not url:
            return {"error": "No URL provided", "status": "failed"}
        
        markdown = self.tool._run(url)
        if markdown.startswith("Error:"):
            return {"error": markdown, "status": "failed"}
            
        property_id = self._extract_id(markdown)
        return {
            "markdown": markdown,
            "property_id": property_id,
            "status": "success",
            "url": url
        }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return self.tool

    def _extract_id(self, text: str) -> Optional[str]:
        if not text: return None
        match = re.search(r'EASYSPACE\s*ID\s*[:=]?\s*(\d+)', text, re.IGNORECASE)
        if not match:
            match = re.search(r'\bID\s*[:=]\s*(\d{2,10})\b', text, re.IGNORECASE)
        return match.group(1) if match else None
