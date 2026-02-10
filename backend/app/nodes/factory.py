import importlib
import os
import sys
from typing import Any, Dict, Optional, Type
from .base import BaseNode

# Ensure the backend directory is in path for dynamic imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Vendor path for imported libraries (langflow, lfx)
vendor_path = os.path.join(project_root, "backend", "vendor")
if vendor_path not in sys.path:
    sys.path.append(vendor_path)

NODE_MAP = {
    # Agents
    "faq_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "availability_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "booking_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "patient_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "orchestrator_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "configurable_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "router_node": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "mainAgent": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "langchainAgent": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "easySpaceAgent": "app.nodes.agents.easyspace.node.EasySpaceAgentNode",

    # Integrations - Batch 1
    "sageNode": "app.nodes.integrations.sage.sage.SageNode",
    "odooNode": "app.nodes.integrations.odoo.odoo.OdooNode",
    "dolibarrNode": "app.nodes.integrations.dolibarr.dolibarr.DolibarrNode",

    # Integrations - Batch 2 (CRM)
    "salesforceNode": "app.nodes.integrations.salesforce.salesforce.SalesforceNode",
    "hubspotNode": "app.nodes.integrations.hubspot.hubspot.HubSpotNode",
    "zohoNode": "app.nodes.integrations.zoho.zoho.ZohoNode",
    "sugarcrmNode": "app.nodes.integrations.sugarcrm.sugarcrm.SugarCRMNode",
    "vtigerNode": "app.nodes.integrations.vtiger.vtiger.VTigerNode",

    # Integrations - Batch 3 (Automation & Dev)
    "zapierNode": "app.nodes.integrations.zapier.zapier.ZapierNode",
    "githubNode": "app.nodes.integrations.github.github.GitHubNode",
    "gitlabNode": "app.nodes.integrations.gitlab.gitlab.GitLabNode",

    # Integrations - Batch 4 (Tools & Analytics)
    "trelloNode": "app.nodes.integrations.trello.trello.TrelloNode",
    "glpiNode": "app.nodes.integrations.glpi.glpi.GLPINode",
    "btrixNode": "app.nodes.integrations.btrix.btrix.BTRIXNode",
    "unicaNode": "app.nodes.integrations.unica.unica.UnicaNode",
    "transcriptionNode": "app.nodes.integrations.transcription.transcription.TranscriptionNode",
    "realEstateScraperNode": "app.nodes.integrations.scraping.real_estate_scraper.RealEstateScraperNode",
    
    # Real Estate AI Nodes
    "intentClassifierNode": "app.nodes.integrations.real_estate.intent_classifier.IntentClassifierNode",
    "propertyExtractorNode": "app.nodes.integrations.real_estate.property_extractor.PropertyExtractorNode",
    "leadFormatterNode": "app.nodes.integrations.real_estate.lead_formatter.LeadFormatterNode",
    "propertyMatcherNode": "app.nodes.integrations.real_estate.property_matcher.PropertyMatcherNode",
    "carouselBuilderNode": "app.nodes.integrations.real_estate.carousel_builder.CarouselBuilderNode",
    "notificationNode": "app.nodes.integrations.real_estate.notification.NotificationNode",
    "leadIngestorNode": "app.nodes.integrations.real_estate.lead_ingestor.LeadIngestorNode",
    "gmailNode": "app.nodes.google.gmail.GmailSendMessageNode",

    
    # Models
    "liteLLM": "app.nodes.models.litellm.litellm_node.LiteLLMNode",
    "liteEmbedding": "app.nodes.models.lite_embedding.lite_embedding_node.LiteEmbeddingNode",
    "openai_chat": "app.nodes.models.openai_node.OpenAINode",
    "anthropic_chat": "app.nodes.models.anthropic_node.AnthropicNode",
    "google_gemini": "app.nodes.models.google_node.GoogleNode",
    
    # Storage
    "supabaseStore": "app.nodes.storage.supabase.supabase_node.SupabaseStoreNode",
    "supabase_SupabaseVectorStore": "app.nodes.storage.supabase.supabase_node.SupabaseStoreNode",
    "smartDB": "app.nodes.storage.nocodb.nocodb_node.SmartDBNode",
    
    # Tools
    "fileNode": "app.nodes.tools.file_reader.file_reader_node.FileReaderNode",
    "files_and_knowledge_File": "app.nodes.tools.file_reader.file_reader_node.FileReaderNode",
    "docling_DoclingInline": "app.nodes.tools.docling.docling_node.DoclingNode",
    "docling_ChunkDoclingDocument": "app.nodes.tools.docling.chunk_node.ChunkDoclingNode",
    "processing_SplitText": "app.nodes.processing.split_node.SplitTextNode",
    "codeNode": "app.nodes.tools.code_executor.code_executor_node.CodeExecutorNode",
    
    # Core
    "chatInput": "app.nodes.core.chat_input.chat_input_node.ChatInputNode",
    "chatOutput": "app.nodes.core.chat_output.chat_output_node.ChatOutputNode",
    "memoryNode": "app.nodes.core.memory_node.MemoryNode",
    "chat_input": "app.nodes.core.chat_input.chat_input_node.ChatInputNode",
    "chat_output": "app.nodes.core.chat_output.chat_output_node.ChatOutputNode",
    "openai_openai": "app.nodes.models.openai_node.OpenAINode",
    "openai_OpenAI": "app.nodes.models.openai_node.OpenAINode",
    "anthropic_anthropic": "app.nodes.models.anthropic_node.AnthropicNode",
    "anthropic_Anthropic": "app.nodes.models.anthropic_node.AnthropicNode",
    "google_google_generative_ai": "app.nodes.models.google_node.GoogleNode",
    "input_output_chat_input": "app.nodes.core.chat_input.chat_input_node.ChatInputNode",
    "input_output_ChatInput": "app.nodes.core.chat_input.chat_input_node.ChatInputNode",
    "input_output_chat_output": "app.nodes.core.chat_output.chat_output_node.ChatOutputNode",
    "input_output_ChatOutput": "app.nodes.core.chat_output.chat_output_node.ChatOutputNode",
    
    # Missing RAG nodes
    "logic_RedisChatMemory": "app.nodes.core.memory_node.MemoryNode",
    "processing_ParseData": "app.nodes.processing.parse_node.ParseDataNode",
    "retrievers_SupabaseVectorStore": "app.nodes.storage.supabase.supabase_node.SupabaseStoreNode",
    "prompts_Prompt": "app.nodes.node_system.models_and_agents.prompt.PromptComponent",
    "models_and_agents_Prompt Template": "app.nodes.node_system.models_and_agents.prompt.PromptComponent",
    "prompt_Prompt": "app.nodes.node_system.models_and_agents.prompt.PromptComponent",
    
    # Flow Controls
    "flow_controls_ConditionalRouter": "app.nodes.flow_controls.router_node.RouterNode",
    "ConditionalRouter": "app.nodes.flow_controls.router_node.RouterNode",
}

