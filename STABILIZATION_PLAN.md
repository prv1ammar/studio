# 🏗️ AUTOMATION STUDIO: FULL REBUILD & STABILIZATION PLAN

## 🎯 FINAL OBJECTIVE
**Transform**: 384 unstable nodes + messy ports + broken configs  
**Into**: A structured engine + standardized nodes + safe execution + scalable platform ready for international growth.

---

## 🛑 PHASE 0: FREEZE (CRITICAL)
**Status**: ⛔ STOP  
*   Adding new nodes
*   Adding new integrations
*   Changing the UI

**Goal**: Stability before expansion.  
**Duration**: 3 days.

---

## 🔍 PHASE 1: GLOBAL AUDIT
**Action**: Create an Audit Script.  
**Goal**: Know exactly how broken the system is.  
**Duration**: 1 week.

The script must detect:
*   Total node count
*   Nodes without version
*   Nodes without category
*   Nodes without inputs/outputs
*   Duplicate `node_type`
*   Nodes containing API keys or hardcoded secrets

---

## ⚖️ PHASE 2: NODE LAW (MANDATORY STANDARD)
**Action**: Enforce a strict schema.
**Duration**: 1 week.

**Required Schema**:
```json
{
  "node_type": "string",
  "version": "1.0.0",
  "category": "trigger|action|logic|ai",
  "inputs": {},
  "outputs": {},
  "credentials_required": [],
  "deprecated": false
}
```
❗ Any node that does not respect this structure cannot run.

---

## 🔌 PHASE 3: PORT NORMALIZATION
**Action**: Standardize Input/Output Ports.
**Duration**: Part of Phase 7.

**Standard**:
*   **Input Ports**: `input`, `config`, `credentials`
*   **Output Ports**: `success`, `error`, `data`
*   **Forbidden**: `done`, `result`, `ok`, `output1`

---

## 🔐 PHASE 4: CREDENTIAL DETOX
**Action**: Secure all secrets.
**Duration**: Part of Phase 7.

1.  Remove all API keys from nodes.
2.  Remove `process.env` usage inside node logic.
3.  Remove hardcoded secrets.
4.  Replace with `"credentials_required": ["openai_key"]`.

---

## ⚙️ PHASE 5: EXECUTION ENGINE REBUILD (✅ DONE/IN PROGRESS)
**Standard ExecutionContext**:
```json
{
  "variables": {},
  "secrets": {},
  "node_outputs": {},
  "metadata": {
    "workflow_id": "",
    "execution_id": ""
  }
}
```

**Mandatory Structured Output**:
```json
{
  "status": "success|error",
  "data": {},
  "error": null
}
```

---

## 🛡️ PHASE 6: GRAPH VALIDATOR (✅ DONE)
**Checks**:
*   Only one trigger allowed (per branch/workflow)
*   No infinite loops (Cycle detection)
*   All required inputs connected
*   Required credentials available

---

## 🧹 PHASE 7: BATCH REFACTOR STRATEGY
**Action**: Refactor nodes in batches.
**Duration**: 4–6 weeks.

*   🔥 **Batch 1 (Critical)**: WhatsApp, HTTP Request, Email, Google Sheets, AI Nodes
*   📦 **Batch 2**: Database, File, Webhook
*   🔌 **Batch 3**: Advanced connectors
*   🧩 **Batch 4**: Rare integrations

---

## 🏷️ PHASE 8: VERSIONING SYSTEM
**Action**: Semantic Versioning for Nodes.
**Standard**: `"version": "1.2.0"`
*   Bug fix → patch
*   New feature → minor
*   Breaking change → major

---

## 🧪 PHASE 9: AUTO TEST FRAMEWORK
**Action**: Create `test_all_nodes.py`.
**Checks**:
*   Structured output
*   Proper error handling
*   No crashes

---

## 🔒 PHASE 10: NODE LOCK SYSTEM
**Action**: Prevent direct modifications.
*   Any change requires version increment.
*   Code review required.

---

## 🗄️ PHASE 11: DATABASE STABILIZATION (✅ DONE)
**Tables**: `users`, `credentials`, `workflows`, `workflow_nodes`, `workflow_edges`, `executions`, `execution_logs`.

---

## 🖥️ PHASE 12: FRONTEND ALIGNMENT
**Action**: Update Studio UI.
*   Node library panel
*   Dynamic config panel
*   Credential manager UI
*   Execution logs viewer
*   Error highlighting

---

## 📉 SMART STRATEGIC OPTION
If 384 nodes are too many:
1.  ✔ Archive 200
2.  ✔ Keep only 100 stable
3.  ✔ Quality > Quantity

---

## ⏳ REALISTIC TIMELINE
| Phase | Duration |
| :--- | :--- |
| Audit | 1 week |
| Node Standardization | 1 week |
| Engine rebuild | 1–2 weeks |
| Batch refactor | 4 weeks |
| Testing & Lock | 1 week |
| **Total** | **≈ 8 weeks** |
