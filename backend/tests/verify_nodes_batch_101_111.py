import sys
import os
import importlib
import traceback

# Adjust path to include backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.nodes.factory import NODE_MAP

# Define the batches we want to test (keys added recently)
TARGET_KEYS = [
    # Batch 102
    "shopify_node", "woocommerce_node", "square_node", "plaid_node", "mollie_node",
    # Batch 103
    "merge_node", "split_in_batches_node", "set_node", "wait_node", "item_lists_node",
    # Batch 104
    "microsoft_teams_node", "sendgrid_node", "zoom_node", "mattermost_node", "aws_ses_node",
    "mailgun_node", "postmark_node", "sparkpost_node", "mandrill_node", "constant_contact_node",
    # Batch 105
    "google_calendar_node", "google_docs_node", "microsoft_outlook_node", "microsoft_excel_node",
    "monday_com_node", "asana_node", "clickup_node", "linear_node", "basecamp_node", "todoist_node",
    # Batch 106
    "facebook_pages_node", "linkedin_node", "reddit_node", "pinterest_node", "medium_node",
    "tumblr_node", "buffer_node", "hootsuite_node", "sprout_social_node", "later_node",
    # Batch 107
    "dropbox_node", "box_node", "onedrive_node", "google_cloud_storage_node", "azure_blob_storage_node",
    "backblaze_b2_node", "wasabi_node", "pcloud_node", "sync_com_node", "ftp_node",
    # Batch 108
    "salesforce_node", "hubspot_node", "zoho_crm_node", "pipedrive_node", "activecampaign_node",
    "mailchimp_node", "copper_node", "insightly_node", "freshsales_node", "keap_node",
    # Batch 109
    "google_analytics_node", "mixpanel_node", "zendesk_node", "intercom_node", "freshdesk_node",
    "posthog_node", "segment_node", "help_scout_node", "drift_node", "hotjar_node",
    # Batch 110
    "jira_node", "github_node", "gitlab_node", "bitbucket_node", "aws_lambda_node",
    "docker_node", "mysql_node", "postgresql_node", "mongodb_node", "redis_node",
    # Batch 111
    "date_time_node", "math_node", "crypto_node", "compression_node", "spreadsheet_parser_node",
    "markdown_node", "data_transformation_node", "wait_for_webhook_node", "ssh_node", "binary_data_node"
]

def verify_nodes():
    print(f"Verifying {len(TARGET_KEYS)} nodes from Batches 102-111...\n")
    
    success_count = 0
    failure_count = 0
    failures = []
    missing_deps = set()

    for key in TARGET_KEYS:
        node_path = NODE_MAP.get(key)
        if not node_path:
            print(f"❌ {key}: Not found in NODE_MAP")
            failure_count += 1
            failures.append(f"{key}: Not found in map")
            continue

        try:
            module_path, class_name = node_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            node_class = getattr(module, class_name)
            
            # Try to instantiate with empty config
            instance = node_class(config={})
            print(f"✅ {key}: Loaded successfully")
            success_count += 1
            
        except ImportError as e:
            print(f"⚠️  {key}: Import Error - {str(e)}")
            failure_count += 1
            failures.append(f"{key}: {str(e)}")
            # heuristic for missing libs
            if "No module named" in str(e):
                missing_deps.add(str(e).split("'")[1])
        except Exception as e:
            print(f"❌ {key}: Instantiation Error - {str(e)}")
            failure_count += 1
            failures.append(f"{key}: {str(e)}")
            # traceback.print_exc() 

    print("\n" + "="*50)
    print(f"Summary: {success_count} Passed, {failure_count} Failed")
    print("="*50)
    
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f" - {f}")

    if missing_deps:
        print("\nLikely Missing Dependencies:")
        for dep in missing_deps:
            print(f" - pip install {dep}")

if __name__ == "__main__":
    verify_nodes()