from .registry import NodeRegistry

class NodeFactory:
    def __init__(self):
        # Trigger an initial scan when factory is created
        NodeRegistry.scan_and_register()

    @staticmethod
    def get_node(node_type: str, config: Dict[str, Any]) -> Optional[BaseNode]:
        # 1. Try Digital Registry (Dynamic Discovery)
        node_class = NodeRegistry.get_node_class(node_type)
        
        # 2. Fallback to Legacy Map
        if not node_class:
            node_path = NODE_MAP.get(node_type)
            if node_path:
                try:
                    module_path, class_name = node_path.rsplit(".", 1)
                    module = importlib.import_module(module_path)
                    node_class = getattr(module, class_name)
                    print(f"[NodeFactory]: Loaded '{node_type}' from Legacy Map. Please move to Registry.")
                except Exception as e:
                    print(f"NodeFactory Error: Failed to load mapped node '{node_type}': {e}")

        # 3. Instantiate if found
        if node_class:
            try:
                return node_class(config=config)
            except Exception as e:
                print(f"NodeFactory Error: Failed to instantiate {node_type}: {e}")

        # 4. Smart Auto-Discovery from Library
        try:
            lib_path = os.path.join(project_root, "backend", "data", "node_library.json")
            if os.path.exists(lib_path):
                import json
                with open(lib_path, "r", encoding="utf-8") as f:
                    library = json.load(f)
                
                # Find node info in library
                node_info = None
                for cat_nodes in library.values():
                    found = next((n for n in cat_nodes if n["id"] == node_type), None)
                    if found:
                        node_info = found
                        break
                
                if node_info:
                    category = node_info.get("category", "")
                    node_id = node_info.get("id", "")
                    
                    # Routing Logic based on Category or ID patterns
                    # 1. Models, Embeddings & Agents
                    if category in ["Models & AI Providers", "Aiml", "Assemblyai", "Twelvelabs", "AI Services & Agents"] or any(x in node_id.lower() for x in ["openai_", "anthropic_", "google_", "embedding", "transcription", "agent"]):
                        from .models.litellm.litellm_node import LiteLLMNode
                        print(f"[NodeFactory]: Auto-routing '{node_id}' ({category}) to LiteLLMNode")
                        return LiteLLMNode(config=config)
                    
                    # 2. API Integrations & Tools
                    if category in ["CRM Systems", "ERP & Accounting", "Productivity", "Dev Tools", "Search & Scraping", "Tools & Utilities", "Cloudflare", "Wolframalpha", "IoT & Home", "Prototypes", "Tools & Analytics"] or "composio" in node_id.lower() or "integration" in node_id.lower():
                        from .integrations.universal_api_node import UniversalAPIConnectorNode
                        print(f"[NodeFactory]: Auto-routing '{node_id}' ({category}) to UniversalAPIConnectorNode")
                        return UniversalAPIConnectorNode(config=config)

                    # 3. Vector Stores & Databases
                    if category in ["Vector Stores & Databases", "Data Sources", "Data & Knowledge"]:
                        if "memory" in node_id.lower():
                            from .core.memory_node import MemoryNode
                            print(f"[NodeFactory]: Auto-routing '{node_id}' to MemoryNode")
                            return MemoryNode(config=config)
                            
                        if "supabase" in node_id.lower() or "vector" in node_id.lower():
                            from .storage.supabase.supabase_node import SupabaseStoreNode
                            print(f"[NodeFactory]: Auto-routing '{node_id}' to SupabaseStoreNode")
                            return SupabaseStoreNode(config=config)
                        else:
                            from .storage.nocodb.nocodb_node import SmartDBNode
                            print(f"[NodeFactory]: Auto-routing '{node_id}' to SmartDBNode")
                            return SmartDBNode(config=config)
                            
                    # 4. Data Processing
                    if category == "Data Processing" or "formatter" in node_id.lower() or "parser" in node_id.lower():
                        if "extractor" in node_id.lower() or "classifier" in node_id.lower() or "matcher" in node_id.lower():
                            from .processing.ai_extractor import AIExtractorNode
                            print(f"[NodeFactory]: Auto-routing '{node_id}' to AIExtractorNode")
                            return AIExtractorNode(config=config)
                        
                    # 5. Logic & Flow
                    if category == "Logic & Flow" or category == "Input / Output":
                         from .generic_node import GenericNode
                         return GenericNode(node_type=node_type, config=config)

        except Exception as e:
            print(f"NodeFactory Auto-Discovery Error: {e}")

        # 5. Final Fallback to GenericNode
        try:
            from .generic_node import GenericNode
            print(f"[NodeFactory]: Node '{node_type}' not found in registry or auto-routing. Falling back to GenericNode.")
            return GenericNode(node_type=node_type, config=config)
        except Exception as e:
             print(f"NodeFactory Generic Fallback Error: {e}")
             return None
