import json

new_nodes = [
    {
        "id": "google_sheets_reader",
        "name": "Google Sheets Reader",
        "label": "G-Sheets Reader",
        "description": "Read data from a Google Spreadsheet using service account credentials.",
        "category": "Productivity",
        "icon": "Database",
        "color": "#0f9d58",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Google Credentials",
                "type": "credentials",
                "required": True
            },
            {
                "name": "spreadsheet_id",
                "display_name": "Spreadsheet ID",
                "type": "text",
                "required": True
            },
            {
                "name": "sheet_name",
                "display_name": "Sheet Name",
                "type": "text",
                "default": "Sheet1",
                "required": False
            },
            {
                "name": "input_range",
                "display_name": "Range (Optional)",
                "type": "handle",
                "placeholder": "A1:C10",
                "required": False
            }
        ],
        "outputs": [
            {
                "name": "data",
                "display_name": "Sheet Data",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "google_sheets_writer",
        "name": "Google Sheets Writer",
        "label": "G-Sheets Writer",
        "description": "Append rows of data to a Google Spreadsheet.",
        "category": "Productivity",
        "icon": "Upload",
        "color": "#0f9d58",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Google Credentials",
                "type": "credentials",
                "required": True
            },
            {
                "name": "spreadsheet_id",
                "display_name": "Spreadsheet ID",
                "type": "text",
                "required": True
            },
            {
                "name": "sheet_name",
                "display_name": "Sheet Name",
                "type": "text",
                "default": "Sheet1",
                "required": False
            },
            {
                "name": "data_to_write",
                "display_name": "Data to Append",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "slack_send_message",
        "name": "Slack Message",
        "label": "Slack Send",
        "description": "Send formatted messages to a Slack channel.",
        "category": "Productivity",
        "icon": "MessageSquare",
        "color": "#4a154b",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Slack Credentials",
                "type": "credentials",
                "required": True
            },
            {
                "name": "channel_id",
                "display_name": "Channel ID/Name",
                "type": "text",
                "required": True
            },
            {
                "name": "message",
                "display_name": "Message Text",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "discord_node",
        "name": "Discord Message",
        "label": "Discord",
        "description": "Send notifications to Discord via Webhook or Bot Token.",
        "category": "Productivity",
        "icon": "MessageSquare",
        "color": "#5865F2",
        "inputs": [
            {
                "name": "webhook_url",
                "display_name": "Webhook URL",
                "type": "text",
                "required": False
            },
            {
                "name": "credentials_id",
                "display_name": "Bot Credentials",
                "type": "credentials",
                "required": False
            },
            {
                "name": "channel_id",
                "display_name": "Channel ID",
                "type": "text",
                "required": False
            },
            {
                "name": "message",
                "display_name": "Message",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "notion_db_reader",
        "name": "Notion DB Reader",
        "label": "Notion Reader",
        "description": "Read entries from a Notion database.",
        "category": "Productivity",
        "icon": "BookOpen",
        "color": "#000000",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Notion Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "database_id",
                "display_name": "Database ID",
                "type": "text",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "data",
                "display_name": "DB Entries",
                "types": ["Data"]
            }
        ]
    },
    {
        "id": "notion_page_creator",
        "name": "Notion Page Creator",
        "label": "Notion Creator",
        "description": "Create a new page in Notion.",
        "category": "Productivity",
        "icon": "FileText",
        "color": "#000000",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Notion Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "database_id",
                "display_name": "Database ID (Optional)",
                "type": "text",
                "required": False
            },
            {
                "name": "page_id",
                "display_name": "Parent Page ID (Optional)",
                "type": "text",
                "required": False
            },
            {
                "name": "title",
                "display_name": "Page Title",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "gmail_send_message",
        "name": "Gmail Message",
        "label": "Gmail Send",
        "description": "Send an email via Gmail API.",
        "category": "Productivity",
        "icon": "Mail",
        "color": "#ea4335",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Gmail Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "recipient",
                "display_name": "Recipient",
                "type": "text",
                "required": False
            },
            {
                "name": "subject",
                "display_name": "Subject",
                "type": "text",
                "required": False
            },
            {
                "name": "message",
                "display_name": "Message",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "hubspot_node",
        "name": "HubSpot CRM",
        "label": "HubSpot",
        "description": "Manage contacts and deals in HubSpot CRM.",
        "category": "Productivity",
        "icon": "Users",
        "color": "#ff7a59",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "HubSpot Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Contact", "value": "create_contact"},
                    {"label": "Search Contact", "value": "search_contact"}
                ],
                "default": "create_contact",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Payload/Query",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "API Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "salesforce_node",
        "name": "Salesforce CRM",
        "label": "Salesforce",
        "description": "Create and update objects in Salesforce.",
        "category": "Productivity",
        "icon": "Cloud",
        "color": "#00a1e0",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Salesforce Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "object_type",
                "display_name": "Object Type",
                "type": "text",
                "default": "Lead",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Fields (JSON)",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "SF Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "telegram_node",
        "name": "Telegram Bot",
        "label": "Telegram",
        "description": "Send messages to Telegram chats via Bot API.",
        "category": "Productivity",
        "icon": "MessageCircle",
        "color": "#0088cc",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Telegram Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "chat_id",
                "display_name": "Chat ID",
                "type": "text",
                "required": True
            },
            {
                "name": "message",
                "display_name": "Message",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "google_drive_loader",
        "name": "Google Drive",
        "label": "Drive Loader",
        "description": "Load content from a Google Drive document.",
        "category": "Productivity",
        "icon": "File",
        "color": "#34A853",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Google Drive Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "document_id",
                "display_name": "Document ID",
                "type": "text",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Doc Content",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "mailchimp_node",
        "name": "Mailchimp",
        "label": "Mailchimp",
        "description": "Add subscribers to a Mailchimp list.",
        "category": "Productivity",
        "icon": "Users",
        "color": "#ffe01b",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Mailchimp Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "list_id",
                "display_name": "Audience ID",
                "type": "text",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Email/Subscriber JSON",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "wordpress_node",
        "name": "WordPress",
        "label": "WP Publisher",
        "description": "Publish posts to your WordPress site.",
        "category": "Productivity",
        "icon": "Globe",
        "color": "#21759b",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "WordPress Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "post_status",
                "display_name": "Status",
                "type": "dropdown",
                "options": [
                    {"label": "Publish", "value": "publish"},
                    {"label": "Draft", "value": "draft"},
                    {"label": "Private", "value": "private"}
                ],
                "default": "publish",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Content (JSON/Text)",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "status",
                "display_name": "Status",
                "types": ["Text"]
            }
        ]
    },
    {
        "id": "pipedrive_node",
        "name": "Pipedrive CRM",
        "label": "Pipedrive",
        "description": "Manage persons and deals in Pipedrive.",
        "category": "Productivity",
        "icon": "Trello",
        "color": "#00b21b",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Pipedrive Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Person", "value": "create_person"},
                    {"label": "Create Deal", "value": "create_deal"}
                ],
                "default": "create_person",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Payload (JSON)",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "API Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "github_node",
        "name": "GitHub",
        "label": "GitHub",
        "description": "Automate GitHub issues and repo info.",
        "category": "Productivity",
        "icon": "Github",
        "color": "#333333",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "GitHub Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "repo_owner",
                "display_name": "Repo Owner",
                "type": "text",
                "required": True
            },
            {
                "name": "repo_name",
                "display_name": "Repo Name",
                "type": "text",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Issue", "value": "create_issue"},
                    {"label": "Get Repo Info", "value": "get_repo_info"}
                ],
                "default": "create_issue",
                "required": True
            },
            {
                "name": "input_data",
                "display_name": "Input (e.g. Title)",
                "type": "handle",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "jira_node",
        "name": "Jira",
        "label": "Jira",
        "description": "Manage Jira issues and tasks.",
        "category": "Productivity",
        "icon": "List",
        "color": "#0052cc",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Jira Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "domain",
                "display_name": "Jira Domain",
                "type": "text",
                "placeholder": "yourcompany.atlassian.net",
                "required": True
            },
            {
                "name": "project_key",
                "display_name": "Project Key",
                "type": "text",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Issue", "value": "create_issue"},
                    {"label": "Get Issue", "value": "get_issue"}
                ],
                "default": "create_issue",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "trello_node",
        "name": "Trello",
        "label": "Trello",
        "description": "Create cards and manage boards in Trello.",
        "category": "Productivity",
        "icon": "Trello",
        "color": "#0079bf",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Trello Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "list_id",
                "display_name": "List ID",
                "type": "text",
                "required": False
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Card", "value": "create_card"},
                    {"label": "Get Board Info", "value": "get_board_info"}
                ],
                "default": "create_card",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "gitlab_node",
        "name": "GitLab",
        "label": "GitLab",
        "description": "Manage issues and projects on GitLab.",
        "category": "Productivity",
        "icon": "Gitlab",
        "color": "#FC6D26",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "GitLab Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "project_id",
                "display_name": "Project ID",
                "type": "text",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Issue", "value": "create_issue"},
                    {"label": "Get Project Info", "value": "get_project_info"}
                ],
                "default": "create_issue",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "stripe_node",
        "name": "Stripe",
        "label": "Stripe",
        "description": "Manage payments and customers in Stripe.",
        "category": "Finance",
        "icon": "CreditCard",
        "color": "#6772e5",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "Stripe Token",
                "type": "credentials",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Customer", "value": "create_customer"},
                    {"label": "Create Payment Intent", "value": "create_payment_intent"},
                    {"label": "List Charges", "value": "list_charges"}
                ],
                "default": "create_customer",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "paypal_node",
        "name": "PayPal",
        "label": "PayPal",
        "description": "Create orders and manage payouts in PayPal.",
        "category": "Finance",
        "icon": "DollarSign",
        "color": "#003087",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "PayPal Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "Create Order", "value": "create_order"},
                    {"label": "List Payouts", "value": "list_payouts"}
                ],
                "default": "create_order",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "quickbooks_node",
        "name": "QuickBooks",
        "label": "QuickBooks",
        "description": "Manage accounting in QuickBooks.",
        "category": "Finance",
        "icon": "Book",
        "color": "#2ca01c",
        "inputs": [
            {
                "name": "credentials_id",
                "display_name": "QuickBooks Creds",
                "type": "credentials",
                "required": True
            },
            {
                "name": "action",
                "display_name": "Action",
                "type": "dropdown",
                "options": [
                    {"label": "List Customers", "value": "list_customers"},
                    {"label": "List Invoices", "value": "list_invoices"}
                ],
                "default": "list_customers",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Response",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "legal_node",
        "name": "Legal Analysis",
        "label": "Legal AI",
        "description": "Analyze contracts, check compliance, and assess legal risk.",
        "category": "Verticals",
        "icon": "Shield",
        "color": "#1e3a8a",
        "inputs": [
            {
                "name": "operation",
                "display_name": "Operation",
                "type": "dropdown",
                "options": [
                    {"label": "Contract Analysis", "value": "contract_analysis"},
                    {"label": "Compliance Check", "value": "compliance_check"},
                    {"label": "Risk Assessment", "value": "risk_assessment"}
                ],
                "default": "contract_analysis",
                "required": True
            },
            {
                "name": "jurisdiction",
                "display_name": "Jurisdiction",
                "type": "text",
                "default": "US",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Analysis",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "medtech_node",
        "name": "MedTech",
        "label": "Medical AI",
        "description": "Summarize patient data, ICD coding, and lab interpretation.",
        "category": "Verticals",
        "icon": "PlusSquare",
        "color": "#059669",
        "inputs": [
            {
                "name": "operation",
                "display_name": "Operation",
                "type": "dropdown",
                "options": [
                    {"label": "Patient Summary", "value": "patient_summary"},
                    {"label": "ICD Coding", "value": "icd_coding"},
                    {"label": "Lab Interpretation", "value": "lab_interpretation"}
                ],
                "default": "patient_summary",
                "required": True
            },
            {
                "name": "specialty",
                "display_name": "Specialty",
                "type": "text",
                "default": "General",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Result",
                "types": ["Data", "Text"]
            }
        ]
    },
    {
        "id": "ecommerce_node",
        "name": "E-commerce",
        "label": "Retail AI",
        "description": "Optimize inventory, predict churn, and dynamic pricing.",
        "category": "Verticals",
        "icon": "ShoppingBag",
        "color": "#db2777",
        "inputs": [
            {
                "name": "operation",
                "display_name": "Operation",
                "type": "dropdown",
                "options": [
                    {"label": "Inventory Optimization", "value": "inventory_optimization"},
                    {"label": "Churn Prediction", "value": "churn_prediction"},
                    {"label": "Dynamic Pricing", "value": "dynamic_pricing"}
                ],
                "default": "inventory_optimization",
                "required": True
            },
            {
                "name": "platform",
                "display_name": "Platform",
                "type": "text",
                "default": "Shopify",
                "required": True
            }
        ],
        "outputs": [
            {
                "name": "output",
                "display_name": "Insight",
                "types": ["Data", "Text"]
            }
        ]
    }
]

lib_path = 'backend/data/node_library.json'
with open(lib_path, 'r', encoding='utf-8') as f:
    lib = json.load(f)

for node in new_nodes:
    cat = node.get("category", "Productivity")
    if cat not in lib:
        lib[cat] = []
    
    # Avoid duplicates
    existing_ids = {n["id"] for n in lib[cat]}
    if node["id"] not in existing_ids:
        lib[cat].insert(0, node)

with open(lib_path, 'w', encoding='utf-8') as f:
    json.dump(lib, f, indent=2)

print("✅ Successfully updated node_library.json with new categories.")
