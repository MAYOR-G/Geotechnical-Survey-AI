from typing import Optional
from pydantic import BaseModel


class IntakeAnalyzeRequest(BaseModel):
    prompt: str = ""


class ChatStreamRequest(BaseModel):
    message: str
    model: str = "tier1_tier2_pipeline"
    action: Optional[str] = None


class QaResolveRequest(BaseModel):
    apply_fix: bool = True


class ResearchQueryRequest(BaseModel):
    query: str
    scope: str = "both"
    thread_id: Optional[str] = None
    project_id: Optional[str] = None
