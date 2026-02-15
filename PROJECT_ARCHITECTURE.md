# 🏗️ Tyboo Studio - Project Architecture & File Reference

This document provides a comprehensive breakdown of the Tyboo Studio codebase. It describes the role of every key file and directory to help developers understand the system's inner workings.

---

## 🌍 Root Level: Infrastructure & DevOps
These files manage the environment, deployment, and overall project metadata.

- `docker-compose.yml`: **The Orchestrator.** Defines the five core services (Postgres, Redis, API, Worker, Frontend) and how they communicate.
- `backend.Dockerfile`: Multi-stage build for the Python backend. Optimized for size and speed.
- `studio/frontend.Dockerfile`: Multi-stage build for the React frontend, using Nginx for production-grade serving.
- `deploy.sh`: **1-Click Launch.** Automates the Docker build and startup process.
- `README_DEPLOY.md`: The official guide for setting up the platform in various environments.
- `PLATFORM_SCALE_ROADMAP.md`: The historical trajectory of the project, tracking progress across all 6 phases.
- `requirements.txt`: Python dependency list (FastAPI, SQLModel, LangChain, etc.).
- `.env`: (Environment Variables) Stores sensitive keys, database URLs, and global timeouts.

---

## ⚙️ Backend: `backend/app/`
The "Commercial Brain" and execution engine of the platform.

### 🔌 API Layer (`backend/app/api/`)
Handles all incoming HTTP requests from the frontend.
- `main.py`: **The Entry Point.** Initializes FastAPI, registers all routers, and manages WebSocket signaling for collaboration.
- `auth.py`: Manages JWT authentication, password hashing, and user registration.
- `workspace.py`: Handles workspace multi-tenancy, team invitations, and **Export/Import** logic.
- `billing.py`: Monitors resource usage (tasks/tokens) and provides data for the usage dashboard.
- `docs.py`: **Dynamic Documentation.** Scans all registered nodes and generates technical specs for the UI portal.
- `templates.py`: Manages the Marketplace (Public) and Workspace (Private) template libraries.
- `rbac.py`: Role-Based Access Control logic (Owner, Admin, Editor, Viewer).

### 🧠 Core Engine (`backend/app/core/`)
The logic responsible for actually running the automations.
- `engine.py`: **The Heart.** Recursively processes the graph, handles data flow between nodes, and manages the circuit breaker.
- `worker.py`: **The Heavy Lifter.** The ARQ worker process that executes workflows in the background to keep the API responsive.
- `billing.py` (Core): Logic for tracking AI tokens (OpenAI usage) and incrementing monthly task counts.
- `tier_manager.py`: Definition of limits (Free vs Pro) for every subscription tier.
- `cache_manager.py`: Redis-based result caching to prevent redundant (and expensive) AI calls.
- `timeout.py`: Enforces strict execution limits per node and per workflow.
- `dlq.py`: **Dead Letter Queue.** Captures failed jobs for later inspection and retry.

### 🗄️ Database & Models (`backend/app/db/`)
- `models.py`: All SQLModel definitions including `User`, `Workspace`, `Workflow`, `UsageRecord`, and `Template`.
- `session.py`: Asynchronous database connection handling and dependency injection.

### 🧩 Node Ecosystem (`backend/app/nodes/`)
Tyboo Studio's modular building blocks.
- `factory.py`: **The Assembler.** Dynamically instantiates the correct node class based on the UI's JSON definition.
- `registry.py`: The "Phonebook" of nodes. Tracks every available component in the system.
- `base.py`: The abstract base class that all nodes must inherit from.
- `integrations/`: A massive library of connectors (Google, Slack, Salesforce, CRM, etc.).
- `models/`: LLM-specific nodes (OpenAI, Anthropic, Gemini, DeepSeek).

---

## 🎨 Frontend: `studio/src/`
The high-performance React application where users build workflows.

### 📍 Main Application
- `App.jsx`: **The Control Center.** Manages the React Flow state, WebSocket connections, sidebar catalog, and main header controls.
- `index.css`: The "Premium Design System." Contains all global styles, glassmorphism effects, and animations.
- `collaboration.css`: Specific styling for real-time multiplayer cursors and activity.
- `config.js`: Centralized endpoint configuration for connecting to the backend.

### 📦 Components (`studio/src/components/`)
- `AgentNode.jsx`: Custom React Flow component for rendering Tyboo’s beautiful node cards on the canvas.
- `WorkspaceModal.jsx`: Interface for team management, context switching, and **Resource Export/Import**.
- `UsageStats.jsx`: Real-time progress bars for monthly task and token quotas.
- `NodeReference.jsx`: The searchable documentation portal for browsing component specs.
- `TemplateGallery.jsx`: The "App Store" for one-click workflow deployment.
- `CommentSidebar.jsx`: Built-in collaboration tool for leaving feedback on specific nodes.
- `CopilotBar.jsx`: The AI-driven assistant for natural language workflow editing.
- `AuditLogViewer.jsx`: A transparent history of all actions taken within a workspace.

---

## 🛠️ Utility Scripts (`backend/scripts/`)
- `seed_templates.py`: Populates the marketplace with best-practice blueprints.
- `replay_dlq.py`: A recovery tool to re-run jobs that failed during high traffic.
- `patch_db.py`: Migration utility for adding new fields to existing databases.

---

**Summary**: Tyboo Studio is built as a **Decoupled High-Concurrency Micro-SaaS**. The backend focuses on secure, metered execution, while the frontend provides a world-class low-code authoring experience.
