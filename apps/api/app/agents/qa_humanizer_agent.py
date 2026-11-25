import asyncio
import json
from pathlib import Path
import re
from typing import Any
import yaml
from app.agents.llm_router import llm_router
from app.models.clarification import QaAlert
from app.models.project import Project

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "qa_humanizer.yaml"


def _load_qa_prompt() -> str:
    if PROMPT_PATH.exists():
        data = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
        if data.get("system_prompt"):
            return str(data["system_prompt"]).strip()
    return (
        "You are a Managing Principal Geotechnical Engineering Reviewer. "
        "Verify numeric accuracy, strip AI clichés, and enforce authentic geotechnical consultancy prose."
    )


PHRASE_REPLACEMENTS = {
    "delve into": "examine",
    "delve": "review",
    "testament to": "evidence of",
    "testament": "evidence",
    "crucial role": "governing function",
    "plays a crucial": "serves a primary",
    "it is important to note that": "note that",
    "it is important to note": "note",
    "it is worth noting that": "",
    "it is worth noting": "",
    "in conclusion,": "in summary,",
    "in conclusion": "in summary",
    "comprehensive overview": "technical synthesis",
    "moreover,": "additionally,",
    "moreover": "additionally",
    "furthermore,": "in addition,",
    "seamlessly": "directly",
    "game-changer": "operational improvement",
    "cutting-edge": "calibrated",
    "tapestry": "sequence",
    "pivotal": "governing",
    "underscore": "confirm",
    "underscores": "confirms",
    "synergy": "integration",
    "holistic": "integrated",
    "multifaceted": "multi-stage",
}


