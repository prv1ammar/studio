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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    workflows: List["Workflow"] = Relationship(back_populates="user")
    credentials: List["Credential"] = Relationship(back_populates="user")

class Workflow(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    definition: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    user_id: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="workflows")
    versions: List["WorkflowVersion"] = Relationship(back_populates="workflow")

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="credentials")

class AuditLog(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(None, foreign_key="user.id")
    action: str
    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
