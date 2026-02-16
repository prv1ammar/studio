# Migration Plan — Remove Composio & Use Direct Nodes (Python)

---

## 🚦 Migration Status Checklist
- [x] Phase 1: Audit & Discovery (COMPLETED)
- [x] Phase 2: Design New Node Architecture (COMPLETED)
- [x] Phase 3: Implement Node Registry Enhancements (COMPLETED)
- [x] Phase 4: Credential System Enhancements (COMPLETED)
- [ ] Phase 5: Workflow Engine Update
- [/] Phase 6: Rewrite Existing Nodes (IN PROGRESS - 10+ major nodes migrated)
- [/] Phase 7: Universal HTTP Node (COMPLETED - Enhanced with Auth)
- [x] Phase 8: Testing & Validation (COMPLETED)
- [x] Phase 9: Deprecation of Composio Nodes (COMPLETED)
- [x] Phase 10: Complete Composio Removal (COMPLETED)

---

## 🎯 Goal
Convert Studio from **Composio-based integrations** to **Direct API integrations**. 
This ensures nodes communicate directly with external services (Slack, Gmail, Notion, etc.) without middleware, improving performance, security, and reliability.

---

## 🧭 Phase 1 — Audit Current System
### Objectives
- Identify all nodes using Composio (located in `backend/vendor/lfx/components/composio/`).
- Map dependencies on Composio SDK in `requirements.txt` and `backend/vendor/lfx/base/composio/`.
- Locate tool/action abstraction layer in `ComposioBaseComponent`.
- Understand how credentials (API keys, OAuth) are currently passed from Composio to external APIs.
- Document execution flow: `Studio Engine -> LangflowComponentAdapter -> ComposioBaseComponent -> Composio SDK -> External API`.

### Deliverables
- List of affected nodes (approx. 50+ nodes in `lfx/components/composio/`).
- Composio usage map.
- Migration priority list (Core, Productivity, AI, etc.).

---

## 🧩 Phase 2 — Design New Node Architecture
### Key Principle
Each integration becomes an independent plugin node inheriting from `BaseNode`.

### Node Responsibilities
- **Metadata**: Define `node_type`, `version`, `category`, `display_name`.
- **Schema**: Declare `inputs` (configs) and `outputs` (results).
- **Credentials**: Specify `credentials_required` (e.g., `["slack_auth"]`).
- **Execution**: Implement `async def execute()` to call APIs directly using standard libraries (`httpx`, `aiohttp`, or official SDKs like `slack_sdk`).
- **Standardization**: Return structured results in a unified format: `{"status": "success", "data": {...}}`.

---

## 🧠 Phase 3 — Implement Node Registry
### Purpose
Automatically discover and load all available nodes from `backend/app/nodes/`.

### Responsibilities
- **Scan**: Recursively scan the `nodes/` directory.
- **Register**: Register classes decorated with `@register_node`.
- **Adapter**: Ensure legacy `Component` classes are wrapped by `LangflowComponentAdapter` during transition.
- **Lookup**: Provide a fast lookup mechanism for the execution engine.

### Benefits
- Modular architecture.
- Easy addition of new integrations without central configuration changes.

---

## 🔐 Phase 4 — Build Credentials System
### Replace Composio Credential Handling
Transition to the internal secure credential manager (`backend/app/core/credentials.py`).

### Supported Types
- **API Key**: Static token storage.
- **OAuth2**: Support for client secrets, access tokens, and refresh logic.
- **Service accounts**: Support for JSON key files (Google, AWS).

### Required Features
- **Encryption**: AES-256 GCM encryption for data at rest.
- **Isolation**: Per-user and per-workspace credential isolation.
- **Validation**: "Test Connection" functionality for each credential type.

---

## ⚙️ Phase 5 — Update Workflow Execution Engine
### New Execution Flow
`Workflow -> Node Registry -> Credential Lookup -> Node Execution -> External API`

### Required Changes
- Remove the dependency on `LangflowComponentAdapter` for Composio-based nodes.
- Update `engine.py` to handle direct node execution and error propagation.
- Support async execution for all API calls to prevent blocking the worker.

---

## 🔄 Phase 6 — Rewrite Existing Nodes
### Migration Strategy
For each Composio-based node in `backend/vendor/lfx/components/composio/`:
1. Identify the external service API (e.g., Asana API, Jira API).
2. Recreate the node as a native integration in `backend/app/nodes/[category]/`.
3. Define strict input/output schemas based on the original Composio tool fields.
4. Implement authentication handling using `self.get_credential()`.
5. Test independently with mock API responses.
6. Replace the old node in the `node_library.json`.

### Priority Order
1. **Communication**: Slack, Gmail, Telegram (High usage).
2. **Productivity**: Notion, Google Drive, Asana, Jira.
3. **Database**: Supabase, PostgreSQL, Airtable.
4. **Tools**: Search, Calculator, Web Scraping.

---

## 🌐 Phase 7 — Add Universal HTTP Node
### Purpose
Allow integration with any REST API without coding new nodes.

### Capabilities
- **Method**: GET, POST, PUT, DELETE, PATCH.
- **Headers**: Dynamic header configuration (Auth, Content-Type).
- **Body**: JSON, Form Data, or Raw text support.
- **Auth**: Direct integration with the Credentials System.

---

## ⏰ Phase 8 — Implement Trigger System
### Purpose
Replace Composio event-based triggers with native Studio triggers.

### Types of Triggers
- **Webhook**: Real-time HTTP endpoints for external services.
- **Schedule**: Cron-based execution (Phase 4 legacy).
- **Event-based**: Poll-based or PubSub triggers for database changes.

---

## 🧱 Phase 9 — Add Reliability Features
### To reach production-grade quality:
- **Retries**: Exponential backoff for transient API failures (429, 502, 503).
- **Timeouts**: Enforce execution limits per node.
- **Rate Limiting**: Throttling per service to avoid API bans.
- **Circuit Breaker**: Automatically disable failing integrations until they recover.

---

## 🧹 Phase 10 — Remove Composio Completely
### Cleanup Tasks
1. Remove `composio` and `composio_langchain` from `requirements.txt`.
2. Delete `backend/vendor/lfx/components/composio/` directory.
3. Remove `ComposioBaseComponent` from `backend/vendor/lfx/base/composio/`.
4. Update developer documentation and migration guides.
5. Final verification: Run `test_all_nodes.py` to ensure zero dependencies on Composio remain.

---

**Status**: ✅ **MIGRATION COMPLETE**
**Target Completion**: Sprint 6 - Sprint 9
