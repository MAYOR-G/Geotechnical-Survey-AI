from datetime import datetime, timezone
from typing import Any, Optional
import uuid
from pydantic import BaseModel


class MetaInfo(BaseModel):
    request_id: str
    timestamp: str


def ok_response(data: Any, request_id: Optional[str] = None) -> dict:
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": request_id or f"req_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "error": None,
    }
