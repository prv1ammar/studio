import json
import os
import shutil
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

class NodeOrganizerSystem:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        
        # Paths
        self.source_nodes = os.path.join(root_dir, "backend", "app", "nodes", "Node System")
        self.source_icons = os.path.join(root_dir, "studio", "icons nodes")
        self.dest_nodes = os.path.join(root_dir, "backend", "app", "nodes")
        self.dest_icons = os.path.join(root_dir, "studio", "public", "assets", "icons", "imported")
        
        self.org_file = os.path.join(root_dir, "studio", "langflow_organization.json")
        self.output_library = os.path.join(root_dir, "backend", "data", "node_library.json")
        
        self.scraped_index_path = os.path.join(self.dest_nodes, "component_index.json")

        # Lucide Fallback
        self.lucide_mapping = self._load_lucide_mapping()
        self.org_mapping = self._load_org_mapping()

    def _load_lucide_mapping(self) -> Dict[str, str]:
        # Minimal fallback if SVG missing
        return {
            "OpenAI": "Bot", "Anthropic": "Brain", "Google": "Globe", "Mistral": "Wind",
            "Tool": "Wrench", "Agent": "Bot", "Chain": "Link", "Memory": "Brain",
            "Embeddings": "Layers", "VectorStore": "Database", "Retriever": "Search",
            "Document": "FileText", "Loader": "Download",
        }

    def _load_org_mapping(self) -> Dict[str, str]:
        """Load langflow_organization.json to map Node Name -> Icon Name"""
        mapping = {}
        if os.path.exists(self.org_file):
            try:
                with open(self.org_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Data is { "Category": [ { "name": "NodeName", "icon": "IconName" } ] }
                    for cat, items in data.items():
                        for item in items:
                            # Map NodeName to IconName
                            # Also Composite Key? category_node
                            mapping[item['name']] = item.get('icon')
            except Exception as e:
                print(f"Error loading organization file: {e}")
        return mapping

    def organize_files(self):
        """Copies nodes and icons to their respective destinations."""
        print("📂 ORGANIZING FILES...")
        
        # 1. Copy Nodes
        if os.path.exists(self.source_nodes):
            print(f"   Copying Nodes from {self.source_nodes} to {self.dest_nodes}")
            shutil.copytree(self.source_nodes, self.dest_nodes, dirs_exist_ok=True)
        else:
            print("   ⚠️ Source 'Node System' not found. Assuming files already in place.")

        # 2. Copy and Normalize Icons
        if os.path.exists(self.source_icons):
            print(f"   Normalizing & Copying Icons to {self.dest_icons}")
            if os.path.exists(self.dest_icons):
                shutil.rmtree(self.dest_icons)
            os.makedirs(self.dest_icons, exist_ok=True)
            for cat_dir in os.listdir(self.source_icons):
                src_cat_path = os.path.join(self.source_icons, cat_dir)
                if not os.path.isdir(src_cat_path): continue
                
                # Normalize category name
                dest_cat_name = cat_dir.lower().replace(" ", "_")
                dest_cat_path = os.path.join(self.dest_icons, dest_cat_name)
                os.makedirs(dest_cat_path, exist_ok=True)
                
                for icon_file in os.listdir(src_cat_path):
                    if not icon_file.endswith(".svg"): continue
                    src_icon_path = os.path.join(src_cat_path, icon_file)
                    # Normalize icon name
                    base_name = icon_file.replace(".svg", "").lower()
                    clean_name = "".join(c if (c.isalnum() or c==" ") else "" for c in base_name)
                    dest_icon_name = clean_name.strip().replace(" ", "_") + ".svg"
                    dest_icon_path = os.path.join(dest_cat_path, dest_icon_name)
                    
                    # --- REPAIR/REPLACE LOGIC ---
                    replaces = {
                        "amazon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M18.72 15.11c-2.4 1.76-5.73 2.71-8.38 2.71-3.87 0-7.38-1.3-10.35-3.56-.3-.23-.33-.52-.05-.71.28-.19.69-.19.98.02 2.65 1.96 5.86 3.1 9.42 3.1 2.73 0 5.61-.82 7.84-2.43.3-.23.69-.02.59.32-.1.35-.25.55-.5.72s-.41.34-.41.34zm.35-1.07c-.09-.54.06-1.07.41-1.5.11-.11.28-.11.39 0 .54.54.74 1.36.52 2.08-.05.15-.22.22-.35.14l-.73-.46c-.15-.09-.21-.24-.24-.26zm2.25-.97c-.22-.16-.57-.16-.75.07-.27.33-.44.72-.51 1.14-.04.26.15.5.41.53.9.12 1.95.88 2.59 1.42.17.14.41.13.56-.02.17-.17.17-.44 0-.62-.64-.69-2.08-1.58-2.59-1.58l.3-2.51z"/></svg>""",
                        "azure": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13.041 3.539l-4.524 12.356H15.6l2.152 4.566H2.4l7.46-13.633L13.041 3.539zm2.46-.001L21.6 15.895l.001 4.566h-4.047l-2.053-4.566H8.517l7.001-12.357-1.1-0.001z"/></svg>""",
                        "redis": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 6.5v11L12 22l10-4.5v-11L12 2zm0 17.5l-7-3.15V8.65l7 3.15 7-3.15v6.7l-7 3.15z"/></svg>""",
                        "cohere": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 4c4.418 0 8 3.582 8 8s-3.582 8-8 8-8-3.582-8-8 3.582-8 8-8zm-2 10h4v2h-4v-2zm0-4h4v2h-4v-2z"/></svg>""",
                        "cleanlab": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8zm-4-9h2v2H8v-2zm6 0h2v2h-2v-2z"/></svg>"""
                    }

                    if dest_cat_name in replaces:
                        with open(dest_icon_path, 'w', encoding='utf-8') as f:
                            f.write(replaces[dest_cat_name])
                    else:
                        with open(src_icon_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # General Repairs
                        # A. Missing Gradient definitions
                        if 'fill="url(#' in content and '<defs>' not in content:
                            content = re.sub(r'fill="url\(#[^"]+\)"', 'fill="currentColor"', content)
                        
                        # B. Large Viewbox / Tiny Stroke
                        viewbox_match = re.search(r'viewBox="([^"]+)"', content)
                        if viewbox_match and 'stroke-width="2"' in content:
                            try:
                                vb = [float(x) for x in viewbox_match.group(1).split()]
                                if vb[2] > 100:
                                    content = content.replace('stroke-width="2"', f'stroke-width="{vb[2]/24:.1f}"')
                            except: pass
                            
                        # C. Garbage data
                        if re.search(r'd="[a-z0-9]{8,15}"', content):
                            content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>'

                        with open(dest_icon_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                # --- END REPAIR LOGIC ---
        else:
            print("   ⚠️ Source 'icons nodes' not found.")

    def resolve_icon(self, category: str, node_name: str, node_label: str, defined_icon: str) -> str:
        """
        Returns the final icon string.
        1. Checks if SVG exists in assets (Best).
        2. Checks Lucide map (Fallback).
        3. Returns 'Box' (Default).
        """
        # 1. Check Custom SVG
        # Filename candidates: Label, DefinedIcon, NodeName
        raw_label = node_label.strip()
        clean_label = "".join(c if c.isalnum() else " " for c in raw_label).strip() # Replace '/' etc with space
        
        candidates = [
            raw_label,
            clean_label,
            raw_label.replace(" Tool", ""),
            raw_label.replace(" Component", ""),
            defined_icon,
            node_name,
            defined_icon.replace(" ", ""),
            "".join(raw_label.split()), # Remove all spaces
        ]
        if node_name == "HCD":
            candidates.extend(["hyperconverged_database", "hyper_converged_database"])
        
        # Remove duplicates
        seen = set()
        candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
        
        base_icon_dir = os.path.join(self.root_dir, "studio", "public", "assets", "icons", "imported")
        
        # Helper for fuzzy file matching
        def fuzzy_match_in_dir(path: str, cands: List[str], cat_name: str) -> Optional[str]:
            if not os.path.exists(path): return None
            try:
                files_in_cat = os.listdir(path)
                # We expect normalized filenames here (lowercase, underscores)
                norm_files = {f.lower(): f for f in files_in_cat if f.endswith('.svg')}
                
                def norm(s):
                    # Lower, remove non-alnum, then replace spaces/underscores with single underscore
                    s = s.lower().replace(".svg", "")
                    s = "".join(c if (c.isalnum() or c==" ") else " " for c in s)
                    return "_".join(s.split())

                for cand in cands:
                    cand_norm = norm(cand)
                    if not cand_norm: continue
                    
                    if (cand_norm + ".svg") in norm_files:
                        return f"/assets/icons/imported/{cat_name}/{norm_files[cand_norm + '.svg']}"
                    
                    # Fuzzy match - does normalized cand exist within any normalized filename?
                    for fn in norm_files:
                        fn_norm = norm(fn)
                        # Direct inclusion
                        if cand_norm in fn_norm or fn_norm in cand_norm:
                            return f"/assets/icons/imported/{cat_name}/{norm_files[fn]}"
                        
                        # Initials check (e.g. HCD matches hyper_converged_database)
                        parts = fn_norm.split("_")
                        initials = "".join(p[0] for p in parts if p)
                        if cand_norm == initials:
                            return f"/assets/icons/imported/{cat_name}/{norm_files[fn]}"
            except Exception: pass
            return None

        # Try Category First
        # Category folder on disk is already normalized (lowercase, underscore)
        cat_clean = category.lower().replace(" ", "_")
        cat_path = os.path.join(base_icon_dir, cat_clean)
        match = fuzzy_match_in_dir(cat_path, candidates, cat_clean)
        if match:
            return match

        # GLOBAL SEARCH
        if os.path.exists(base_icon_dir):
            for cat_dir in os.listdir(base_icon_dir):
                if cat_dir == cat_clean: continue
                match = fuzzy_match_in_dir(os.path.join(base_icon_dir, cat_dir), candidates, cat_dir)
                if match:
                    return match
        
        # 2. Fallback to Lucide
        return self.lucide_mapping.get(defined_icon, "Box")

    def convert_input_field(self, field_name: str, field_data: Dict) -> Optional[Dict]:
        """Convert input field to Tyboo format"""
        if field_name in ["code", "_type"] or not field_data.get("show", True):
            return None
        
        input_type = field_data.get("_input_type", "StrInput")
        type_mapping = {
            "StrInput": "text", "MessageTextInput": "text", "MultilineInput": "textarea",
            "IntInput": "number", "FloatInput": "number", "BoolInput": "boolean",
            "SecretStrInput": "password", "DropdownInput": "dropdown",
            "HandleInput": "handle", "DictInput": "json", "FileInput": "file",
        }
        
        return {
            "name": field_name,
            "display_name": field_data.get("display_name", field_name),
            "type": type_mapping.get(input_type, "text"),
            "required": field_data.get("required", False),
            "description": field_data.get("info", ""),
            "default": field_data.get("value"),
            "options": field_data.get("options", []) if input_type == "DropdownInput" else None,
            "advanced": field_data.get("advanced", False),
        }

    def convert_node(self, node_name: str, node_data: Dict, category: str) -> Dict:
        # Use Organization overrides if available
        org_icon = self.org_mapping.get(node_name)
        defined_icon = node_data.get("icon", org_icon or "Box")
        
        node_label = node_data.get("display_name", node_name)

        # Resolve final icon (SVG URL or Lucide Name)
        final_icon = self.resolve_icon(category, node_name, node_label, defined_icon)
        
        # Extract inputs/outputs
        template = node_data.get("template", {})
        inputs = []
        for fn, fd in template.items():
            if isinstance(fd, dict):
                conv = self.convert_input_field(fn, fd)
                if conv: inputs.append(conv)
                
        outputs = []
        for out in node_data.get("outputs", []):
            outputs.append({
                "name": out.get("name"), 
                "display_name": out.get("display_name", out.get("name")), 
                "types": out.get("types", [])
            })

        return {
            "id": f"{category.lower().replace(' ', '_')}_{node_name}",
            "name": node_name,
            "label": node_data.get("display_name", node_name),
            "description": node_data.get("description", ""),
            "category": category,
            "icon": final_icon,
            "color": "#6b7280", # Default color
            "inputs": inputs,
            "outputs": outputs,
            "base_classes": node_data.get("base_classes", []),
            "beta": node_data.get("beta", False),
            "documentation": node_data.get("documentation", ""),
        }

    def extract_category_from_module(self, module_path: str) -> str:
        if not module_path: return "Other"
        parts = module_path.split(".")
        if len(parts) >= 3:
            category = parts[2]
            return category.replace("_", " ").title()
        return "Other"

    def process_category(self, category_name: str, category_data: Dict) -> List[Dict]:
        nodes = []
        for node_name, node_data in category_data.items():
            try:
                module_path = node_data.get("metadata", {}).get("module", "")
                # category = self.extract_category_from_module(module_path) 
                # Actually, use the key from index as Category usually matches better
                category = category_name.title()
                
                node = self.convert_node(node_name, node_data, category)
                nodes.append(node)
            except Exception as e:
                print(f"Error converting {node_name}: {e}")
        return nodes

    def get_tyboo_nodes(self) -> List[Dict]:
        """Manually defined Tyboo company-specific nodes"""
        return [
            {
                "id": "liteLLM",
                "name": "LiteLLM",
                "label": "Lite LLM (Tybot)",
                "description": "High-performance company-specific LLM router.",
                "category": "Tyboo",
                "icon": "Cpu",
                "color": "#ec4899",
                "inputs": [
                    {"name": "input_data", "display_name": "Input Text", "type": "handle", "required": True},
                    {"name": "api_key", "display_name": "API Key", "type": "password", "required": True, "default": "sk-RVApjtnPznKZ4UXosZYEOQ"},
                    {"name": "base_url", "display_name": "Base URL", "type": "text", "default": "https://toknroutertybot.tybotflow.com/"},
                    {"name": "model_name", "display_name": "Model Name", "type": "text", "default": "gpt-4.1-mini"},
                    {"name": "temperature", "display_name": "Temperature", "type": "number", "default": 0.1}
                ],
                "outputs": [{"name": "response", "display_name": "Assistant Response", "types": ["Text"]}]
            },
            {
                "id": "langchainAgent",
                "name": "LangChainAgent",
                "label": "Configurable Agent (LangChain)",
                "description": "Powerful agent that composes LLM, Tools, and Memory from its inputs.",
                "category": "Tyboo",
                "icon": "Zap",
                "color": "#f59e0b",
                "inputs": [
                    {"name": "input_data", "display_name": "User Question", "type": "handle", "required": True},
                    {"name": "system_prompt", "display_name": "System Prompt", "type": "textarea", "default": "You are a helpful assistant."},
                    {"name": "llm", "display_name": "LLM Provider", "type": "handle", "info": "Connect an LLM node (e.g., LiteLLM)."},
                    {"name": "tools", "display_name": "Tools", "type": "handle", "info": "Connect Tool nodes (e.g., SmartDB)."},
                ],
                "outputs": [{"name": "output", "display_name": "Agent Response", "types": ["Text"]}]
            },
            {
                "id": "liteEmbedding",
                "name": "LiteEmbedding",
                "label": "Tyboo Embedding",
                "description": "Proprietary vector embedding model for semantic search.",
                "category": "Tyboo",
                "icon": "Layers",
                "color": "#8b5cf6",
                "inputs": [
                    {"name": "input_data", "display_name": "Text to Embed", "type": "handle", "required": True},
                    {"name": "api_key", "display_name": "API Key", "type": "password", "required": True, "default": "sk-RVApjtnPznKZ4UXosZYEOQ"},
                    {"name": "base_url", "display_name": "Base URL", "type": "text", "default": "https://toknroutertybot.tybotflow.com/"},
                    {"name": "model_name", "display_name": "Embedding Model", "type": "text", "default": "text-embedding-3-small"}
                ],
                "outputs": [{"name": "embeddings", "display_name": "Vector Embeddings", "types": ["Vector"]}]
            },
            {
                "id": "smartDB",
                "name": "SmartDB",
                "label": "SmartDB (NocoDB)",
                "description": "Connect to your NocoDB instance with automated schema discovery.",
                "category": "Tyboo",
                "icon": "Database",
                "color": "#10b981",
                "inputs": [
                    {"name": "input_data", "display_name": "Operation Data", "type": "handle", "required": False},
                    {"name": "base_url", "display_name": "NocoDB URL", "type": "text", "placeholder": "https://nocodb.yourcompany.com"},
                    {"name": "api_key", "display_name": "API Key", "type": "password"},
                    {"name": "project_id", "display_name": "Select Database", "type": "dropdown", "options": []},
                    {"name": "table_id", "display_name": "Select Table", "type": "dropdown", "options": []},
                    {"name": "operations", "display_name": "Operations", "type": "dropdown", "options": ["Create", "Read", "Update", "Delete", "All"]}
                ],
                "outputs": [{"name": "result", "display_name": "Query Result", "types": ["Any"]}]
            }
        ]

    def get_essentials(self) -> List[Dict]:
        return [
            {
                "id": "chatInput",
                "name": "ChatInput",
                "label": "Chat Input",
                "description": "Starting point for user messages.",
                "category": "Essentials",
                "icon": "MessageSquare",
                "color": "#4f46e5",
                "inputs": [],
                "outputs": [{"name": "message", "display_name": "User Message", "types": ["Text"]}]
            },
            {
                "id": "memoryNode",
                "name": "MemoryNode",
                "label": "Conversation Memory",
                "description": "Configurable memory with Redis, in-memory, or windowed storage.",
                "category": "Essentials",
                "icon": "History",
                "color": "#6366f1",
                "inputs": [
                    {
                        "name": "backend",
                        "display_name": "Memory Backend",
                        "type": "dropdown",
                        "options": ["in_memory", "redis", "windowed"],
                        "default": "in_memory",
                        "info": "Choose the storage backend for conversation history."
                    },
                    {
                        "name": "redis_url",
                        "display_name": "Redis URL",
                        "type": "text",
                        "default": "redis://localhost:6379/0",
                        "info": "Redis connection URL (only for Redis backend).",
                        "show_if": {"backend": "redis"}
                    },
                    {
                        "name": "session_id",
                        "display_name": "Session ID",
                        "type": "text",
                        "default": "default_session",
                        "info": "Unique session identifier for memory isolation.",
                        "show_if": {"backend": "redis"}
                    },
                    {
                        "name": "ttl",
                        "display_name": "TTL (seconds)",
                        "type": "number",
                        "info": "Optional: Time-to-live for Redis keys.",
                        "show_if": {"backend": "redis"}
                    },
                    {
                        "name": "window_size",
                        "display_name": "Window Size",
                        "type": "number",
                        "default": 10,
                        "info": "Number of recent messages to keep (windowed backend only).",
                        "show_if": {"backend": "windowed"}
                    }
                ],
                "outputs": [{"name": "memory", "display_name": "Memory Object", "types": ["Memory"]}]
            },
            {
                "id": "chatOutput",
                "name": "ChatOutput",
                "label": "Chat Output",
                "description": "Final response display.",
                "category": "Essentials",
                "icon": "LogOut",
                "color": "#4f46e5",
                "inputs": [{"name": "message", "display_name": "Response Text", "type": "handle", "required": True}],
                "outputs": []
            }
        ]

    def migrate_library(self):
        print("🔄 MIGRATING LIBRARY...")
        
        if not os.path.exists(self.scraped_index_path):
            print(f"❌ Index not found at {self.scraped_index_path}")
            return

        with open(self.scraped_index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        entries = data.get("entries", []) # List of [category, dict]
        all_nodes = {}
        
        # 1. Inject Top Categories
        all_nodes["Tyboo"] = self.get_tyboo_nodes()
        all_nodes["Essentials"] = self.get_essentials()

        for category_name, category_data in entries:
            nodes = self.process_category(category_name, category_data)
            if nodes:
                # Group by actual category
                for node in nodes:
                    # Skip if already in Essentials (keep it clean)
                    if node["label"] in ["Chat Input", "Chat Output"] and node["category"] == "Input_Output":
                        continue
                        
                    cat = node["category"]
                    if cat not in all_nodes: all_nodes[cat] = []
                    all_nodes[cat].append(node)
        
        # Save
        with open(self.output_library, 'w', encoding='utf-8') as f:
            json.dump(all_nodes, f, indent=2)
            
        print(f"✅ Saved {sum(len(v) for v in all_nodes.values())} nodes to Library.")

if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    system = NodeOrganizerSystem(root_dir)
    system.organize_files()
    system.migrate_library()
