from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models import SlaMetric, Incident
from app.core.config import settings

class SlaManager:
    """
    Manages Enterprise SLA Monitoring, Incident Tracking, and Proactive Alerting.
    Ensures that system health status is not only monitored but acted upon.
    """
    
    def __init__(self):
        self.alert_webhook_url = os.getenv("MONITORING_ALERT_WEBHOOK")
        self.last_status: Optional[str] = None

    async def check_and_alert(self, current_health: Dict[str, Any]):
        """
        Analyzes health status and triggers alerts if status has degraded.
        Also persists current health into SLA metrics.
        """
        status = current_health.get("status", "unknown")
        
        # 1. Alerting Logic
        if status != self.last_status:
            if status in ["warning", "critical"]:
                await self._send_alert(current_health)
            elif self.last_status in ["warning", "critical"] and status == "healthy":
                await self._send_alert(current_health, recovered=True)
            
            self.last_status = status

        # 2. Persist Metics (Hourly Aggregation)
        # In a real system, we'd aggregate. Here we log the snapshot.
        await self._log_metric(current_health)

    async def _send_alert(self, health: Dict[str, Any], recovered: bool = False):
        """Dispatches an alert to the configured enterprise webhook."""
        if not self.alert_webhook_url:
            print(f" Monitoring Alert ({health['status']}): {health['message']}")
            return

        payload = {
            "text": f"{' RECOVERED' if recovered else ' INCIDENT'} - Studio Platform",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"Platform Status: {health['status'].upper()}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Message:* {health['message']}\n*Time:* {health['timestamp']}"}
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.alert_webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f" Failed to send monitoring alert: {e}")

    async def _log_metric(self, health: Dict[str, Any]):
        """Saves current health state into the SlaMetric table."""
        async with async_session() as db:
            metric = SlaMetric(
                component="platform_global",
                region=settings.STUDIO_REGION,
                uptime_percentage=100.0 if health["status"] == "healthy" else 0.0,
                period_start=datetime.utcnow() - timedelta(minutes=1),
                period_end=datetime.utcnow()
            )
            db.add(metric)
            await db.commit()

    async def create_incident(self, title: str, description: str, severity: str = "minor"):
        """Manually or automatically create a new incident for the status page."""
        async with async_session() as db:
            incident = Incident(
                title=title,
                description=description,
                severity=severity,
                status="investigating"
            )
            db.add(incident)
            await db.commit()
            return incident.id

import os
sla_manager = SlaManager()

