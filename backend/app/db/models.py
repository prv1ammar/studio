from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
import uuid

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True)
    role: str = Field(default="user") # user, admin
    
    # Tier-based subscription system
    tier: str = Field(default="free")  # free, pro, enterprise
    tier_limits: Dict[str, int] = Field(default={}, sa_column=Column(JSON))  # Custom limits per tier
    billing_email: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    subscription_status: str = Field(default="active")  # active, cancelled, past_due
    subscription_ends_at: Optional[datetime] = None
    
    preferred_region: str = Field(default="us-east-1")  # us-east-1, eu-west-1, ap-northeast-1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    owned_workspaces: List["Workspace"] = Relationship(back_populates="owner")
    workspace_memberships: List["WorkspaceMember"] = Relationship(back_populates="user")
    credentials: List["Credential"] = Relationship(back_populates="user")
    comments: List["Comment"] = Relationship(back_populates="user")

class Workspace(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner: User = Relationship(back_populates="owned_workspaces")
    members: List["WorkspaceMember"] = Relationship(back_populates="workspace")
    workflows: List["Workflow"] = Relationship(back_populates="workspace")
    credentials: List["Credential"] = Relationship(back_populates="workspace")

class WorkspaceMember(SQLModel, table=True):
    workspace_id: str = Field(foreign_key="workspace.id", primary_key=True)
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    role: str = Field(default="editor") # owner, editor, viewer
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    workspace: Workspace = Relationship(back_populates="members")
    user: User = Relationship(back_populates="workspace_memberships")

class Workflow(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    definition: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    workspace: Workspace = Relationship(back_populates="workflows")
    versions: List["WorkflowVersion"] = Relationship(back_populates="workflow")
    comments: List["Comment"] = Relationship(back_populates="workflow")

class WorkflowVersion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_id: str = Field(foreign_key="workflow.id")
    definition: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workflow: Workflow = Relationship(back_populates="versions")

class Credential(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    type: str
    encrypted_data: str
    user_id: str = Field(foreign_key="user.id")
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="credentials")
    workspace: Workspace = Relationship(back_populates="credentials")

class Comment(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_id: str = Field(foreign_key="workflow.id")
    node_id: Optional[str] = None # ID of the node being commented on
    user_id: str = Field(foreign_key="user.id")
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workflow: Workflow = Relationship(back_populates="comments")
    user: User = Relationship(back_populates="comments")

class AuditLog(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(None, foreign_key="user.id")
    workspace_id: Optional[str] = Field(None, foreign_key="workspace.id")
    action: str
    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WebhookEndpoint(SQLModel, table=True):
    """Registered webhook endpoints for external triggers."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id")
    name: str
    url: str  # The URL to call when webhook is triggered
    secret: Optional[str] = None  # HMAC secret for signature verification
    verification_type: str = Field(default="generic") # generic, stripe, github, slack
    events: List[str] = Field(default=[], sa_column=Column(JSON))  # Event types to listen for
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookEvent(SQLModel, table=True):
    """Incoming webhook events for persistence and replay."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    endpoint_id: str = Field(foreign_key="webhookendpoint.id")
    event_type: str
    payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    headers: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    signature: Optional[str] = None
    verified: bool = Field(default=False)
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookDelivery(SQLModel, table=True):
    """Outgoing webhook delivery attempts with retry tracking."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_id: str = Field(foreign_key="webhookevent.id")
    attempt: int = Field(default=1)
    status: str  # "pending", "success", "failed"
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Execution(SQLModel, table=True):
    """Workflow execution record for persistence and observability."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_id: Optional[str] = Field(default=None, foreign_key="workflow.id", index=True)
    workspace_id: Optional[str] = Field(default=None, foreign_key="workspace.id", index=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.id", index=True)
    status: str = Field(default="pending")  # pending, running, completed, failed, cancelled
    input: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    output: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    error: Optional[str] = None
    duration: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

class NodeExecution(SQLModel, table=True):
    """Detailed record of an individual node's execution within a workflow run."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    execution_id: str = Field(foreign_key="execution.id", index=True)
    node_id: str = Field(index=True)  # The unique ID of the node in the UI graph
    node_type: str
    status: str = Field(default="success")  # success, error
    input: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    output: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    logs: List[str] = Field(default=[], sa_column=Column(JSON))
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    execution_time: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Schedule(SQLModel, table=True):
    """Recurring workflow triggers based on CRON expressions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_id: str = Field(foreign_key="workflow.id", index=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    name: str
    cron: str  # e.g., "0 0 * * *"
    enabled: bool = Field(default=True)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PrivateNode(SQLModel, table=True):
    """Custom enterprise nodes stored in the database, isolated by workspace."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    name: str = Field(index=True)
    node_type: str = Field(unique=True, index=True)
    category: str = Field(default="Custom")
    description: Optional[str] = None
    icon: str = Field(default="Box")
    color: str = Field(default="#94a3b8")
    code: str  # The Python source code
    ui_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Template(SQLModel, table=True):
    """Workflow blueprints shared in the Marketplace."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: str
    category: str = Field(default="Generic", index=True)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    definition: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    author_id: str = Field(foreign_key="user.id", index=True)
    workspace_id: Optional[str] = Field(default=None, foreign_key="workspace.id", index=True)
    is_public: bool = Field(default=True, index=True)
    downloads_count: int = Field(default=0)
    likes_count: int = Field(default=0)
    preview_image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SlaMetric(SQLModel, table=True):
    """Historical performance metrics for SLA reporting."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    component: str = Field(index=True) # e.g., "worker_pool", "api_gateway", "database"
    uptime_percentage: float = Field(default=100.0)
    avg_latency_ms: Optional[float] = None
    error_rate: float = Field(default=0.0)
    region: str = Field(default="global", index=True)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)

class Incident(SQLModel, table=True):
    """Tracks system outages and performance degradations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    description: str
    status: str = Field(default="investigating") # "investigating", "identified", "monitoring", "resolved"
    severity: str = Field(default="minor") # "minor", "major", "critical"
    affected_components: List[str] = Field(default=[], sa_column=Column(JSON))
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ApiKey(SQLModel, table=True):
    """Secure access tokens for programmatic workflow triggering."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    name: str  # e.g., "Production Trigger Key"
    key_hash: str = Field(unique=True, index=True)  # Hashed key for storage
    key_prefix: str  # First 4-8 chars for UI identification (e.g., "st_live_...")
    scopes: List[str] = Field(default=["workflow:run"], sa_column=Column(JSON))
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
