import json
from pathlib import Path
from typing import Any
import yaml
from app.agents.llm_router import llm_router
from app.core.exceptions import ExternalProviderError
from app.models.clarification import ClarificationItem
from app.models.project import Project, ProjectInputFile

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "intake_clarifier.yaml"


def _load_intake_prompt() -> str:
    if PROMPT_PATH.exists():
        data = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
        if data.get("system_prompt"):
            return str(data["system_prompt"]).strip()
    return (
        "You are the Principal Offshore & Trenchless Geotechnical Project Manager and Forensic Intake Gap Analyst. "
        "Audit the uploaded files and project metadata and return JSON clarification items."
    )


class IntakeClarifierAgent:
    """
    Forensic Geotechnical Intake & Gap Analyst (intake_clarifier.yaml).
    Inspects uploaded project files (.xlsx, .csv, .docx, .pdf, notes, images) and project metadata
    via Tier-1 engine to produce high-value project-specific ClarificationItems before drafting.
    """

    async def analyze(
        self,
        project: Project,
        input_files: list[ProjectInputFile],
        prompt: str = "",
        api_key_override: str = "",
    ) -> list[ClarificationItem]:
        file_previews: list[dict[str, Any]] = []
        for f in input_files:
            summary = f.parsed_summary_json or {}
            tables_preview = [
                {
                    "title": tbl.get("title"),
                    "kind": tbl.get("kind"),
                    "columns": tbl.get("columns", []),
                    "sample_rows": (tbl.get("rows") or [])[:12],
                    "row_count": tbl.get("row_count", 0),
                }
                for tbl in summary.get("tables", [])
            ]
            file_previews.append(
                {
                    "filename": f.filename,
                    "kind": summary.get("kind"),
                    "metrics": summary.get("extracted_metrics", {}),
                    "tables": tables_preview,
                    "raw_text_excerpt": (summary.get("raw_text") or "")[:3000],
                }
            )

        sys_prompt = _load_intake_prompt()
        user_msg = json.dumps(
            {
                "project_title": project.title,
                "subtitle": project.subtitle,
                "document_type": project.document_type,
                "client": project.client_name,
                "contractor": project.contractor_name,
                "client_ref_code": project.client_ref_code,
                "contractor_ref_code": project.contractor_ref_code,
                "water_depth_range": project.water_depth_range,
                "vessel_name": project.vessel_name,
                "prompt": prompt,
                "files": file_previews,
            }
        )

        raw = await llm_router.complete_tier1(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            api_key_override=api_key_override,
            max_tokens=2048,
        )

        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.strip("`").strip()
                if clean.lower().startswith("json"):
                    clean = clean[4:].strip()
            start_b = clean.find("{")
            end_b = clean.rfind("}")
            if start_b != -1 and end_b != -1:
                clean = clean[start_b : end_b + 1]
            parsed = json.loads(clean)
            result: list[ClarificationItem] = []
            for row in parsed.get("items", [])[:5]:
                q_text = str(row.get("question_text") or "").strip()
                if not q_text:
                    continue
                result.append(
                    ClarificationItem(
                        project_id=project.id,
                        category=str(row.get("category") or "missing_data"),
                        question_text=q_text,
                        context_reference=str(
                            row.get("context_reference") or "Forensic Intake Audit"
                        )[:250],
                        suggested_answer=(
                            str(row.get("suggested_answer")).strip()
                            if row.get("suggested_answer")
                            else "Confirmed per standard project specification"
                        ),
                        is_resolved=False,
                        omit_section=False,
                    )
                )
            return result
        except Exception as exc:
            raise ExternalProviderError(
                f"Intake & Clarification Engine received an invalid JSON response: {exc}"
            ) from exc
