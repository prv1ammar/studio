import asyncio
import json
import os
from enum import Enum
from lfx.interface.listing import lazy_load_dict

class LangflowEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

async def extract():
    try:
        print("Extracting Langflow Component Dictionary...")
        data = await lazy_load_dict.get_type_dict()
        
        with open("backend/true_langflow_library.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=LangflowEncoder)
            
        print(f"Successfully extracted {len(data)} categories to backend/true_langflow_library.json")
    except Exception as e:
        import traceback
        print(f"Error during extraction: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(extract())
