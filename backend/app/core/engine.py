import sys
import os
from typing import Dict, Any, List, Optional
import traceback
import orjson
import time
import asyncio
import random
from app.nodes.factory import NodeFactory

# Root path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Backend path to support 'app.' imports
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Agents directory for legacy/utility support
agents_dir = os.path.join(project_root, "backend", "app", "agents")
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

from app.nodes.factory import NodeFactory
from app.core.validator import validator
from app.core.credentials import cred_manager
from app.core.storage import storage_manager
from app.core.dlq import dlq
from app.db.session import async_session
from app.db.models import Execution, NodeExecution
import uuid
from datetime import datetime

class AgentEngine:
    """
    Modular Agent Engine for the Automation Studio.
    Supports Graph Validation, Execution Context, and Resilience.
    """
    
    def __init__(self):
        self.node_factory = NodeFactory()

    async def execute_node(self, node_type: str, input_text: Any, config: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Any:
        """
        Loads and executes a node with Resilience (Retry logic), Timeout protection, Intelligent Caching, Analytics, and Circuit Breaker.
        """
        from app.core.timeout import execute_with_timeout, TimeoutError
        from app.core.cache import cache_manager
        from app.core.analytics import analytics_tracker
        from app.core.circuit_breaker import circuit_breaker
        
        node_start_time = time.time()
        
        # Check circuit breaker first
        can_execute, reason = await circuit_breaker.can_execute(node_type)
        if not can_execute:
            print(f" Circuit breaker preventing execution of {node_type}: {reason}")
            return {"error": reason, "error_type": "circuit_breaker"}
        
        # Check cache (if enabled and node is cacheable)
        cached_result = await cache_manager.get(node_type, input_text, config or {})
        if cached_result is not None:
            # Track cache hit
            node_duration = time.time() - node_start_time
            await analytics_tracker.track_node_execution(
                node_type=node_type,
                user_id=context.get("user_id") if context else None,
                workspace_id=context.get("workspace_id") if context else None,
                execution_id=context.get("execution_id") if context else "unknown",
                duration=node_duration,
                success=True,
                cached=True
            )
            return cached_result
        
        node = await self.node_factory.get_instance(node_type, config, context)
        if not node:
             return {"error": f"Node type '{node_type}' not found."}
        
        # Resilience: Retry Logic
        max_retries = int(config.get("retry_count", 0)) if config else 0
        last_error = None
        
        # Get node-specific timeout or use default
        node_timeout = int(config.get("timeout", 0)) if config else 0
        if node_timeout == 0:
            from app.core.config import settings
            node_timeout = settings.NODE_EXECUTION_TIMEOUT

        for attempt in range(max_retries + 1):
            try:
                # Add current attempt to context
                if context: context["attempt"] = attempt
                
                # Execute with timeout protection
                result = await execute_with_timeout(
                    node.run(input_text, context),
                    timeout=node_timeout
                )
                
                # Check for logical errors that might need healing
                if isinstance(result, dict) and "error" in result and attempt < max_retries:
                    from app.core.self_healing import self_healing
                    analysis = await self_healing.analyze_and_suggest(node_type, result["error"], config or {}, attempt)
                    
                    if analysis["strategy"] == "retry":
                        delay = analysis.get("delay", 1)
                        print(f" Self-Healing: {analysis['reason']} (Waiting {delay}s...)")
                        await asyncio.sleep(delay)
                        
                        # Apply dynamic config patches (e.g., increase timeout)
                        if "config_patch" in analysis:
                            config.update(analysis["config_patch"])
                            if "timeout" in analysis["config_patch"]:
                                node_timeout = analysis["config_patch"]["timeout"]
                        continue
                
                # Calculate duration
                node_duration = time.time() - node_start_time
                success = not (isinstance(result, dict) and "error" in result)
                
                # Track analytics
                await analytics_tracker.track_node_execution(
                    node_type=node_type,
                    user_id=context.get("user_id") if context else None,
                    workspace_id=context.get("workspace_id") if context else None,
                    execution_id=context.get("execution_id") if context else "unknown",
                    duration=node_duration,
                    success=success,
                    cached=False
                )
                
                # Update circuit breaker
                if success:
                    await circuit_breaker.record_success(node_type)
                    # Cache successful result
                    await cache_manager.set(node_type, input_text, config or {}, result)

                    token_usage = 0
                    if isinstance(result, dict):
                        # Detect common token usage patterns (OpenAI, Anthropic, etc.)
                        data = result.get("data", {})
                        raw_res = data.get("result", {})
                        if isinstance(raw_res, dict) and "usage" in raw_res:
                            usage = raw_res["usage"]
                            token_usage = usage.get("total_tokens", 0) or usage.get("total_tokens", 0)

                    # Track Billing Usage (Task execution) - background
                    asyncio.create_task(billing_manager.track_usage(
                        workspace_id=context.get("workspace_id") if context else None,
                        tasks=1,
                        tokens=token_usage
                    ))
                else:
                    error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
                    await circuit_breaker.record_failure(node_type, error_msg)

                return result
                
            except TimeoutError as e:
                last_error = f"Node execution timeout ({node_timeout}s)"
                if attempt < max_retries:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    print(f" Retrying node {node_type} (Attempt {attempt+1}/{max_retries}) due to timeout. Waiting {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                # Track failed execution
                node_duration = time.time() - node_start_time
                await analytics_tracker.track_node_execution(
                    node_type=node_type,
                    user_id=context.get("user_id") if context else None,
                    workspace_id=context.get("workspace_id") if context else None,
                    execution_id=context.get("execution_id") if context else "unknown",
                    duration=node_duration,
                    success=False,
                    cached=False
                )
                
                # Record circuit breaker failure
                await circuit_breaker.record_failure(node_type, last_error)
                
                print(f" Node Execution Timeout ({node_type}) after {attempt+1} attempts: {last_error}")
                return {"error": last_error, "error_type": "timeout"}
                
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    print(f" Retrying node {node_type} (Attempt {attempt+1}/{max_retries}) due to exception: {last_error}. Waiting {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                
                # Track failed execution
                node_duration = time.time() - node_start_time
                await analytics_tracker.track_node_execution(
                    node_type=node_type,
                    user_id=context.get("user_id") if context else None,
                    workspace_id=context.get("workspace_id") if context else None,
                    execution_id=context.get("execution_id") if context else "unknown",
                    duration=node_duration,
                    success=False,
                    cached=False
                )
                
                # Record circuit breaker failure
                await circuit_breaker.record_failure(node_type, last_error)
                
                import traceback
                stack_trace = traceback.format_exc()
                print(f" Node Execution Failed ({node_type}) after {attempt + 1} attempts: {last_error}")
                return {"error": last_error, "stack_trace": stack_trace}

    async def process_workflow(self, graph_data: Dict[str, Any], message: str, broadcaster=None, execution_id: str = None, start_node_id: str = None, initial_outputs: Dict[str, Any] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Core workflow execution engine with Validation and Structured Context.
        Supports resuming from a specific node.
        """
        workspace_id = context.get("workspace_id") if context else None
        
        # 1. Check Billing Limits
        if not await billing_manager.check_limits(workspace_id):
            error_msg = "Monthly task limit exceeded for this workspace."
            if broadcaster: await broadcaster("error", "billing_limit_exceeded", {"message": error_msg})
            raise Exception(error_msg)

        execution_id = execution_id or str(uuid.uuid4())
        
        # Performance Tracking (OpenTelemetry Ready)
        start_time = time.time()
        
        # 0. RATE LIMITING CHECK
        from app.core.rate_limiter import rate_limiter
        user_id = context.get("user_id") if context else "anonymous"
        workspace_id = context.get("workspace_id") if context else "default"
        
        can_run = await rate_limiter.check_user_limit(user_id)
        if not can_run:
            error_msg = f"Rate Limit Exceeded: Parallel execution limit reached for user {user_id}"
            if broadcaster: await broadcaster("error", "rate_limit_exceeded", {"message": error_msg})
            return error_msg
            
        await rate_limiter.acquire(user_id, workspace_id, execution_id)
        
        # PERSIST INITIAL EXECUTION RECORD
        try:
            async with async_session() as session:
                exec_record = Execution(
                    id=execution_id,
                    workflow_id=graph_data.get("id"),
                    workspace_id=context.get("workspace_id", "default") if context else "default",
                    user_id=context.get("user_id") if context else None,
                    status="running",
                    input={"message": message}
                )
                session.add(exec_record)
                await session.commit()
        except Exception as e:
            print(f" Failed to persist initial execution: {e}")

        # 1. GRAPH VALIDATION
        is_valid, errors = validator.validate(graph_data)
        if not is_valid:
            error_msg = " | ".join(errors)
            if broadcaster: await broadcaster("error", "validation_failed", {"message": error_msg})
            return f"Validation Failed: {error_msg}"

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # 2. SEED EXECUTION CONTEXT
        user_id = context.get("user_id") if context else None
        execution_context = {
            "variables": {"initial_query": message},
            "node_outputs": initial_outputs or {},
            "graph_metadata": {"node_count": len(nodes)},
            "execution_id": execution_id,
            "user_id": user_id,
            "engine": self
        }

        # Auditing
        from app.core.audit import audit_logger
        await audit_logger.log(
            action="workflow_start",
            user_id=user_id,
            details={"execution_id": execution_id, "node_count": len(nodes)}
        )
        
        # Analytics: Track workflow start
        from app.core.analytics import analytics_tracker
        workflow_id = execution_context.get("workflow_id", "unknown")
        workspace_id = context.get("workspace_id") if context else None
        await analytics_tracker.track_workflow_execution(
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            status="started"
        )

        # 3. Identify Entry Point (Support 'chatInput' or resume node)
        if start_node_id:
            current_node = next((n for n in nodes if n['id'] == start_node_id), None)
            if not current_node: return f"Resume Failed: Node {start_node_id} not found."
            current_input = execution_context["node_outputs"].get(start_node_id, message)
        else:
            current_node = next((n for n in nodes if n.get('data', {}).get('id') == 'chatInput'), nodes[0])
            current_input = message
        visited = set()
        
        # Safety: Path limit
        for _ in range(50):
            node_id = current_node['id']
            if node_id in visited: break
            visited.add(node_id)
            
            node_data = current_node.get('data', {})
            reg_id = node_data.get('id')
            
            # Update Context for current hop
            execution_context["current_node_id"] = node_id
            
            # Broadcast node start
            if broadcaster: 
                await broadcaster("node_start", node_id, {
                    "input": str(current_input)[:500],
                    "timestamp": time.time()
                })
            
            #  DEBUGGER: Check for BREAKPOINT
            if context and context.get("debug_mode"):
                from app.core.config import settings
                import redis.asyncio as aioredis
                r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                
                # Check if this node_id is marked as a breakpoint
                is_paused = await r.get(f"breakpoint_{execution_id}_{node_id}")
                if is_paused:
                    print(f" Debugger: Paused at node {node_id}")
                    if broadcaster: await broadcaster("debug_paused", node_id)
                    
                    # Wait for resume signal
                    while await r.get(f"breakpoint_{execution_id}_{node_id}"):
                        await asyncio.sleep(0.5)
                        # Check for 'step_over'
                        if await r.get(f"step_{execution_id}"):
                            await r.delete(f"step_{execution_id}")
                            break
                    
                    if broadcaster: await broadcaster("debug_resumed", node_id)
            
            # --- EXECUTE ---
            if reg_id == 'chatInput':
                result = current_input
            else:
                result = await self.execute_node(reg_id, current_input, config=node_data, context=execution_context)

            # PERSIST NODE EXECUTION
            try:
                async with async_session() as session:
                    node_exec = NodeExecution(
                        execution_id=execution_id,
                        node_id=node_id,
                        node_type=reg_id,
                        input=current_input,
                        output=result,
                        logs=getattr(node, "metrics", {}).get("logs", []),
                        status="success" if not (isinstance(result, dict) and "error" in result) else "error",
                        error=result.get("error") if isinstance(result, dict) else None,
                        stack_trace=result.get("stack_trace") if isinstance(result, dict) else None,
                        execution_time=node.metrics.get("execution_time", 0.0) if hasattr(node, "metrics") else 0.0
                    )
                    session.add(node_exec)
                    await session.commit()
            except Exception as e:
                print(f" Failed to persist node execution: {e}")

            # Store in output history
            execution_context["node_outputs"][node_id] = result
            
            # Broadcast node completion
            if broadcaster: 
                log_output = result.get("data") if isinstance(result, dict) and "data" in result else result
                await broadcaster("node_end", node_id, {
                    "output": str(log_output)[:1000],
                    "status": "success" if not is_error else "error",
                    "execution_time": node.metrics.get("execution_time", 0.0) if hasattr(node, "metrics") else 0.0
                })
            
            # Handle Critical Failures (unless 'continue_on_fail' is set)
            is_error = False
            error_message = ""
            
            if isinstance(result, dict):
                if result.get("status") == "error":
                    is_error = True
                    error_message = result.get("error", "Unknown error")
                elif "error" in result:
                    is_error = True
                    error_message = result["error"]
            
            if is_error:
                if not node_data.get("continue_on_fail"):
                    error_msg = f"Stopped at {node_data.get('label')}: {error_message}"
                    dlq.capture(execution_id, graph_data, error_msg, execution_context)
                    
                    # Log Failure
                    from app.core.audit import audit_logger
                    await audit_logger.log(
                        action="workflow_fail",
                        user_id=user_id,
                        details={"execution_id": execution_id, "error": error_msg}
                    )

                    # UPDATE EXECUTION RECORD TO FAILED
                    try:
                        async with async_session() as db:
                            from sqlmodel import select
                            statement = select(Execution).where(Execution.id == execution_id)
                            res = await db.execute(statement)
                            exec_rec = res.scalar_one_or_none()
                            if exec_rec:
                                exec_rec.status = "failed"
                                exec_rec.error = error_msg
                                exec_rec.finished_at = datetime.utcnow()
                                db.add(exec_rec)
                                await db.commit()
                    except Exception as e:
                        print(f" Failed to update failed execution record: {e}")

                    return error_msg

            # --- TRAVERSAL ---
            # Determine next node based on handle matching or sequential edge
            next_edges = [e for e in edges if e['source'] == node_id]
            next_edge = None
            
            # Priority: Handle-based routing
            # 1. Check for explicit handle match (e.g. 'success', 'error', 'data')
            if isinstance(result, dict):
                # If we have a status, we might want to follow 'success' or 'error' edges
                status = result.get("status")
                
                # Check for direct handle match in result keys
                for edge in next_edges:
                    handle = edge.get('sourceHandle')
                    if handle and handle in result:
                        next_edge = edge
                        break
                
                # Special Logic: If status is success, follow 'success' handle if present
                if not next_edge and status == "success":
                     next_edge = next((e for e in next_edges if e.get('sourceHandle') == "success"), None)
                
                # Special Logic: If status is error (and we continued), follow 'error' handle
                if not next_edge and status == "error":
                     next_edge = next((e for e in next_edges if e.get('sourceHandle') == "error"), None)

            # Fallback: First generic edge (no handle or handle='default')
            if not next_edge:
                next_edge = next((e for e in next_edges if not e.get('sourceHandle') or e.get('sourceHandle') in ["default", "output"]), None)

            if not next_edge: break
            
            next_node_id = next_edge['target']
            s_handle = next_edge.get('sourceHandle')
            
            # Prepare Input for Next Node
            current_input = result
            
            if isinstance(result, dict):
                # 1. Direct handle match logic
                if s_handle and s_handle in result:
                    current_input = result[s_handle]
                # 2. 'data' extraction for standard flow
                elif "data" in result and getattr(result, "status", None) != "error":
                     current_input = result["data"]
                # 3. Legacy error fallback
                elif "error" in result:
                     current_input = result["error"]

            # Threshold for storage by reference (e.g., 50KB)
            if isinstance(current_input, str) and len(current_input) > 50000:
                print(f" Storing large output from {node_id} by reference.")
                current_input = storage_manager.store(current_input)

            # Resolve reference if input is a pointer
            if storage_manager.is_reference(current_input):
                 current_input = storage_manager.retrieve(current_input)

            current_node = next((n for n in nodes if n['id'] == next_node_id), None)
            if not current_node: break
            
        # Log Success
        from app.core.audit import audit_logger
        workflow_duration = time.time() - start_time
        await audit_logger.log(
            action="workflow_success",
            user_id=user_id,
            details={
                "execution_id": execution_id, 
                "duration": f"{workflow_duration:.2f}s"
            }
        )
        
        # Analytics: Track workflow completion
        await analytics_tracker.track_workflow_execution(
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            status="completed",
            duration=workflow_duration
        )
        
        # UPDATE EXECUTION RECORD
        try:
            async with async_session() as db:
                from sqlmodel import select
                statement = select(Execution).where(Execution.id == execution_id)
                results = await db.execute(statement)
                exec_record = results.scalar_one_or_none()
                if exec_record:
                    exec_record.status = "completed"
                    exec_record.output = {"result": str(result)}
                    exec_record.duration = workflow_duration
                    exec_record.finished_at = datetime.utcnow()
                    db.add(exec_record)
                    await db.commit()
        except Exception as e:
            print(f" Failed to update execution record: {e}")
        
        # RELEASE RATE LIMIT SLOT
        await rate_limiter.release(user_id, workspace_id)
        
        return str(result)

# Instantiate and export the engine
engine = AgentEngine()

# Add registry property for compatibility with main.py
# (It expects engine.registry to exist)
from app.nodes.factory import NODE_MAP
engine.registry = NODE_MAP

