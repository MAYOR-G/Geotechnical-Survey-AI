from typing import Any, Optional
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    default_contractor_name: Optional[str] = None
    default_contractor_logo_url: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_designation: Optional[str] = None
    author_signature_url: Optional[str] = None
    style_guide_json: Optional[dict[str, Any]] = None
    enable_passcode_gate: Optional[bool] = None
