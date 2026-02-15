# 🚀 Tyboo Studio: Platform & Scale Roadmap (V3.1+)

This document outlines the strategic transition from a **Hardened Core Engine** to a **Scalable, Multi-Tenant SaaS Platform**.

---

## 🏁 Phase 1: Operational Safeguards (The "SaaS Shield") ✅
*Protecting server stability and preventing resource abuse.*

- [x] **Redis Rate Limiting**: Enforce per-user/per-workspace concurrent execution limits.
- [x] **Circuit Breakers (Global)**: Automatically quarantine unstable nodes (e.g., failing LLM APIs).
- [x] **Execution Timeouts**: Enforce strict `max_duration` at the node and workflow level.
- [x] **Memory Protections**: Prevent large payloads from causing OOM (Out of Memory) crashes.

## 🏢 Phase 2: Multi-Tenant Hardening & RBAC 
*Absolute data isolation and team-based collaboration.*

- [ ] **Workspace Scoping Audit**: Verify all DB queries are filtered by `workspace_id`.
- [ ] **Credential Sandboxing**: Prevent cross-workspace credential leakage.
- [ ] **Governance & Audit Logs**: High-fidelity records of system changes (Users invited, Keys rotated).
- [ ] **Permission UI**: Frontend roles management (Invite/Promote/Demote members).

## 📦 Phase 3: Distributed Execution (Worker Pool)
*Scaling execution independently of the API.*

- [ ] **Async Queue (ARQ)**: Transition Webhook/API triggers to Redis-backed queues.
- [ ] **Worker Isolation**: Deploy separate worker nodes to handle heavy AI/Data processing.
- [ ] **Retry Policies**: Advanced backoff strategies for transient network failures.
- [ ] **Dead Letter Queue (DLQ)**: Capture and replay failed background tasks.

## 🎨 Phase 4: Growth & Templates
*Reducing friction for new users.*

- [ ] **Public Template Library**: Pre-built recipes (e.g., Slack alerts, DB Sync).
- [ ] **Private Template Marketplace**: Custom organization-wide blueprints.
- [ ] **Graph Search**: Search and replace functionality within complex workflows.

## 💳 Phase 5: Usage Metering & Pre-Billing
*Understanding costs and laying the foundation for monetization.*

- [ ] **Execution Metering**: Track "Tasks per Month" per workspace.
- [ ] **AI Token Logging**: Transparent tracking of LLM costs (Input/Output tokens).
- [ ] **Tier Manager**: Logic to switch between Free/Pro limits.

---

**Current Status**: 🟢 Hardened Core (V3.0) Complete | 🟡 Starting Phase 1
**Last Updated**: 2026-02-15
