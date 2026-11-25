from typing import Any, Optional
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    subtitle: str = ""
    document_type: str = "Geotechnical Survey Field Report"
    client_name: str = ""
    contractor_name: str = ""
    client_ref_code: str = ""
    contractor_ref_code: str = ""
    revision_number: str = "Rev 01"
    fao_text: str = ""
    water_depth_range: str = ""
    vessel_name: str = ""
    header_logos_json: list[dict[str, Any]] = []
    revision_history_json: list[dict[str, Any]] = []
    authorization_matrix_json: list[dict[str, Any]] = []


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[str] = None
    client_name: Optional[str] = None
    contractor_name: Optional[str] = None
    client_ref_code: Optional[str] = None
    contractor_ref_code: Optional[str] = None
    revision_number: Optional[str] = None
    fao_text: Optional[str] = None
    water_depth_range: Optional[str] = None
    vessel_name: Optional[str] = None
    header_logos_json: Optional[list[dict[str, Any]]] = None
    revision_history_json: Optional[list[dict[str, Any]]] = None
    authorization_matrix_json: Optional[list[dict[str, Any]]] = None
    document_ast_json: Optional[dict[str, Any]] = None


class DocumentAstUpdate(BaseModel):
    document_ast_json: dict[str, Any]


class ClarificationPatchItem(BaseModel):
    id: str
    user_response: Optional[str] = None
    is_resolved: bool = True
    omit_section: bool = False


class ClarificationBatchPatch(BaseModel):
    items: list[ClarificationPatchItem]


class InlineEditRequest(BaseModel):
    selection_text: str
    instruction: str
    section_context: Optional[str] = None


class ExportRequest(BaseModel):
    format: str = "pdf"


class AttachmentReorderRequest(BaseModel):
    ordered_ids: list[str]


class SectionExpandRequest(BaseModel):
    instruction: str


class SectionChartRequest(BaseModel):
    chart_type: str = "casagrande"
