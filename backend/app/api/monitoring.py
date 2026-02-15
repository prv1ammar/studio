from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import SlaMetric, Incident, User
from app.api.auth import get_current_user
from app.core.worker_monitor import worker_monitor
from app.core.sla_manager import sla_manager

router = APIRouter()

@router.get("/status")
async def get_public_status():
    """Public status endpoint for status pages."""
    health = await worker_monitor.get_health_status()
    
    # Trigger alerting/logging logic
    await sla_manager.check_and_alert(health)
    
    return {
        "status": health["status"],
        "message": health["message"],
        "timestamp": health["timestamp"]
    }

@router.get("/incidents")
async def list_active_incidents(db: AsyncSession = Depends(get_session)):
    """Lists recent and active incidents."""
    res = await db.execute(select(Incident).order_by(Incident.started_at.desc()).limit(10))
    return res.scalars().all()

@router.get("/sla")
async def get_sla_report(db: AsyncSession = Depends(get_session)):
    """Aggregated SLA metrics for the enterprise dashboard."""
    res = await db.execute(select(SlaMetric).order_by(SlaMetric.period_end.desc()).limit(100))
    metrics = res.scalars().all()
    if not metrics:
        return {"uptime_30d": 100.0, "status": "no_data"}
    uptime = sum(m.uptime_percentage for m in metrics) / len(metrics)
    return {"uptime_report": uptime, "sample_count": len(metrics), "period": "recent_history"}

@router.get("/scaling/forecast")
async def get_scaling_forecast():
    """Predictive scaling recommendations (Phase 7)."""
    from app.core.scaling_predictor import scaling_predictor
    from app.core.config import settings
    return await scaling_predictor.forecast_load(region=settings.STUDIO_REGION)

@router.post("/incidents")
async def create_manual_incident(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Admin endpoint to manually report or update an incident."""
    # Logic same as sla_manager.create_incident but via API
    incident = Incident(
        title=data.get("title"),
        description=data.get("description"),
        severity=data.get("severity", "minor"),
        status="investigating"
    )
    db.add(incident)
    await db.commit()
    return incident
