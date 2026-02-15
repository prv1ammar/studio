# Missing Dependencies for Studio Nodes

To fully enable all the new integration nodes created (Batches 102-111), please install the following Python libraries.
These enable connectivity to external services like databases, cloud storage, and APIs.

Run the following command in your terminal:

```bash
pip install aiohttp feedparser xmltodict beautifulsoup4 python-dateutil markdown html2text asyncssh paramiko aiobotocore aiomysql asyncpg motor redis stripe plaid-python mollie-api-python ShopifyAPI woocommerce
```

## Detailed List

| Node Category | Library | Purpose |
| :--- | :--- | :--- |
| **Core / Web** | `aiohttp` | Async HTTP requests (Used by 90% of nodes) |
| **Utilities** | `feedparser` | RSS Feed Node |
| **Utilities** | `xmltodict` | XML Parser Node |
| **Utilities** | `beautifulsoup4` | HTML Parser Node |
| **Utilities** | `python-dateutil`| Date & Time Node |
| **Utilities** | `markdown` | Markdown Node |
| **Utilities** | `html2text` | Markdown Node |
| **Utilities** | `asyncssh` | SSH Node |
| **Storage** | `paramiko` | SFTP Support (Optional) |
| **Storage/Dev**| `aiobotocore` | Wasabi, S3, AWS Lambda Nodes |
| **Database** | `aiomysql` | MySQL Node |
| **Database** | `asyncpg` | PostgreSQL Node |
| **Database** | `motor` | MongoDB Node |
| **Database** | `redis` | Redis Node |
| **Finance** | `stripe` | Stripe Node |
| **Finance** | `plaid-python` | Plaid Node |
| **Finance** | `mollie-api-python`| Mollie Node |
| **Commerce** | `ShopifyAPI` | Shopify Node |
| **Commerce** | `woocommerce` | WooCommerce Node |

The nodes are designed to fail gracefully with a descriptive error message if these libraries are missing.
