from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.db.models import WebhookEndpoint, WebhookEvent, Workflow, Execution
from app.core.engine import engine
from app.core.config import settings
import json
import uuid
from datetime import datetime
import hmac
import hashlib

router = APIRouter()

@router.post("/{webhook_id}")
@router.get("/{webhook_id}")
async def handle_incoming_webhook(
    webhook_id: str, 
    request: Request, 
    db: AsyncSession = Depends(get_session)
):
    """
    Unified entry point for all external webhooks.
    Identifies the endpoint, validates security, and triggers the workflow.
    """
    # 1. Look up the endpoint (either in Master Table or directly in Workflows)
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.id == webhook_id))
    endpoint = result.scalar_one_or_none()
    
    # Fallback/Optimization: If not in Master table, we scan workflows later
    # but we need the security config NOW to verify the signature.
    security_config = {
        "secret": endpoint.secret if endpoint else None,
        "verification_type": endpoint.verification_type if endpoint else "generic",
        "workspace_id": endpoint.workspace_id if endpoint else None
    }

    # If endpoint not in DB, we search all workflows to find the matching node and its security
    if not endpoint:
        wf_result = await db.execute(select(Workflow))
        all_workflows = wf_result.scalars().all()
        for wf in all_workflows:
            nodes = wf.definition.get("nodes", [])
            for node in nodes:
                node_data = node.get("data", {})
                if (node.get("type") == "webhook_trigger" or node_data.get("id") == "webhook_trigger") \
                   and node_data.get("webhook_id") == webhook_id:
                    security_config["secret"] = node_data.get("secret")
                    security_config["verification_type"] = node_data.get("verification_type", "generic")
                    security_config["workspace_id"] = wf.workspace_id
                    break
            if security_config["secret"]: break

    if not endpoint and not security_config["workspace_id"]:
        raise HTTPException(status_code=404, detail="Webhook ID not found")

    # 2. Extract payload and headers
    try:
        if request.method == "POST":
            payload = await request.json()
        else:
            payload = dict(request.query_params)
    except:
        payload = {"raw_body": (await request.body()).decode()}

    headers = dict(request.headers)

    # 3. Security: Signature Verification
    if security_config["secret"]:
        body = await request.body()
        is_verified = False
        v_type = security_config["verification_type"] or "generic"

        if v_type == "generic":
            signature = headers.get("x-signature") or headers.get("x-hub-signature-256")
            if signature:
                expected = hmac.new(security_config["secret"].encode(), body, hashlib.sha256).hexdigest()
                if hmac.compare_digest(expected, signature.replace("sha256=", "")):
                    is_verified = True

        elif v_type == "github":
            signature = headers.get("x-hub-signature-256")
            if signature:
                expected = hmac.new(security_config["secret"].encode(), body, hashlib.sha256).hexdigest()
                if hmac.compare_digest(f"sha256={expected}", signature):
                    is_verified = True

        elif v_type == "stripe":
            signature = headers.get("stripe-signature")
            if signature:
                parts = dict(x.split('=') for x in signature.split(','))
                timestamp = parts.get('t')
                v1 = parts.get('v1')
                if timestamp and v1:
                    signed_payload = f"{timestamp}.{body.decode()}".encode()
                    expected = hmac.new(security_config["secret"].encode(), signed_payload, hashlib.sha256).hexdigest()
                    if hmac.compare_digest(v1, expected):
                        is_verified = True

        elif v_type == "slack":
            signature = headers.get("x-slack-signature")
            timestamp = headers.get("x-slack-request-timestamp")
            if signature and timestamp:
                sig_basestring = f"v0:{timestamp}:{body.decode()}".encode()
                expected = hmac.new(security_config["secret"].encode(), sig_basestring, hashlib.sha256).hexdigest()
                if hmac.compare_digest(f"v0={expected}", signature):
                    is_verified = True

        if not is_verified:
            raise HTTPException(status_code=403, detail=f"Invalid {v_type} signature")

    # 4. Persist the Event
    event = WebhookEvent(
        endpoint_id=endpoint.id if endpoint else f"node_{webhook_id}",
        event_type="incoming_raw",
        payload=payload,
        headers=headers,
        verified=True if security_config["secret"] else False
    )
    db.add(event)
    await db.flush()

    # 5. FIND AND TRIGGER ASSOCIATED WORKFLOW
    execution_id = str(uuid.uuid4())
    triggered_workflow_id = None
    from app.db.models import Workflow
    
    # Search all workflows in the workspace
    workflow_result = await db.execute(select(Workflow).where(Workflow.workspace_id == security_config["workspace_id"]))
    workflows = workflow_result.scalars().all()

    for wf in workflows:
        nodes = wf.definition.get("nodes", [])
        for node in nodes:
            node_data = node.get("data", {})
            # Look for matching webhook_id in any node with 'webhook_trigger' as id or type
            if (node_data.get("id") == "webhook_trigger" or node.get("type") == "webhook_trigger") \
               and node_data.get("webhook_id") == endpoint.id: # Or just match by endpoint ID
                triggered_workflow_id = wf.id
                break
        if triggered_workflow_id:
            break

    if triggered_workflow_id:
        # Trigger execution in background (Fire and Forget for the HTTP caller)
        # In a real environment, we'd use 'arq' or 'celery' here.
        # For POC, we'll start an async task.
        import asyncio
        from app.core.engine import engine
        
        asyncio.create_task(
            engine.process_workflow(
                wf.definition,
                message=json.dumps(payload), # Pass payload as message
                context={
                    "webhook_payload": payload,
                    "webhook_headers": headers,
                    "execution_id": execution_id,
                    "workspace_id": endpoint.workspace_id
                }
            )
        )
        print(f" Webhook Gateway: Triggered Workflow '{wf.name}' for event {event.id}")

    # 6. Mark as processed and return
    event.processed = True
    await db.commit()

    return {
        "status": "accepted",
        "message": f"Webhook received and {'workflow triggered' if triggered_workflow_id else 'logged'}",
        "event_id": event.id,
        "execution_id": execution_id,
        "workflow_triggered": triggered_workflow_id is not None
    }

@router.get("/endpoints/list")
async def list_endpoints(
    workspace_id: str, 
    db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.workspace_id == workspace_id))
    return result.scalars().all()

@router.post("/endpoints/create")
async def create_endpoint(
    data: Dict[str, Any], 
    db: AsyncSession = Depends(get_session)
):
    new_ep = WebhookEndpoint(
        workspace_id=data["workspace_id"],
        name=data["name"],
        url="", # Will be generated based on ID
        secret=data.get("secret"),
        verification_type=data.get("verification_type", "generic"),
        events=data.get("events", ["*"])
    )
    db.add(new_ep)
    await db.commit()
    await db.refresh(new_ep)
    
    # Generate the actual URL
    new_ep.url = f"{settings.API_BASE_URL}/webhooks/{new_ep.id}"
    db.add(new_ep)
    await db.commit()
    
    return new_ep
