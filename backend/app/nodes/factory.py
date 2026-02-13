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
    "webhook_trigger": "app.nodes.core.webhook_node.WebhookTriggerNode",
    "database_query": "app.nodes.storage.database_nodes.DatabaseQueryNode",
    "database_insert": "app.nodes.storage.database_nodes.DatabaseInsertNode",
    "database_update": "app.nodes.storage.database_nodes.DatabaseUpdateNode",
    "read_file": "app.nodes.core.file_nodes.ReadFileNode",
    "write_file": "app.nodes.core.file_nodes.WriteFileNode",
    "delete_file": "app.nodes.core.file_nodes.DeleteFileNode",
    "slack_message_send": "app.nodes.integrations.slack_node.SlackSendMessageNode",
    "slack_channel_read": "app.nodes.integrations.slack_node.SlackReadChannelNode",
    "discord_message_send": "app.nodes.integrations.discord_node.DiscordNode",
    "salesforce_record_create": "app.nodes.integrations.salesforce_node.SalesforceNode",
    "hubspot_crm_action": "app.nodes.integrations.hubspot_node.HubSpotNode",
    "json_query": "app.nodes.logic.json_nodes.JSONQueryNode",
    "json_transform": "app.nodes.logic.json_nodes.JSONTransformNode",
    "json_parse": "app.nodes.logic.json_nodes.JSONParseNode",
    "pdf_parser": "app.nodes.processing.pdf_node.PDFParserNode",
    "image_ocr": "app.nodes.integrations.image_ocr.ImageOCRNode",
    "text_formatter": "app.nodes.logic.format_nodes.TextFormatterNode",
    "date_formatter": "app.nodes.logic.format_nodes.DateFormatterNode",
    "math_operation": "app.nodes.logic.format_nodes.MathOperationNode",
    "gmail_send": "app.nodes.google.gmail.GmailSendMessageNode",
    "gmail_message_fetch": "app.nodes.google.gmail.GmailFetchMessagesNode",
    "twilio_sms_send": "app.nodes.communication.twilio_node.TwilioSMSNode",
    "whatsapp_message_send": "app.nodes.communication.whatsapp_node.WhatsAppNode",
    "email_smtp_send": "app.nodes.communication.smtp_node.SmtpEmailNode",
    "github_action": "app.nodes.integrations.github_node.GitHubNode",
    "jira_action": "app.nodes.integrations.jira_node.JiraNode",
    "trello_action": "app.nodes.integrations.trello_node.TrelloNode",
    "stripe_action": "app.nodes.integrations.stripe_node.StripeNode",
    "paypal_action": "app.nodes.integrations.paypal_node.PayPalNode",
    "telegram_send": "app.nodes.integrations.telegram_node.TelegramNode",
    "firecrawl_scrape": "app.nodes.integrations.scraping.firecrawl_nodes.FirecrawlScrapeNode",
    "firecrawl_crawl": "app.nodes.integrations.scraping.firecrawl_nodes.FirecrawlCrawlNode",
    "agentql_extract": "app.nodes.integrations.scraping.agentql_node.AgentQLNode",
    "instagram_scrape": "app.nodes.integrations.scraping.social_nodes.InstagramScrapeNode",
    "assemblyai_action": "app.nodes.integrations.media.assemblyai_node.AssemblyAINode",
    "elevenlabs_tts": "app.nodes.integrations.media.elevenlabs_node.ElevenLabsNode",
    "stability_image_gen": "app.nodes.integrations.media.stability_node.StabilityAINode",
    "universal_agent": "app.nodes.agents.universal_agent.UniversalAgentNode",
    "text_parser": "app.nodes.processing.parser.TextParserNode",
    "text_splitter": "app.nodes.processing.split_node.SplitTextNode",
    "regex_extract": "app.nodes.processing.regex.RegexNode",
    "ai_extractor": "app.nodes.processing.ai_extractor.AIExtractorNode",
    "tavily_search": "app.nodes.tavily.tavily_search.TavilySearchNode",
    "duckduckgo_search": "app.nodes.duckduckgo.duck_duck_go_search_run.DuckDuckGoSearchNode",
    "wikipedia_search": "app.nodes.wikipedia.wikipedia.WikipediaNode",
    "serpapi_search": "app.nodes.serpapi.serp.SerpApiNode",
    "openai_embeddings": "app.nodes.openai.openai.OpenAIEmbeddingsNode",
    "google_embeddings": "app.nodes.google.google_generative_ai_embeddings.GoogleEmbeddingsNode",
    "vertexai_embeddings": "app.nodes.vertexai.vertexai_embeddings.VertexAIEmbeddingsNode",
    "pinecone_vectorstore": "app.nodes.pinecone.pinecone.PineconeNode",
    "chroma_vectorstore": "app.nodes.chroma.chroma.ChromaNode",
    "hubspot_crm": "app.nodes.integrations.hubspot_node.HubSpotNode",
    "salesforce_crm": "app.nodes.integrations.salesforce_node.SalesforceNode",
    "pipedrive_crm": "app.nodes.integrations.pipedrive_node.PipedriveNode",
    "stripe_action": "app.nodes.integrations.stripe_node.StripeNode",
    "paypal_action": "app.nodes.integrations.paypal_node.PayPalNode",
    "quickbooks_node": "app.nodes.integrations.quickbooks_node.QuickbooksNode",
    "github_action": "app.nodes.integrations.github_node.GitHubNode",
    "gitlab_action": "app.nodes.integrations.gitlab_node.GitLabNode",
    "jira_action": "app.nodes.integrations.jira_node.JiraNode",
    "notion_action": "app.nodes.integrations.notion_node.NotionNode",
    "slack_action": "app.nodes.integrations.slack_node.SlackNode",
    "discord_action": "app.nodes.integrations.discord_node.DiscordNode",
    "telegram_action": "app.nodes.integrations.telegram_node.TelegramNode",
    "mailchimp_action": "app.nodes.integrations.mailchimp_node.MailchimpNode",
    "airtable_action": "app.nodes.storage.airtable_node.AirtableNode",
    "google_sheets_action": "app.nodes.google.google_sheets.GoogleSheetsNode",
    "supabase_action": "app.nodes.storage.supabase.supabase_node.SupabaseActionNode",
    "youtube_action": "app.nodes.google.youtube.YouTubeNode",
    "twitter_action": "app.nodes.social.twitter.TwitterNode",
    "assemblyai_action": "app.nodes.integrations.media.assemblyai_node.AssemblyAINode",
    "elevenlabs_tts": "app.nodes.integrations.media.elevenlabs_node.ElevenLabsNode",
    "stability_image_gen": "app.nodes.integrations.media.stability_node.StabilityAINode",
    "conditional_branch": "app.nodes.logic.advanced.ConditionalBranchNode",
    "task_sequencer": "app.nodes.logic.advanced.TaskSequencerNode",
    "autonomous_agent": "app.nodes.logic.advanced.AutonomousAgentNodeV2",
    "odoo_action": "app.nodes.integrations.odoo_node.OdooNode",
    "zoho_action": "app.nodes.integrations.zoho_node.ZohoNode",
    "wordpress_action": "app.nodes.integrations.wordpress_node.WordPressNode",
    "trello_action": "app.nodes.integrations.trello_node.TrelloNode",
    "ecommerce_action": "app.nodes.verticals.ecommerce_node.EcommerceNode",
    "legal_action": "app.nodes.verticals.legal_node.LegalNode",
    "medtech_action": "app.nodes.verticals.medtech_node.MedTechNode",
    "firecrawl_action": "app.nodes.integrations.scraping.firecrawl_nodes.FirecrawlNode",
    "agentql_action": "app.nodes.integrations.scraping.agentql_node.AgentQLNode",
    "analytics_action": "app.nodes.integrations.analytics_node.AnalyticsNode",
    "mixpanel_action": "app.nodes.integrations.analytics_node.AnalyticsNode",
    "sentry_action": "app.nodes.integrations.analytics_node.AnalyticsNode",
    "aws_s3_action": "app.nodes.amazon.aws_node.AWSS3Node",
    "google_cloud_action": "app.nodes.google.google_cloud_node.GoogleCloudNode",
    "digitalocean_action": "app.nodes.integrations.digitalocean_node.DigitalOceanNode",
    "groq_chat": "app.nodes.models.groq_node.GroqNode",
    "deepseek_chat": "app.nodes.models.deepseek_node.DeepSeekNode",
    "mistral_chat": "app.nodes.models.mistral_node.MistralNode",
    "vertexai_chat": "app.nodes.models.vertexai_node.VertexAINode",
    "milvus_vector_action": "app.nodes.storage.milvus_node.MilvusNode",
    "qdrant_vector_action": "app.nodes.storage.qdrant_node.QdrantNode",
    "weaviate_vector_action": "app.nodes.storage.weaviate_node.WeaviateNode",
    "confluence_action": "app.nodes.integrations.confluence_node.ConfluenceNode",
    "marketing_ads_action": "app.nodes.integrations.marketing_ads_node.MarketingAdsNode",
    "support_ticketing_action": "app.nodes.integrations.support_ticketing_node.SupportTicketingNode",
    "pdf_parser": "app.nodes.processing.pdf_node.PDFParserNode",
    "image_ocr": "app.nodes.integrations.image_ocr.ImageOCRNode",
    "document_processing_action": "app.nodes.processing.document_processing_node.DocumentProcessingNode",
    # Batch 102: E-commerce & Payments
    "shopify_node": "app.nodes.commerce.shopify_node.ShopifyNode",
    "woocommerce_node": "app.nodes.commerce.woocommerce_node.WooCommerceNode",
    "square_node": "app.nodes.finance.square_node.SquareNode",
    "plaid_node": "app.nodes.finance.plaid_node.PlaidNode",
    "mollie_node": "app.nodes.finance.mollie_node.MollieNode",
}

from .registry import NodeRegistry

class NodeFactory:
    def __init__(self):
        # Scan moved to lazy loading in get_node
        pass

    @staticmethod
    def get_node(node_type: str, config: Dict[str, Any]) -> Optional[BaseNode]:
        # 1. Try Digital Registry (Check if already loaded/registered via decorators)
        node_class = NodeRegistry.get_node_class(node_type, scan=False)
        
        # 2. Try Legacy Map (Explicit paths - FAST)
        if not node_class:
            node_path = NODE_MAP.get(node_type)
            if node_path:
                try:
                    module_path, class_name = node_path.rsplit(".", 1)
                    module = importlib.import_module(module_path)
                    node_class = getattr(module, class_name)
                except Exception as e:
                    print(f"NodeFactory Error loading from NODE_MAP '{node_type}': {e}")
        
        # 3. Last Resort: Trigger Full Digital Scan (Slow but thorough)
        if not node_class:
            node_class = NodeRegistry.get_node_class(node_type, scan=True)
            
        # 4. Instantiate if found
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
