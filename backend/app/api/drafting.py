from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional, List
from app.api.auth import get_current_user
from app.db.models import User
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json

router = APIRouter()

class NodeDraft(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]

class EdgeDraft(BaseModel):
    id: str
    source: str
    target: str

class WorkflowDraft(BaseModel):
    nodes: List[NodeDraft]
    edges: List[EdgeDraft]

@router.post("/draft")
async def draft_workflow(
    prompt: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    LINGUISTIC DRAFTING (Phase 7).
    Uses LangChain to convert natural language into a valid Studio Workflow JSON.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    system_prompt = (
        "You are the Studio Architect AI. Convert the user's request into a valid React Flow graph JSON.\n"
        "Available node types: chatInput, chatOutput, liteLLM, google_search, translation_node, sub_workflow, webhook_trigger, parallel_map.\n"
        "React Flow uses 'id', 'type', and 'data' for nodes. Edges use 'id', 'source', and 'target'."
    )
    
    lc_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    # Use with_structured_output for guaranteed JSON schema
    structured_llm = llm.with_structured_output(WorkflowDraft)
    chain = lc_prompt | structured_llm
    
    try:
        draft = await chain.ainvoke({"input": prompt})
        return {
            "status": "drafted",
            "prompt": prompt,
            "graph": draft.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drafting Failed: {str(e)}")
