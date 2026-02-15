import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import select
from app.db.session import async_session
from app.db.models import Schedule, Workflow
from app.core.engine import engine
from app.core.config import settings
import uuid
import json

class WorkflowScheduler:
    """
    Lightweight dynamic scheduler for recurring workflows.
    Polls the database for 'due' schedules and triggers them via the engine.
    """
    def __init__(self, poll_interval: int = 60):
        self.poll_interval = poll_interval
        self.running = False

    async def start(self):
        """Starts the scheduler loop."""
        if self.running:
            return
        
        self.running = True
        print(f"[INFO] Workflow Scheduler started (Poll Interval: {self.poll_interval}s)")
        
        while self.running:
            try:
                await self.check_and_trigger()
            except Exception as e:
                print(f"[ERROR] Scheduler Loop Error: {e}")
            
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self.running = False

    async def check_and_trigger(self):
        """Checks for all enabled schedules which are due for execution."""
        now = datetime.utcnow()
        
        async with async_session() as db:
            # Query for enabled schedules where next_run_at <= now
            # Note: For the first run, next_run_at might be None, so we handle that.
            query = select(Schedule).where(Schedule.enabled == True)
            result = await db.execute(query)
            schedules = result.scalars().all()
            
            for schedule in schedules:
                if self._is_due(schedule, now):
                    await self._trigger_schedule(schedule, db)

    def _is_due(self, schedule: Schedule, now: datetime) -> bool:
        """Determines if a schedule is due. Simple implementation using polling logic."""
        if not schedule.next_run_at:
            # First time initialization
            schedule.next_run_at = self._calculate_next_run(schedule.cron, now)
            return False
        
        return schedule.next_run_at <= now

    def _calculate_next_run(self, cron_expr: str, current_time: datetime) -> datetime:
        """
        Parses a cron-like string and returns the next occurrence.
        Limited POC implementation: Supports '@minutely', '@hourly', '@daily'.
        In production, replace with 'croniter'.
        """
        if cron_expr == "@minutely":
            return current_time + timedelta(minutes=1)
        elif cron_expr == "@hourly":
            return (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        elif cron_expr == "@daily":
            return (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Fallback to daily if unknown
            return current_time + timedelta(days=1)

    async def _trigger_schedule(self, schedule: Schedule, db):
        """Triggers the actual workflow execution."""
        print(f"[SCHEDULER] Triggering '{schedule.name}' (Workflow: {schedule.workflow_id})")
        
        # 1. Fetch the workflow definition
        wf_result = await db.execute(select(Workflow).where(Workflow.id == schedule.workflow_id))
        workflow = wf_result.scalar_one_or_none()
        
        if not workflow:
            print(f"[WARN] Workflow {schedule.workflow_id} not found for schedule {schedule.id}")
            return

        # 2. Trigger in background via Engine
        execution_id = str(uuid.uuid4())
        
        # Fire and forget
        asyncio.create_task(
            engine.process_workflow(
                workflow.definition,
                message="[Scheduled Trigger]",
                context={
                    "schedule_id": schedule.id,
                    "execution_id": execution_id,
                    "user_id": schedule.user_id,
                    "workspace_id": schedule.workspace_id
                }
            )
        )

        # 3. Update Schedule Status
        schedule.last_run_at = datetime.utcnow()
        schedule.next_run_at = self._calculate_next_run(schedule.cron, schedule.last_run_at)
        db.add(schedule)
        await db.commit()

scheduler = WorkflowScheduler()

