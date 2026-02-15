from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from sqlmodel import select
from app.db.session import async_session
from app.db.models import Execution, SlaMetric
import statistics

class ScalingPredictor:
    """
    Predictive scaling engine for Phase 7.
    Analyzes historical workflow volume and SLA performance to forecast load
    and recommend worker pool adjustments.
    """
    
    def __init__(self):
        self.lookback_hours = 24
        self.scaling_threshold = 0.8 # 80% occupancy triggers scale up

    async def forecast_load(self, region: str = "us-east-1") -> Dict[str, Any]:
        """
        Analyzes the last 24 hours of data to predict load for the next hour.
        """
        async with async_session() as db:
            now = datetime.utcnow()
            yesterday = now - timedelta(hours=self.lookback_hours)
            
            # 1. Get execution volume per hour for the last 24h
            # In a real system, we'd use a time-series grouping.
            # Here we'll simulate trend analysis.
            res = await db.execute(
                select(Execution)
                .where(Execution.created_at >= yesterday)
            )
            executions = res.scalars().all()
            
            if not executions:
                return {"predicted_load": "low", "recommendation": "keep_current", "confidence": 0.5}

            # Simple heuristic: compare last hour to average hour
            last_hour_start = now - timedelta(hours=1)
            last_hour_vol = len([e for e in executions if e.created_at >= last_hour_start])
            avg_hourly_vol = len(executions) / self.lookback_hours
            
            trend = "increasing" if last_hour_vol > avg_hourly_vol else "stable"
            
            # 2. Check SLA Performance (Latency/Error spikes)
            sla_res = await db.execute(
                select(SlaMetric)
                .where(SlaMetric.region == region)
                .order_by(SlaMetric.period_end.desc())
                .limit(10)
            )
            metrics = sla_res.scalars().all()
            avg_uptime = statistics.mean([m.uptime_percentage for m in metrics]) if metrics else 100.0
            
            # 3. Decision Logic
            recommendation = "keep_current"
            if trend == "increasing" and avg_uptime < 99.0:
                recommendation = "scale_up"
            elif trend == "decreasing" and avg_hourly_vol < 10:
                recommendation = "scale_down"
                
            return {
                "region": region,
                "current_hourly_volume": last_hour_vol,
                "avg_hourly_volume": round(avg_hourly_vol, 2),
                "load_trend": trend,
                "predicted_load": "high" if trend == "increasing" else "normal",
                "recommendation": recommendation,
                "confidence": 0.85 if len(executions) > 100 else 0.6
            }

scaling_predictor = ScalingPredictor()

