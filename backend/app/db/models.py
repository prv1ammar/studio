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
