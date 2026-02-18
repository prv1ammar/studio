"""
Item Lists Node - Studio Standard (Universal Method)
Batch 103: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("item_lists_node")
class ItemListsNode(BaseNode):
    """
    Split and aggregate lists of items in workflows.
    """
    node_type = "item_lists_node"
    version = "1.0.0"
    category = "flow_controls"
    credentials_required = []


    properties = [
        {
            'displayName': 'Field To Split',
            'name': 'field_to_split',
            'type': 'string',
            'default': '',
            'description': 'Field containing array to split (for split_out)',
        },
        {
            'displayName': 'Limit',
            'name': 'limit',
            'type': 'string',
            'default': '',
            'description': 'Maximum number of items to keep',
        },
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'split_out',
            'options': [
                {'name': 'Split Out', 'value': 'split_out'},
                {'name': 'Aggregate', 'value': 'aggregate'},
                {'name': 'Remove Duplicates', 'value': 'remove_duplicates'},
                {'name': 'Sort', 'value': 'sort'},
                {'name': 'Limit', 'value': 'limit'},
                {'name': 'Summarize', 'value': 'summarize'},
            ],
            'description': 'List operation to perform',
        },
        {
            'displayName': 'Sort Field',
            'name': 'sort_field',
            'type': 'string',
            'default': '',
            'description': 'Field to sort by',
        },
        {
            'displayName': 'Sort Order',
            'name': 'sort_order',
            'type': 'options',
            'default': 'asc',
            'options': [
                {'name': 'Asc', 'value': 'asc'},
                {'name': 'Desc', 'value': 'desc'},
            ],
        },
        {
            'displayName': 'Unique Field',
            'name': 'unique_field',
            'type': 'string',
            'default': '',
            'description': 'Field to check for duplicates',
        },
    ]
    inputs = {
        "operation": {
            "type": "dropdown",
            "default": "split_out",
            "options": ["split_out", "aggregate", "remove_duplicates", "sort", "limit", "summarize"],
            "description": "List operation to perform"
        },
        "field_to_split": {
            "type": "string",
            "optional": True,
            "description": "Field containing array to split (for split_out)"
        },
        "sort_field": {
            "type": "string",
            "optional": True,
            "description": "Field to sort by"
        },
        "sort_order": {
            "type": "dropdown",
            "default": "asc",
            "options": ["asc", "desc"],
            "optional": True
        },
        "limit": {
            "type": "number",
            "optional": True,
            "description": "Maximum number of items to keep"
        },
        "unique_field": {
            "type": "string",
            "optional": True,
            "description": "Field to check for duplicates"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "list_info": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            operation = self.get_config("operation", "split_out")
            
            # Get input items
            if isinstance(input_data, list):
                items = input_data
            else:
                items = [input_data] if input_data else []
            
            if operation == "split_out":
                # Split array field into separate items
                field = self.get_config("field_to_split")
                
                if not field:
                    return {"status": "error", "error": "field_to_split required for split_out operation"}
                
                result = []
                for item in items:
                    if isinstance(item, dict) and field in item:
                        array_value = item[field]
                        if isinstance(array_value, list):
                            # Create new item for each array element
                            for element in array_value:
                                new_item = dict(item)
                                new_item[field] = element
                                result.append(new_item)
                        else:
                            result.append(item)
                    else:
                        result.append(item)
                
                return {
                    "status": "success",
                    "data": {
                        "result": result,
                        "list_info": {
                            "operation": "split_out",
                            "input_count": len(items),
                            "output_count": len(result)
                        }
                    }
                }
            
            elif operation == "aggregate":
                # Combine all items into a single item with an array
                return {
                    "status": "success",
                    "data": {
                        "result": [{"items": items, "count": len(items)}],
                        "list_info": {
                            "operation": "aggregate",
                            "aggregated_count": len(items)
                        }
                    }
                }
            
            elif operation == "remove_duplicates":
                # Remove duplicate items
                unique_field = self.get_config("unique_field")
                
                if unique_field:
                    # Remove duplicates based on specific field
                    seen = set()
                    result = []
                    for item in items:
                        if isinstance(item, dict):
                            value = item.get(unique_field)
                            if value not in seen:
                                seen.add(value)
                                result.append(item)
                        else:
                            if item not in seen:
                                seen.add(item)
                                result.append(item)
                else:
                    # Remove exact duplicates
                    result = []
                    seen = []
                    for item in items:
                        if item not in seen:
                            seen.append(item)
                            result.append(item)
                
                return {
                    "status": "success",
                    "data": {
                        "result": result,
                        "list_info": {
                            "operation": "remove_duplicates",
                            "input_count": len(items),
                            "output_count": len(result),
                            "removed_count": len(items) - len(result)
                        }
                    }
                }
            
            elif operation == "sort":
                # Sort items
                sort_field = self.get_config("sort_field")
                sort_order = self.get_config("sort_order", "asc")
                
                if sort_field:
                    # Sort by specific field
                    result = sorted(
                        items,
                        key=lambda x: x.get(sort_field, "") if isinstance(x, dict) else x,
                        reverse=(sort_order == "desc")
                    )
                else:
                    # Sort items directly
                    result = sorted(items, reverse=(sort_order == "desc"))
                
                return {
                    "status": "success",
                    "data": {
                        "result": result,
                        "list_info": {
                            "operation": "sort",
                            "sort_field": sort_field,
                            "sort_order": sort_order,
                            "count": len(result)
                        }
                    }
                }
            
            elif operation == "limit":
                # Limit number of items
                limit = int(self.get_config("limit", 10))
                result = items[:limit]
                
                return {
                    "status": "success",
                    "data": {
                        "result": result,
                        "list_info": {
                            "operation": "limit",
                            "input_count": len(items),
                            "output_count": len(result),
                            "limit": limit
                        }
                    }
                }
            
            elif operation == "summarize":
                # Provide summary statistics
                summary = {
                    "total_items": len(items),
                    "first_item": items[0] if items else None,
                    "last_item": items[-1] if items else None
                }
                
                # If items are dicts, count unique values per field
                if items and isinstance(items[0], dict):
                    field_stats = {}
                    for key in items[0].keys():
                        values = [item.get(key) for item in items if isinstance(item, dict)]
                        field_stats[key] = {
                            "unique_count": len(set(str(v) for v in values)),
                            "null_count": sum(1 for v in values if v is None)
                        }
                    summary["field_statistics"] = field_stats
                
                return {
                    "status": "success",
                    "data": {
                        "result": [summary],
                        "list_info": {
                            "operation": "summarize",
                            "summary": summary
                        }
                    }
                }
            
            return {"status": "error", "error": f"Unsupported operation: {operation}"}

        except Exception as e:
            return {"status": "error", "error": f"Item Lists Node Failed: {str(e)}"}