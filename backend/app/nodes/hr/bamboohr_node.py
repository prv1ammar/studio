"""
BambooHR Node - Studio Standard
Batch 64: HR & Recruiting
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("bamboohr_node")
class BambooHRNode(BaseNode):
    """
    Automate HR administration and employee records via BambooHR API.
    """
    node_type = "bamboohr_node"
    version = "1.0.0"
    category = "hr"
    credentials_required = ["bamboohr_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_employee_directory',
            'options': [
                {'name': 'Get Employee Directory', 'value': 'get_employee_directory'},
                {'name': 'Get Employee', 'value': 'get_employee'},
                {'name': 'Get Time Off Requests', 'value': 'get_time_off_requests'},
                {'name': 'Get Company Report', 'value': 'get_company_report'},
            ],
            'description': 'BambooHR action to perform',
        },
        {
            'displayName': 'Employee Id',
            'name': 'employee_id',
            'type': 'string',
            'default': '',
            'description': 'ID of the specific employee',
        },
        {
            'displayName': 'Subdomain',
            'name': 'subdomain',
            'type': 'string',
            'default': '',
            'description': 'Your BambooHR subdomain (e.g. 'company' in company.bamboohr.com)',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_employee_directory",
            "options": ["get_employee_directory", "get_employee", "get_time_off_requests", "get_company_report"],
            "description": "BambooHR action to perform"
        },
        "subdomain": {
            "type": "string",
            "required": True,
            "description": "Your BambooHR subdomain (e.g. 'company' in company.bamboohr.com)"
        },
        "employee_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the specific employee"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("bamboohr_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            subdomain = self.get_config("subdomain")
            
            if not api_key or not subdomain:
                return {"status": "error", "error": "BambooHR API Key and Subdomain are required."}

            # BambooHR uses Basic Auth with api_key as username and "x" as password
            auth_str = f"{api_key}:x"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json"
            }
            
            base_url = f"https://api.bamboohr.com/api/gateway.php/{subdomain}/v1"
            action = self.get_config("action", "get_employee_directory")

            async with aiohttp.ClientSession() as session:
                if action == "get_employee_directory":
                    url = f"{base_url}/employees/directory"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        employees = res_data.get("employees", [])
                        return {"status": "success", "data": {"result": employees, "count": len(employees)}}

                elif action == "get_employee":
                    employee_id = self.get_config("employee_id") or str(input_data)
                    # For get_employee, we need to specify fields
                    fields = "firstName,lastName,workEmail,jobTitle,department"
                    url = f"{base_url}/employees/{employee_id}/?fields={fields}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_time_off_requests":
                    url = f"{base_url}/time_off/requests/"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                return {"status": "error", "error": f"Unsupported BambooHR action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"BambooHR Node Failed: {str(e)}"}