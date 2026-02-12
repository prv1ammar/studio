import json
from datetime import datetime
from typing import Any, Dict, Optional
from app.db.session import async_session
from app.db.models import AuditLog

class AuditLogger:
    """
    Persistence layer for system and user actions.
    Transitioned to PostgreSQL for Phase 3.
    """
    async def log(self, action: str, user_id: Optional[str], workspace_id: Optional[str] = None, details: Dict[str, Any] = {}):
        """Asynchronously logs an action to the database."""
        async with async_session() as db:
            log_entry = AuditLog(
                user_id=user_id,
                workspace_id=workspace_id,
                action=action,
                details=details,
                timestamp=datetime.utcnow()
            )
            db.add(log_entry)
            await db.commit()

audit_logger = AuditLogger()
