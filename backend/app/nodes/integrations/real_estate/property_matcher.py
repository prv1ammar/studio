from typing import Any, Dict, Optional, List
from ...base import BaseNode
import json

class PropertyMatcherNode(BaseNode):
    """
    Searches for matching properties in Smart DB and Supabase.
    Combines SQL filtering with semantic search.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract search criteria
        location = None
        budget_max = None
        bedrooms = None
        property_type = None
        
        if isinstance(input_data, dict):
            location = input_data.get("location")
            budget_max = input_data.get("budget_max")
            bedrooms = input_data.get("bedrooms")
            property_type = input_data.get("property_type")
        
        # Fallback to config
        if not location:
            location = self.config.get("location")
        if not budget_max:
            budget_max = self.config.get("budget_max")
        if not bedrooms:
            bedrooms = self.config.get("bedrooms")
        if not property_type:
            property_type = self.config.get("property_type")
        
        matches = []
        
        # 1. Query Smart DB (if configured in context)
        if context and 'graph_data' in context:
            graph_data = context['graph_data']
            node_id = context['node_id']
            edges = graph_data.get('edges', [])
            nodes = graph_data.get('nodes', [])
            engine = context.get('engine')
            
            # Find Smart DB node connected to this node
            smartdb_edge = next((e for e in edges if e['target'] == node_id and 
                               any(n['id'] == e['source'] and n.get('data', {}).get('id') == 'smartDBNode' 
                                   for n in nodes)), None)
            
            if smartdb_edge and engine:
                source_id = smartdb_edge['source']
                source_node = next((n for n in nodes if n['id'] == source_id), None)
                
                if source_node:
                    # Build query filters
                    query_data = {}
                    
                    # Build WHERE clause
                    where_conditions = []
                    if location:
                        where_conditions.append(f"(location LIKE '%{location}%')")
                    if budget_max:
                        where_conditions.append(f"(price <= {budget_max})")
                    if bedrooms:
                        where_conditions.append(f"(bedrooms >= {bedrooms})")
                    if property_type:
                        where_conditions.append(f"(property_type = '{property_type}')")
                    
                    if where_conditions:
                        query_data["where"] = " AND ".join(where_conditions)
                    
                    query_data["limit"] = 10
                    query_data["sort"] = ["-created_at"]  # Most recent first
                    
                    try:
                        # Execute Smart DB query
                        db_result = await engine.execute_node(
                            'smartDBNode',
                            query_data,
                            config=source_node['data'],
                            context={**context, 'node_id': source_id}
                        )
                        
                        # Parse result
                        if isinstance(db_result, dict) and 'list' in db_result:
                            matches.extend(db_result['list'])
                        elif isinstance(db_result, list):
                            matches.extend(db_result)
                    except Exception as e:
                        print(f"Smart DB query error: {e}")
        
        # 2. Query Supabase for semantic search (if configured)
        if context and 'graph_data' in context:
            graph_data = context['graph_data']
            node_id = context['node_id']
            edges = graph_data.get('edges', [])
            nodes = graph_data.get('nodes', [])
            engine = context.get('engine')
            
            # Find Supabase node connected to this node
            supabase_edge = next((e for e in edges if e['target'] == node_id and 
                                any(n['id'] == e['source'] and n.get('data', {}).get('id') == 'supabaseStoreNode' 
                                    for n in nodes)), None)
            
            if supabase_edge and engine:
                source_id = supabase_edge['source']
                source_node = next((n for n in nodes if n['id'] == source_id), None)
                
                if source_node:
                    # Build semantic search query
                    search_query = f"{property_type or 'Appartement'} à {location or 'Casablanca'}"
                    if bedrooms:
                        search_query += f" {bedrooms} chambres"
                    if budget_max:
                        search_query += f" max {budget_max} DH"
                    
                    try:
                        # Get the Supabase tool
                        from ...factory import NodeFactory
                        factory = NodeFactory()
                        supabase_node = factory.get_node('supabaseStoreNode', source_node['data'])
                        supabase_tool = await supabase_node.get_langchain_object(context)
                        
                        if supabase_tool:
                            semantic_results = supabase_tool.func(search_query)
                            # Parse semantic results (they come as text)
                            # For now, just add them as a note
                            if semantic_results and not semantic_results.startswith("Error"):
                                # You could parse the results here
                                pass
                    except Exception as e:
                        print(f"Supabase search error: {e}")
        
        # 3. Rank and return results
        # Remove duplicates based on URL
        seen_urls = set()
        unique_matches = []
        for match in matches:
            url = match.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_matches.append(match)
        
        # Sort by relevance (price closest to budget)
        if budget_max and unique_matches:
            unique_matches.sort(key=lambda x: abs((x.get('price') or budget_max) - budget_max))
        
        return {
            "matches": unique_matches[:5],  # Return top 5
            "total_found": len(unique_matches),
            "search_criteria": {
                "location": location,
                "budget_max": budget_max,
                "bedrooms": bedrooms,
                "property_type": property_type
            },
            "status": "success"
        }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
