"""
ArXiv Node - Studio Standard (Universal Method)
"""
from typing import Any, Dict, Optional, List
import urllib.request
from urllib.parse import urlparse, quote
from xml.etree.ElementTree import Element
from defusedxml.ElementTree import fromstring
from ...base import BaseNode
from ...registry import register_node

@register_node("arxiv_node")
class ArXivNode(BaseNode):
    """
    Search and retrieve papers from arXiv.org
    """
    node_type = "arxiv_node"
    version = "1.0.0"
    category = "search"
    credentials_required = []

    inputs = {
        "search_query": {
            "type": "string",
            "required": True,
            "description": "The search query for arXiv papers (e.g., 'quantum computing')"
        },
        "search_type": {
            "type": "dropdown",
            "default": "all",
            "options": ["all", "title", "abstract", "author", "cat"],
            "description": "The field to search in"
        },
        "max_results": {
            "type": "number",
            "default": 10,
            "description": "Maximum number of results to return"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            search_query = self.get_config("search_query") or str(input_data)
            search_type = self.get_config("search_type", "all")
            max_results = int(self.get_config("max_results", 10))

            base_url = "http://export.arxiv.org/api/query?"
            
            if search_type == "all":
                query = search_query
            else:
                prefix_map = {"title": "ti", "abstract": "abs", "author": "au", "cat": "cat"}
                prefix = prefix_map.get(search_type, "")
                query = f"{prefix}:{search_query}"

            params = {
                "search_query": query,
                "max_results": str(max_results),
            }
            
            query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
            url = base_url + query_string

            # Use aiohttp for async if possible, but keeping logic consistent with their component
            # Actually, standard Studio uses aiohttp. 
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response_text = await response.text()
            
            papers = self._parse_atom_response(response_text)
            
            return {
                "status": "success",
                "data": {
                    "results": papers
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"ArXiv Search Failed: {str(e)}"}

    def _parse_atom_response(self, response_text: str) -> List[Dict[str, Any]]:
        root = fromstring(response_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
        papers = []
        for entry in root.findall("atom:entry", ns):
            paper = {
                "id": self._get_text(entry, "atom:id", ns),
                "title": self._get_text(entry, "atom:title", ns),
                "summary": self._get_text(entry, "atom:summary", ns),
                "published": self._get_text(entry, "atom:published", ns),
                "updated": self._get_text(entry, "atom:updated", ns),
                "authors": [author.find("atom:name", ns).text for author in entry.findall("atom:author", ns)],
                "arxiv_url": self._get_link(entry, "alternate", ns),
                "pdf_url": self._get_link(entry, "related", ns),
                "comment": self._get_text(entry, "arxiv:comment", ns),
                "journal_ref": self._get_text(entry, "arxiv:journal_ref", ns),
                "primary_category": self._get_category(entry, ns),
                "categories": [cat.get("term") for cat in entry.findall("atom:category", ns)],
            }
            papers.append(paper)
        return papers

    def _get_text(self, element: Element, path: str, ns: dict) -> Optional[str]:
        el = element.find(path, ns)
        return el.text.strip() if el is not None and el.text else None

    def _get_link(self, element: Element, rel: str, ns: dict) -> Optional[str]:
        for link in element.findall("atom:link", ns):
            if link.get("rel") == rel:
                return link.get("href")
        return None

    def _get_category(self, element: Element, ns: dict) -> Optional[str]:
        cat = element.find("arxiv:primary_category", ns)
        return cat.get("term") if cat is not None else None