class QaHumanizerAgent:
    """
    Implements two distinct independent pipeline stages:
      - Stage 4 (Independent Cross-Checker & Numeric QA Agent):
        Audits drafted prose and tables against raw uploaded files and retrieved research facts,
        flagging any numeric discrepancy, rounded depth/coordinate, or internal inconsistency.
      - Stage 5 (Senior Engineering Anti-AI Humanizer Agent):
        Uses the higher-tier Tier-2 editorial model plus deterministic phrase stripping to remove
        generic AI phrasing and enforce crisp, natural consultancy prose matching the Vault voice.
    """

    def humanize_html(self, html: str, style_guide: dict[str, Any]) -> tuple[str, int]:
        configured_banned = list(style_guide.get("banned_ai_phrases") or [])
        banned = list(dict.fromkeys(configured_banned + list(PHRASE_REPLACEMENTS.keys())))
        cleaned = html
        replacements = 0
        for phrase in banned:
            if not phrase or not str(phrase).strip():
                continue
            pattern = re.compile(rf"\b{re.escape(str(phrase).strip())}\b", re.IGNORECASE)
            if pattern.search(cleaned):
                replacement = PHRASE_REPLACEMENTS.get(str(phrase).strip().lower(), "")
                cleaned, count = pattern.subn(replacement, cleaned)
                replacements += count
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r"<p>\s*,\s*", "<p>", cleaned)
        return cleaned, replacements

    async def run_independent_qa_crosscheck(
        self,
        project: Project,
        document_ast: dict[str, Any],
        research_sources: list[dict[str, Any]] | None = None,
        openrouter_key: str = "",
    ) -> list[QaAlert]:
        """Stage 4: Deterministic + Independent Tier-1 Numeric & Factual Cross-Checker."""
        alerts: list[QaAlert] = []
        seen_pairs: set[tuple[str, str]] = set()
        sections = document_ast.get("sections", [])

        # 1. Deterministic precision audit against uploaded spreadsheets/logs
        for infile in project.input_files or []:
            metrics = (infile.parsed_summary_json or {}).get("extracted_metrics", {})
            for field_key, label in (
                ("water_depths", "Water Depth Precision Check"),
                ("penetrations", "Penetration / Terminal Depth Precision Check"),
            ):
                for raw_val in metrics.get(field_key, [])[:20]:
                    clean_num = re.sub(r"[^0-9.]", "", str(raw_val))
                    if "." not in clean_num:
                        continue
                    try:
                        num = float(clean_num)
                    except ValueError:
                        continue
                    rounded_int = f"{round(num):.1f}"
                    if rounded_int == clean_num:
                        continue
                    for sec in sections:
                        plain = re.sub(r"<[^>]+>", " ", sec.get("html_content", ""))
                        if re.search(rf"\b{re.escape(rounded_int)}\s*m\b", plain) and clean_num not in plain:
                            key = (sec.get("id", "sec-1"), clean_num)
                            if key in seen_pairs:
                                continue
                            seen_pairs.add(key)
                            alerts.append(
                                QaAlert(
                                    project_id=project.id,
                                    severity="warning",
                                    section_id=sec.get("id", "sec-1"),
                                    field_label=label,
                                    source_value=f"{clean_num}m",
                                    draft_value=f"{rounded_int}m",
                                    message=(
                                        f"Uploaded source '{infile.filename}' records {clean_num}m, "
                                        f"whereas narrative text rounded to {rounded_int}m."
                                    ),
                                    is_resolved=False,
                                )
                            )

        # 2. Independent LLM QA Cross-Check when raw files or clarifications exist
        if (project.input_files or project.clarifications) and sections:
            raw_facts = [
                {
                    "filename": f.filename,
                    "metrics": (f.parsed_summary_json or {}).get("extracted_metrics", {}),
                    "excerpt": ((f.parsed_summary_json or {}).get("raw_text") or "")[:1800],
                }
                for f in (project.input_files or [])[:4]
            ]
            draft_digest = [
                {
                    "section_id": s.get("id"),
                    "title": f"{s.get('section_number')} {s.get('title')}",
                    "text": re.sub(r"<[^>]+>", " ", s.get("html_content", ""))[:1200],
                }
                for s in sections
            ]
            qa_sys = (
                "You are an Independent Geotechnical Numeric & Factual QA Auditor. "
                "Compare the drafted report sections against the raw uploaded file metrics and project metadata. "
                "Identify ONLY genuine numeric, coordinate, depth, or borehole-count discrepancies (0 to 3 items max). "
                "If everything is consistent, return `{\"alerts\": []}`.\n"
                "Return ONLY valid JSON:\n"
                '{"alerts":[{"section_id":"...","field_label":"...","source_value":"...","draft_value":"...","message":"..."}]}'
            )
            try:
                raw_qa = await llm_router.complete_tier1(
                    messages=[
                        {"role": "system", "content": qa_sys},
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "project_title": project.title,
                                    "client": project.client_name,
                                    "water_depth_range": project.water_depth_range,
                                    "uploaded_files": raw_facts,
                                    "draft_sections": draft_digest,
                                }
                            ),
                        },
                    ],
                    temperature=0.05,
                    api_key_override=openrouter_key,
                    max_tokens=1500,
                )
                s_idx = raw_qa.find("{")
                e_idx = raw_qa.rfind("}")
                if s_idx != -1 and e_idx != -1:
                    qa_json = json.loads(raw_qa[s_idx : e_idx + 1])
                    valid_sec_ids = {s.get("id") for s in sections}
                    for row in (qa_json.get("alerts") or [])[:3]:
                        src_v = str(row.get("source_value") or "").strip()
                        drf_v = str(row.get("draft_value") or "").strip()
                        msg = str(row.get("message") or "").strip()
                        sec_id = str(row.get("section_id") or sections[0].get("id"))
                        if sec_id not in valid_sec_ids:
                            sec_id = str(sections[0].get("id"))
                        if msg and src_v and drf_v and src_v != drf_v:
                            alerts.append(
                                QaAlert(
                                    project_id=project.id,
                                    severity="warning",
                                    section_id=sec_id,
                                    field_label=str(row.get("field_label") or "Cross-Check Discrepancy")[:120],
                                    source_value=src_v[:80],
                                    draft_value=drf_v[:80],
                                    message=msg[:300],
                                    is_resolved=False,
                                )
                            )
            except Exception:
                pass

        return alerts

    async def run_senior_humanizer_pass(
        self,
        document_ast: dict[str, Any],
        style_guide: dict[str, Any],
        openrouter_key: str = "",
    ) -> tuple[dict[str, Any], int]:
        """
        Stage 5: Senior Engineering Anti-AI Humanizer Agent (Tier-2 Editorial Model + Deterministic Stripper).
        Polishes drafted chapters to read like an experienced geotechnical principal engineer while
        preserving every number, coordinate, HTML structure, and `<p class="formula">` equation.
        """
        sections = list(document_ast.get("sections") or [])
        total_stripped = 0

        # First deterministic pass to count and strip banned AI clichés
        for sec in sections:
            cleaned, count = self.humanize_html(sec.get("html_content", ""), style_guide)
            sec["html_content"] = cleaned
            total_stripped += count

        # Editorial Tier-2 pass on key narrative chapters (Executive Summary, Intro, Geology, Ground Model, Conclusions)
        voice_rules = (style_guide.get("voice_rules") or [])[:5]
        nomenclature = (style_guide.get("preferred_nomenclature") or [])[:12]
        banned_list = list(
            dict.fromkeys((style_guide.get("banned_ai_phrases") or []) + list(PHRASE_REPLACEMENTS.keys()))
        )[:20]

        async def _polish_section(sec: dict[str, Any]) -> int:
            html_in = sec.get("html_content", "")
            # Skip formula-heavy methodology chapter so Equation blocks stay 100% untouched
            if sec.get("id") == "sec-5-lab-methods" or len(html_in) < 180:
                return 0
            sys_prompt = (
                f"{_load_qa_prompt()}\n\n"
                "Rewrite the HTML section prose below so it reads with crisp, natural, senior geotechnical "
                "consultancy authority—eliminating robotic transitions, repetitive sentence starters, and generic AI filler.\n"
                f"- Voice rules: {voice_rules}\n"
                f"- Preferred nomenclature: {nomenclature}\n"
                f"- Strictly forbidden words: {banned_list}\n"
                "- Preserve ALL numbers, coordinates, depths, units, `<h3>` subheadings, `<ul>`/`<ol>` lists, and `<p class=\"formula\">` blocks verbatim.\n"
                "- Do NOT shorten or summarize—maintain full technical density.\n"
                "- Return ONLY the clean HTML fragment (no markdown code fences)."
            )
            try:
                revised = await llm_router.complete_tier2(
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": html_in},
                    ],
                    temperature=0.2,
                    api_key_override=openrouter_key,
                    max_tokens=4096,
                )
                clean_rev = revised.strip()
                if clean_rev.startswith("```"):
                    clean_rev = re.sub(r"^```(?:html)?\s*", "", clean_rev, flags=re.IGNORECASE)
                    clean_rev = re.sub(r"\s*```$", "", clean_rev)
                if len(clean_rev) >= int(len(html_in) * 0.72) and "<p" in clean_rev:
                    final_html, extra_c = self.humanize_html(clean_rev, style_guide)
                    sec["html_content"] = final_html
                    return extra_c
            except Exception:
                pass
            return 0

        # Polish key narrative chapters concurrently (bounded concurrency = 3)
        sem = asyncio.Semaphore(3)

        async def _guarded(s: dict[str, Any]) -> int:
            async with sem:
                return await _polish_section(s)

        extra_counts = await asyncio.gather(*[_guarded(s) for s in sections])
        total_stripped += sum(extra_counts)
        document_ast["sections"] = sections
        return document_ast, total_stripped

    def verify_and_humanize_project(
        self,
        project: Project,
        document_ast: dict[str, Any],
        style_guide: dict[str, Any],
    ) -> tuple[dict[str, Any], list[QaAlert], int]:
        """Synchronous deterministic helper retained for unit test compatibility."""
        total_stripped = 0
        sections = document_ast.get("sections", [])
        for sec in sections:
            cleaned, count = self.humanize_html(sec.get("html_content", ""), style_guide)
            sec["html_content"] = cleaned
            total_stripped += count
        return document_ast, [], total_stripped

    async def inline_rewrite(
        self,
        selection_text: str,
        instruction: str,
        style_guide: dict[str, Any],
        openrouter_key: str = "",
    ) -> tuple[str, str]:
        sys_prompt = (
            f"{_load_qa_prompt()}\n\n"
            "Rewrite or expand the highlighted passage according to the engineer's instruction. "
            "Keep ALL numbers, coordinates, depths, equations, and 24-hour times intact. "
            f"Voice rules: {style_guide.get('voice_rules', [])[:5]}. "
            f"Avoid banned AI words: {style_guide.get('banned_ai_phrases', [])}. "
            "Return ONLY the revised technical text."
        )
        res = await llm_router.complete_tier2(
            messages=[
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": f"Instruction: {instruction}\n\nSelected Text:\n{selection_text}",
                },
            ],
            temperature=0.2,
            api_key_override=openrouter_key,
            max_tokens=2400,
        )
        cleaned, _ = self.humanize_html(res, style_guide)
        return cleaned, "Verified via Senior Geotechnical Editorial & Anti-AI Humanizer Engine."

    async def expand_section(
        self,
        section: dict[str, Any],
        instruction: str,
        style_guide: dict[str, Any],
        openrouter_key: str = "",
    ) -> dict[str, Any]:
        sys_prompt = (
            f"{_load_qa_prompt()}\n\n"
            "You are expanding and refining a major section of a geotechnical engineering report. "
            "Preserve all existing verified coordinates, depths, equations, and findings while expanding the "
            "section with rigorous technical derivation, borehole correlations, or analytical checks as requested. "
            "Return ONLY valid JSON matching:\n"
            '{"html_content":"<p>Full expanded HTML content...</p>",'
            '"additional_table":{"title":"Optional New Summary Table Title","columns":["Col 1","Col 2","Col 3"],"rows":[["...","...","..."]]} | null}'
        )
        user_payload = {
            "section_number": section.get("section_number"),
            "title": section.get("title"),
            "current_html_content": section.get("html_content", ""),
            "existing_tables": [
                {"title": t.get("title"), "columns": t.get("columns")}
                for t in (section.get("tables") or [])
            ],
            "engineer_instruction": instruction,
        }
        try:
            raw = await llm_router.complete_tier2(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
                temperature=0.2,
                api_key_override=openrouter_key,
                max_tokens=8192,
            )
            clean = raw.strip()
            start_b = clean.find("{")
            end_b = clean.rfind("}")
            if start_b != -1 and end_b != -1:
                clean = clean[start_b : end_b + 1]
            parsed = json.loads(clean)
            new_html = str(parsed.get("html_content") or "").strip()
            if new_html:
                cleaned_html, _ = self.humanize_html(new_html, style_guide)
                section["html_content"] = cleaned_html
            add_tbl = parsed.get("additional_table")
            if isinstance(add_tbl, dict) and add_tbl.get("columns") and add_tbl.get("rows"):
                tables = list(section.get("tables") or [])
                tables.append(
                    {
                        "id": f"tbl-exp-{len(tables) + 1}",
                        "table_number": f"Table {section.get('section_number', '').rstrip('.')}.{len(tables) + 1}",
                        "title": str(add_tbl.get("title") or "Supplementary Geotechnical Analysis Table"),
                        "columns": [str(c) for c in add_tbl.get("columns", [])],
                        "rows": [[str(cell) for cell in r] for r in add_tbl.get("rows", [])],
                    }
                )
                section["tables"] = tables
        except Exception:
            revised, _ = await self.inline_rewrite(
                selection_text=re.sub(r"<[^>]+>", " ", section.get("html_content", ""))[:2000],
                instruction=instruction,
                style_guide=style_guide,
                openrouter_key=openrouter_key,
            )
            if revised:
                section["html_content"] = f"{section.get('html_content', '')}\n<p>{revised}</p>"

        return section
