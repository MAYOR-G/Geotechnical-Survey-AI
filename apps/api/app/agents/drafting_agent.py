import json
from pathlib import Path
import re
import time
from typing import Any, Awaitable, Callable, Optional
import yaml
from app.agents.llm_router import llm_router
from app.models.project import Project
from app.repositories.vault_repo import VaultRepository
from app.services.chart_generator import (
    ScientificChartGenerator,
    extract_project_chart_params,
)
from app.services.image_search_service import ImageSearchService
from app.services.storage_service import StorageService

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "section_drafter.yaml"

StepCallback = Optional[Callable[[str, dict[str, Any]], Awaitable[None]]]


def _load_drafter_prompts() -> dict[str, Any]:
    if PROMPT_PATH.exists():
        return yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
    return {}


def _extract_json_dict(raw: str) -> dict[str, Any]:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean)
    start_b = clean.find("{")
    end_b = clean.rfind("}")
    if start_b != -1 and end_b != -1 and end_b > start_b:
        clean = clean[start_b : end_b + 1]
    return json.loads(clean)


STANDARD_ABBREVIATIONS: list[dict[str, str]] = [
    {"term": "API", "definition": "American Petroleum Institute"},
    {"term": "ASCE", "definition": "American Society of Civil Engineers"},
    {"term": "ASME", "definition": "American Society of Mechanical Engineers"},
    {"term": "ASTM", "definition": "American Society for Testing and Materials"},
    {"term": "BGL", "definition": "Below Existing Ground Level"},
    {"term": "BH", "definition": "Geotechnical Exploratory Borehole"},
    {"term": "BHA", "definition": "Bottom Hole Assembly"},
    {"term": "BRF", "definition": "Below the River-Floor"},
    {"term": "BS", "definition": "British Standard (BS 1377: 1990 / BS 5930)"},
    {"term": "Cc", "definition": "Coefficient of Curvature (PSD) / Compression Index (Consolidation)"},
    {"term": "CH", "definition": "High-Plasticity Inorganic Clay (USCS) / Alignment Chainage"},
    {"term": "CL", "definition": "Low-to-Medium Plasticity Inorganic Clay (USCS)"},
    {"term": "CPT / CPTu", "definition": "Cone Penetration Test / Piezocone Penetration Test with Pore Pressure"},
    {"term": "Cs", "definition": "Swelling / Recompression Index"},
    {"term": "Cu / cu", "definition": "Coefficient of Uniformity (D60/D10) / Undrained Shear Strength (kPa)"},
    {"term": "Cv", "definition": "Coefficient of Consolidation (m²/yr)"},
    {"term": "DGPS", "definition": "Differential Global Positioning System"},
    {"term": "DP-2", "definition": "Dynamic Positioning Class 2 Survey Vessel"},
    {"term": "EN 1997", "definition": "Eurocode 7: Geotechnical Design (Part 1 & Part 2)"},
    {"term": "Fs", "definition": "Factor of Safety"},
    {"term": "Gs / SG", "definition": "Specific Gravity of Soil Solids / Drilling Fluid Specific Gravity"},
    {"term": "HDD", "definition": "Horizontal Directional Drilling"},
    {"term": "ISO 19901-8", "definition": "Marine Soil Investigations for Offshore Structures"},
    {"term": "LAT", "definition": "Lowest Astronomical Tide"},
    {"term": "LL", "definition": "Liquid Limit (%)"},
    {"term": "LLWL", "definition": "Low-Low Water Level"},
    {"term": "mBSF", "definition": "Metres Below Seabed / Seafloor"},
    {"term": "MH", "definition": "High-Plasticity Elastic or Organic Silt (USCS)"},
    {"term": "Mv", "definition": "Coefficient of Volume Compressibility (m²/MN)"},
    {"term": "OCR", "definition": "Overconsolidation Ratio (p'c / σ'v0)"},
    {"term": "OD", "definition": "Nominal Outside Diameter"},
    {"term": "OML", "definition": "Oil Mining Lease"},
    {"term": "PCPT", "definition": "Piezocone Penetration Test"},
    {"term": "PI", "definition": "Plasticity Index (LL - PL, %)"},
    {"term": "PL", "definition": "Plastic Limit (%)"},
    {"term": "PSD", "definition": "Particle Size Distribution"},
    {"term": "PWD", "definition": "Pressure-While-Drilling Downhole Annular Pressure Sub"},
    {"term": "qc", "definition": "Cone Tip Resistance (MPa)"},
    {"term": "RoC", "definition": "Radius of Curvature (m)"},
    {"term": "SMYS", "definition": "Specified Minimum Yield Strength"},
    {"term": "SOW", "definition": "Scope of Work"},
    {"term": "SPT", "definition": "Standard Penetration Test (N-value blows per 300 mm)"},
    {"term": "UU", "definition": "Unconsolidated Undrained Triaxial Compression Test"},
    {"term": "VES", "definition": "Vertical Electrical Sounding (Geoelectric Resistivity Survey)"},
    {"term": "WGS84", "definition": "World Geodetic System 1984"},
]

STANDARD_GEOTECH_CODES_TABLE: dict[str, Any] = {
    "id": "tbl-1-2",
    "table_number": "Table 1.2",
    "title": "Referenced Geotechnical Standards, Codes of Practice and Authoritative Texts",
    "columns": ["Standard / Reference", "Title & Technical Scope"],
    "rows": [
        ["BS 1377: 1990 (Parts 1–9)", "Methods of Test for Soils for Civil Engineering Purposes (Classification, Compressibility, Shear Strength & Chemical Tests)"],
        ["Eurocode 7: EN 1997-1 & EN 1997-2", "Geotechnical Design — General Rules, Ground Investigation and Laboratory/Field Testing"],
        ["BS 5930: 2015+A1:2020", "Code of Practice for Ground Investigations and Soil/Rock Logging"],
        ["ISO 19901-8: 2014 / API RP 2GEO", "Marine Soil Investigations & Geotechnical Foundation Design Considerations for Offshore Structures"],
        ["ASTM D4318 / D3080 / C1580 / D1411", "Atterberg Limits, Direct Shear Testing, Water-Soluble Sulphate & Chloride Determinations"],
        ["ASTM F1962-20 / ASME B31.4 & B31.8", "Maxi-Horizontal Directional Drilling Pipeline Placement & Longitudinal/Combined Stress Verification"],
        ["T. Lunne, P. K. Robertson & J. J. M. Powell (1997)", "Cone Penetration Testing in Geotechnical Practice"],
        ["G. E. Barnes (2016) & R. F. Craig (2004)", "Soil Mechanics: Principles and Practice"],
    ],
}

MANDATORY_LAB_FORMULAS: list[str] = [
    '<p class="formula"><strong>Equation 5.1 (Natural Moisture Content — BS 1377: Part 2):</strong> w = [(M2 - M1) / (M3 - M1)] × 100%</p>',
    '<p class="formula"><strong>Equation 5.2 (Gradation Uniformity, Curvature &amp; Permeability):</strong> Cu = D60 / D10 ;   Cc = (D30)² / (D10 × D60) ;   k = C_H × (D10)²</p>',
    '<p class="formula"><strong>Equation 5.3 (Atterberg Plasticity &amp; Liquidity Index):</strong> PI = LL - PL ;   LI = (w - PL) / PI</p>',
    '<p class="formula"><strong>Equation 5.4 (Mohr-Coulomb &amp; Undrained Shear Strength):</strong> τ_f = c\' + σ\'_n × tan(φ\') ;   Cu = (σ1 - σ3)_f / 2</p>',
    '<p class="formula"><strong>Equation 5.5 (1D Oedometer Consolidation — BS 1377: Part 5):</strong> Cc = -Δe / Δlog10(σ\'_v) ;   mv = [Δe / (1 + e0)] × (1 / Δσ\'_v) ;   cv = (T50 × H_d²) / t50 ;   OCR = p\'_c / σ\'_v0</p>',
    '<p class="formula"><strong>Equation 5.6 (Unit Weights):</strong> γ_bulk = ρ_bulk × g ;   γ_dry = γ_bulk / (1 + w) ;   γ\' = γ_bulk - γ_w</p>',
]


class StyleDraftingAgent:
    """
    Stage-3 Iterative Section-by-Section Technical Author.
    Never generates the whole report in a single call and never injects canned fallback reports.
    Executes a 7-stage sequential authoring loop retrieving per-section Knowledge Vault context,
    verified external web research, deterministic pandas tables, and Tri-Source visuals
    (Vault Gallery + Cached External Technical Images + Data-Driven Matplotlib Scientific Plots).
    """

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()
        self.chart_gen = ScientificChartGenerator(self.storage)
        self.image_search = ImageSearchService(self.storage)

    def _is_offshore_archetype(self, project: Project, intake_texts: list[str]) -> bool:
        combined = (
            f"{project.title} {project.subtitle} {project.document_type} {project.vessel_name} "
            + " ".join(intake_texts)
        ).lower()
        if any(
            k in combined
            for k in (
                "hdd",
                "directional drilling",
                "river crossing",
                "bore path",
                "trenchless",
                "airstrip",
            )
        ):
            return False
        if any(
            k in combined
            for k in (
                "offshore",
                "marine",
                "oml",
                "dp-2",
                "vessel",
                "moonpool",
                "seabed",
                "mbsf",
                "pcpt",
                "subsea",
            )
        ):
            return True
        return False

    def _find_gallery_match(
        self, gallery_assets: list[Any], keywords: tuple[str, ...]
    ) -> tuple[str | None, str | None, str | None]:
        for a in gallery_assets:
            if getattr(a, "category", "") in ("logo", "signature"):
                continue
            hay = f"{a.title} {a.default_caption} {' '.join(a.tags or [])}".lower()
            if any(k in hay for k in keywords):
                return a.id, a.file_url, a.default_caption
        return None, None, None

    async def _resolve_or_search_visual(
        self,
        vault_repo: VaultRepository,
        gallery_assets: list[Any],
        vault_keywords: tuple[str, ...],
        external_query: str,
        fallback_title: str,
        category: str,
        tavily_key: str = "",
    ) -> tuple[str | None, str | None, str | None]:
        aid, aurl, acap = self._find_gallery_match(gallery_assets, vault_keywords)
        if aurl:
            return aid, aurl, acap

        cached = await self.image_search.find_and_cache_best_visual(
            query=external_query,
            fallback_title=fallback_title,
            category=category,
            tavily_key_override=tavily_key,
        )
        if cached:
            saved = await vault_repo.create_gallery_asset(cached)
            gallery_assets.append(saved)
            return saved.id, saved.file_url, saved.default_caption
        return None, None, None

    async def draft_document(
        self,
        project: Project,
        style_guide: dict[str, Any],
        vault_repo: VaultRepository,
        openrouter_key: str = "",
        tavily_key: str = "",
        research_sources: list[dict[str, Any]] | None = None,
        prompt_notes: str = "",
        force_regenerate: bool = False,
        step_callback: StepCallback = None,
    ) -> dict[str, Any]:
        # Fail fast if OPENROUTER_API_KEY is missing — never silently return canned prose
        llm_router._require_api_key(openrouter_key)

        existing_ast = project.document_ast_json or {}
        if existing_ast.get("sections") and not prompt_notes.strip() and not force_regenerate:
            return existing_ast

        prompts_cfg = _load_drafter_prompts()
        global_sys = str(prompts_cfg.get("global_system_directive") or "").strip()

        # 1. Gather deterministic tables & raw notes from uploaded ProjectInputFiles
        coord_tables: list[dict[str, Any]] = []
        borehole_tables: list[dict[str, Any]] = []
        other_tables: list[dict[str, Any]] = []
        intake_texts: list[str] = []

        for infile in project.input_files or []:
            summary = infile.parsed_summary_json or {}
            for tbl in summary.get("tables") or []:
                tbl_copy = dict(tbl)
                if tbl.get("kind") == "coordinate_table":
                    coord_tables.append(tbl_copy)
                elif tbl.get("kind") == "borehole_profile":
                    borehole_tables.append(tbl_copy)
                else:
                    other_tables.append(tbl_copy)
            raw_text = (summary.get("raw_text") or "").strip()
            if raw_text:
                intake_texts.append(f"[{infile.filename}]\n{raw_text[:4000]}")

        is_offshore = self._is_offshore_archetype(project, intake_texts)

        # 2. Retrieve Knowledge Vault documents, gallery visuals, and blueprint
        vault_docs = await vault_repo.list_documents()
        gallery_assets = await vault_repo.list_gallery()
        layout_blueprint = next(
            (d.pdf_layout_blueprint_json for d in vault_docs if d.pdf_layout_blueprint_json),
            {},
        )

        # 3. Tri-Source Visual Intelligence:
        #    Tier 3: Data-driven scientific Matplotlib plots
        safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", project.contractor_ref_code or project.id)[:36]
        chart_params = extract_project_chart_params(project)
        if step_callback:
            await step_callback(
                "step_start",
                {
                    "id": "visual-sourcing",
                    "kind": "tool",
                    "status": "running",
                    "title": "Sourcing Tri-Tier engineering visuals (Vault Gallery, External Maps & Scientific Matplotlib Plots)...",
                    "detail": "Generating 240-DPI geotechnical plots & caching verified technical figures",
                },
            )
        t_vis = time.perf_counter()
        scientific_charts = self.chart_gen.generate_all_suite(
            project_slug=safe_slug,
            is_offshore=is_offshore,
            custom_params=chart_params,
        )

        #    Tier 1 + Tier 2: Vault Gallery or Live External Image Discovery & Local Caching
        region_hint = project.subtitle or project.title
        map_id, map_url, map_cap = await self._resolve_or_search_visual(
            vault_repo=vault_repo,
            gallery_assets=gallery_assets,
            vault_keywords=("geological map", "regional geology", "map of", "basin", "oml"),
            external_query=f"{region_hint} regional geological map sedimentary basin",
            fallback_title=f"Regional Geological & Basin Setting Map ({project.title})",
            category="map",
            tavily_key=tavily_key,
        )
        equip_id, equip_url, equip_cap = await self._resolve_or_search_visual(
            vault_repo=vault_repo,
            gallery_assets=gallery_assets,
            vault_keywords=(
                ("vessel", "dolphin", "heave", "dp-2", "moonpool", "seabed")
                if is_offshore
                else ("drill rig", "rotary", "hdd", "percussion", "barge", "cpt")
            ),
            external_query=(
                "offshore geotechnical survey vessel heave compensated drill rig"
                if is_offshore
                else "geotechnical rotary drilling rig horizontal directional drilling spread"
            ),
            fallback_title=(
                "Offshore Geotechnical Survey Vessel & Drilling Spread"
                if is_offshore
                else "Geotechnical Drilling & In-Situ Testing Spread"
            ),
            category="vessel" if is_offshore else "drill_rig",
            tavily_key=tavily_key,
        )

        if step_callback:
            await step_callback(
                "step_done",
                {
                    "id": "visual-sourcing",
                    "kind": "tool",
                    "status": "done",
                    "title": "Prepared Tri-Source figures, cached maps, and 5 scientific engineering plots",
                    "duration": max(1, int((time.perf_counter() - t_vis) * 1000)),
                    "output": (
                        f"Generated `5 scientific Matplotlib plots` · "
                        f"`{'Resolved' if map_url else 'Slot ready'}` regional map · "
                        f"`{'Resolved' if equip_url else 'Slot ready'}` field equipment figure."
                    ),
                },
            )

        clarification_notes = [
            f"{c.context_reference}: {c.user_response or c.suggested_answer}"
            for c in (project.clarifications or [])
            if not c.omit_section and (c.user_response or c.suggested_answer)
        ]

        research_digest = [
            f"[{i + 1}] {s.get('title')} ({s.get('site')}): {s.get('snippet', '')[:320]}"
            for i, s in enumerate(research_sources or [])
        ]

        shared_context = {
            "project": {
                "title": project.title,
                "subtitle": project.subtitle,
                "document_type": project.document_type,
                "archetype": (
                    "OFFSHORE_MARINE_GEOTECHNICAL_FIELD_REPORT"
                    if is_offshore
                    else "GEOTECHNICAL_SITE_AND_LABORATORY_INVESTIGATION_REPORT"
                ),
                "client_name": project.client_name or "Client / Operator",
                "contractor_name": project.contractor_name or "Lead Geotechnical Contractor",
                "client_ref_code": project.client_ref_code or "",
                "contractor_ref_code": project.contractor_ref_code or "",
                "revision_number": project.revision_number or "Rev 01",
                "water_depth_range": project.water_depth_range or "",
                "vessel_name": project.vessel_name or "",
            },
            "style_guide": {
                "tone": style_guide.get("tone")
                or "Crisp, objective geotechnical engineering consultancy prose",
                "voice_rules": (style_guide.get("voice_rules") or [])[:6],
                "preferred_nomenclature": (style_guide.get("preferred_nomenclature") or [])[:16],
                "banned_ai_phrases": (style_guide.get("banned_ai_phrases") or [])[:16],
            },
            "uploaded_intake_excerpts": intake_texts[:4],
            "uploaded_table_summaries": [
                {
                    "title": t.get("title"),
                    "columns": t.get("columns"),
                    "row_count": len(t.get("rows") or []),
                    "sample_rows": (t.get("rows") or [])[:15],
                }
                for t in (coord_tables + borehole_tables + other_tables)[:6]
            ],
            "verified_clarifications": clarification_notes,
            "external_and_vault_research": research_digest,
            "engineer_instruction": prompt_notes,
        }

        # =====================================================================
        # 7-CALL SEQUENTIAL SECTION-BY-SECTION AUTHORING PIPELINE
        # =====================================================================
        chapter_specs: list[dict[str, Any]] = [
            {
                "step_id": "draft-call-1",
                "step_title": "Drafting Front Matter & Section 0.0: Executive Summary...",
                "step_detail": "Synthesizing commission, investigation scope, subsurface controls & design summary table",
                "vault_query": f"{project.title} executive summary geotechnical findings recommendations",
                "sections_spec": [
                    {
                        "id": "sec-exec-summary",
                        "section_number": "0.0",
                        "title": "EXECUTIVE SUMMARY",
                        "category": "Executive_Summary",
                        "required_tables": [
                            {
                                "table_number": "Table 0.1",
                                "title": "Executive Summary of Principal Geotechnical Findings, Design Parameters & Recommendations",
                                "min_rows": 6,
                            }
                        ],
                        "directive": (
                            "Write a thorough 6-to-8 paragraph Executive Summary strictly tailored to this project's title, client, contractor, "
                            "location, uploaded data, and verified clarifications. Never invent unrelated project names. Summarize the investigation "
                            "commission, exploratory scope, subsurface soil stratigraphy, governing strength/compressibility parameters, geohazards, "
                            "and actionable foundation or bore-path engineering recommendations, accompanied by Table 0.1."
                        ),
                    }
                ],
            },
            {
                "step_id": "draft-call-2",
                "step_title": "Drafting Section 1.0: Introduction, Scope of Work & Applicable Standards...",
                "step_detail": "Authoring background, itemized field/lab scope, and international standards matrices",
                "vault_query": f"{project.title} introduction project background scope of work standards BS 1377",
                "sections_spec": [
                    {
                        "id": "sec-1-intro",
                        "section_number": "1.0",
                        "title": "INTRODUCTION AND SCOPE OF WORK",
                        "category": "Introduction",
                        "required_tables": [
                            {
                                "table_number": "Table 1.3",
                                "title": "Project-Specific Investigation Scope & Applicable Design Codes",
                                "min_rows": 6,
                            }
                        ],
                        "directive": (
                            "Draft Section 1.0 with subsections `<h3>1.1 Project Background and Objectives</h3>`, "
                            "`<h3>1.2 Executed Scope of Work</h3>` (detailed itemized bullet list of field & lab activities), "
                            "`<h3>1.3 Abbreviations and Nomenclature</h3>`, and `<h3>1.4 Applicable Codes, Standards and Design Guidelines</h3>`."
                        ),
                    }
                ],
            },
            {
                "step_id": "draft-call-3",
                "step_title": "Drafting Section 2.0: Site Description, Geomorphology & Regional Geology...",
                "step_detail": "Integrating verified geological formations, depositional setting, and regional map",
                "vault_query": f"{project.title} {project.subtitle} site description geomorphology regional geology stratigraphy",
                "sections_spec": [
                    {
                        "id": "sec-2-geology",
                        "section_number": "2.0",
                        "title": "SITE DESCRIPTION AND REGIONAL GEOLOGY",
                        "category": "Introduction",
                        "required_tables": [
                            {
                                "table_number": "Table 2.1",
                                "title": "Regional Lithostratigraphic Units & Local Depositional Characteristics",
                                "min_rows": 4,
                            }
                        ],
                        "directive": (
                            "Draft Section 2.0 with subsections `<h3>2.1 Geographic Setting, Physiography and Climate</h3>`, "
                            "`<h3>2.2 Local Quaternary Depositional Environment</h3>`, and `<h3>2.3 Regional Basin Stratigraphy and Structural Framework</h3>` "
                            "grounded in the verified research sources and project location."
                        ),
                    }
                ],
            },
            {
                "step_id": "draft-call-4",
                "step_title": "Drafting Sections 3.0 & 4.0: Fieldwork Operations, Coordinates & Soil Stratigraphy...",
                "step_detail": "Embedding deterministic pandas coordinate/borehole sheets & stratigraphic correlation",
                "vault_query": "fieldwork drilling methodology CPT PCPT sampling coordinates soil stratigraphy borehole sequence",
                "sections_spec": [
                    {
                        "id": "sec-3-fieldwork",
                        "section_number": "3.0",
                        "title": "FIELDWORK OPERATIONS AND SURVEYED POSITIONS",
                        "category": "Procedures",
                        "required_tables": (
                            []
                            if coord_tables
                            else [
                                {
                                    "table_number": "Table 3.1",
                                    "title": "Summary of Exploratory Investigation Locations, Depths & Datum Controls",
                                    "min_rows": 5,
                                }
                            ]
                        ),
                        "directive": (
                            "Draft Section 3.0 with `<h3>3.1 Mobilisation, Drilling and Sampling Methodology</h3>`, "
                            "`<h3>3.2 In-Situ Penetration Testing (SPT / CPT / PCPT)</h3>`, and "
                            "`<h3>3.3 Positioning, Datum Control and Field Conditions</h3>`. Reference any uploaded coordinate tables accurately without altering numbers."
                        ),
                    },
                    {
                        "id": "sec-4-stratigraphy",
                        "section_number": "4.0",
                        "title": "SUBSURFACE SOIL STRATIGRAPHY",
                        "category": "Field_Results",
                        "required_tables": (
                            []
                            if borehole_tables
                            else [
                                {
                                    "table_number": "Table 4.1",
                                    "title": "Generalized Subsurface Soil Stratigraphic Sequence & Consistency Profile",
                                    "min_rows": 6,
                                }
                            ]
                        ),
                        "directive": (
                            "Draft Section 4.0 with `<h3>4.1 Subsurface Stratigraphic Correlation</h3>` and "
                            "`<h3>4.2 Groundwater, Seabed / Surface Conditions and Borehole Stability Observations</h3>`, "
                            "honoring exact depths and descriptions from uploaded files where provided."
                        ),
                    },
                ],
            },
            {
                "step_id": "draft-call-5",
                "step_title": "Drafting Sections 5.0 & 6.0: Laboratory Methodologies, Equations & Parameter Analysis...",
                "step_detail": "Authoring BS 1377 / EN 1997-2 formulations, statistical parameter tables & scientific charts",
                "vault_query": "laboratory investigation moisture content particle size atterberg triaxial oedometer consolidation sulphate chloride",
                "sections_spec": [
                    {
                        "id": "sec-5-lab-methods",
                        "section_number": "5.0",
                        "title": "LABORATORY INVESTIGATION METHODOLOGIES AND EQUATIONS",
                        "category": "Procedures",
                        "required_tables": [],
                        "directive": (
                            "Draft Section 5.0 detailing step-by-step BS 1377:1990 & Eurocode 7 EN 1997-2 laboratory testing procedures "
                            "(`<h3>5.1 Natural Moisture Content &amp; Unit Weight</h3>`, `<h3>5.2 Particle Size Distribution &amp; Hydrometer</h3>`, "
                            "`<h3>5.3 Atterberg Consistency Limits</h3>`, `<h3>5.4 Shear Strength Testing (UU Triaxial &amp; Direct Shear)</h3>`, "
                            "`<h3>5.5 One-Dimensional Oedometer Consolidation</h3>`, `<h3>5.6 Soil &amp; Pore-Water Chemical Aggressivity</h3>`) "
                            "with `<p class=\"formula\">` mathematical equations."
                        ),
                    },
                    {
                        "id": "sec-6-lab-results",
                        "section_number": "6.0",
                        "title": "LABORATORY RESULTS AND GEOTECHNICAL PARAMETER INTERPRETATION",
                        "category": "Field_Results",
                        "required_tables": [
                            {
                                "table_number": "Table 6.1",
                                "title": "Summary of Derived Geotechnical Index, Strength & Compressibility Parameters (Cohesive Units)",
                                "min_rows": 7,
                            },
                            {
                                "table_number": "Table 6.2",
                                "title": "Summary of Gradation & Effective Strength Parameters (Granular Sand Units)",
                                "min_rows": 6,
                            },
                        ],
                        "directive": (
                            "Draft Section 6.0 interpreting index classification, Casagrande plasticity (Figure 6.1), moisture/unit-weight profiles (Figure 6.2), "
                            "undrained/drained shear strength profiles (Figure 6.3), compressibility, and chemical test findings."
                        ),
                    },
                ],
            },
            {
                "step_id": "draft-call-6",
                "step_title": "Drafting Sections 7.0 & 8.0: Engineering Ground Model, Design Inputs & Geohazard Risk Register...",
                "step_detail": "Deriving characteristic design units, installation/foundation checks & hazard mitigations",
                "vault_query": "engineering ground model characteristic design parameters geohazard evaluation hydraulic fracture bearing stability",
                "sections_spec": [
                    {
                        "id": "sec-7-ground-model",
                        "section_number": "7.0",
                        "title": "ENGINEERING GROUND MODEL AND DESIGN INPUT PARAMETERS",
                        "category": "Field_Results",
                        "required_tables": [
                            {
                                "table_number": "Table 7.1",
                                "title": "Characteristic Engineering Ground Model & Geotechnical Design Parameters",
                                "min_rows": 5,
                            }
                        ],
                        "directive": (
                            "Draft Section 7.0 establishing the Characteristic Engineering Ground Model (Eurocode 7 characteristic parameter selection, "
                            "lateral continuity across Figure 7.1, effective & undrained design profiles, and foundation / pipeline / HDD design inputs)."
                        ),
                    },
                    {
                        "id": "sec-8-geohazards",
                        "section_number": "8.0",
                        "title": "GEOTECHNICAL HAZARD EVALUATION AND MITIGATION FRAMEWORK",
                        "category": "Field_Results",
                        "required_tables": [
                            {
                                "table_number": "Table 8.1",
                                "title": "Geotechnical Hazard Risk Register, Exposure Rating & Engineering Mitigations",
                                "min_rows": 6,
                            }
                        ],
                        "directive": (
                            "Draft Section 8.0 evaluating all governing site geohazards (e.g., hydraulic fracture / punch-through, borehole or trench wall instability, "
                            "soft clay consolidation settlement, organic/peat horizons, artesian sand heave, scour, and chemical/saline exposure) "
                            "referenced to Table 8.1 and Figure 8.1."
                        ),
                    },
                ],
            },
            {
                "step_id": "draft-call-7",
                "step_title": "Drafting Sections 9.0 & 10.0: Engineering Recommendations, Conclusions & Factual Appendices...",
                "step_detail": "Finalizing numbered actionable engineering controls and compiling factual appendix schedule",
                "vault_query": "discussion engineering recommendations conclusions factual appendices field photographs",
                "sections_spec": [
                    {
                        "id": "sec-9-conclusions",
                        "section_number": "9.0",
                        "title": "ENGINEERING DISCUSSION, RECOMMENDATIONS AND CONCLUSIONS",
                        "category": "Field_Results",
                        "required_tables": [],
                        "directive": (
                            "Draft Section 9.0 synthesizing all field, laboratory, and analytical findings into clear engineering conclusions "
                            "and an ordered list (`<ol><li><strong>...</strong></li></ol>`) of 6 to 8 specific, actionable engineering recommendations."
                        ),
                    },
                    {
                        "id": "sec-10-appendices",
                        "section_number": "10.0",
                        "title": "FACTUAL APPENDICES AND RECORD SCHEDULE",
                        "category": "Appendices",
                        "required_tables": [
                            {
                                "table_number": "Table 10.1",
                                "title": "Schedule of Factual Logs, Laboratory Sheets & Appended Packages",
                                "min_rows": 4,
                            }
                        ],
                        "directive": (
                            "Draft Section 10.0 introducing the Factual Appendices, photographic plates, borehole/CPT logs, "
                            "and external laboratory PDF attachments merged at the end of the deliverable."
                        ),
                    },
                ],
            },
        ]

        all_sections: list[dict[str, Any]] = []
        meta_overrides: dict[str, str] = {}

        for stage_idx, stage in enumerate(chapter_specs):
            t_start = time.perf_counter()
            if step_callback:
                await step_callback(
                    "step_start",
                    {
                        "id": stage["step_id"],
                        "kind": "thought",
                        "status": "running",
                        "title": stage["step_title"],
                        "detail": stage["step_detail"],
                    },
                )

            vault_matches = await vault_repo.search_similar_chunks(
                stage["vault_query"],
                top_k=3,
                openrouter_key=openrouter_key,
            )
            vault_snippets = [
                f"[{fname} — {chk.heading_title}]\n{chk.content_text[:1100]}"
                for chk, fname, score in vault_matches
                if score > 0.02
            ]

            drafted_batch, batch_meta = await self._author_section_group(
                global_sys=global_sys,
                shared_context=shared_context,
                vault_snippets=vault_snippets,
                sections_spec=stage["sections_spec"],
                include_front_matter_meta=(stage_idx == 0),
                openrouter_key=openrouter_key,
            )
            if batch_meta:
                meta_overrides.update(batch_meta)

            # Attach deterministic tables, standard reference tables, formulas, and Tri-Source figures
            for sec in drafted_batch:
                sid = sec["id"]
                if sid == "sec-1-intro":
                    sec["tables"] = [dict(STANDARD_GEOTECH_CODES_TABLE)] + list(sec.get("tables") or [])
                elif sid == "sec-2-geology":
                    sec["placeholders"] = [
                        {
                            "id": "ph-2-1",
                            "figure_number": "Figure 2.1",
                            "prompt": f"Regional Location & Geological Setting Map — {project.title}",
                            "suggested_category": "map",
                            "resolved_asset_id": map_id,
                            "resolved_url": map_url,
                            "caption": map_cap
                            or f"Figure 2.1: Regional location and geological framework for {project.title}.",
                        }
                    ]
                elif sid == "sec-3-fieldwork":
                    # Deterministic pandas coordinate & uploaded tables come FIRST verbatim
                    det_tables = [dict(t) for t in (coord_tables + other_tables)]
                    for idx_t, dt in enumerate(det_tables, start=1):
                        dt.setdefault("table_number", f"Table 3.{idx_t}")
                    sec["tables"] = det_tables + list(sec.get("tables") or [])
                    sec["placeholders"] = [
                        {
                            "id": "ph-3-1",
                            "figure_number": "Figure 3.1",
                            "prompt": (
                                "Offshore Survey Vessel & Heave-Compensated Drilling Spread"
                                if is_offshore
                                else "Geotechnical Drilling Rig & In-Situ Penetration Testing Spread"
                            ),
                            "suggested_category": "vessel" if is_offshore else "drill_rig",
                            "resolved_asset_id": equip_id,
                            "resolved_url": equip_url,
                            "caption": equip_cap
                            or f"Figure 3.1: Field drilling and in-situ testing spread deployed for {project.title}.",
                        }
                    ]
                elif sid == "sec-4-stratigraphy":
                    det_bh = [dict(t) for t in borehole_tables]
                    for idx_b, db in enumerate(det_bh, start=1):
                        db.setdefault("table_number", f"Table 4.{idx_b}")
                    sec["tables"] = det_bh + list(sec.get("tables") or [])
                elif sid == "sec-5-lab-methods":
                    existing_html = sec.get("html_content", "")
                    missing_eqs = [
                        eq
                        for eq in MANDATORY_LAB_FORMULAS
                        if eq.split("</strong>")[0] not in existing_html
                    ]
                    if missing_eqs and 'class="formula"' not in existing_html:
                        sec["html_content"] = existing_html + "\n" + "\n".join(missing_eqs)
                elif sid == "sec-6-lab-results":
                    sec["placeholders"] = [
                        {
                            "id": f"ph-6-{idx_c}",
                            "figure_number": f"Figure 6.{idx_c}",
                            "prompt": ch["title"],
                            "suggested_category": "lab_equipment",
                            "resolved_asset_id": f"chart-6-{idx_c}",
                            "resolved_url": ch["file_url"],
                            "caption": ch["caption"],
                        }
                        for idx_c, ch in enumerate(scientific_charts[:3], start=1)
                    ]
                elif sid == "sec-7-ground-model" and len(scientific_charts) > 3:
                    ch_ls = scientific_charts[3]
                    sec["placeholders"] = [
                        {
                            "id": "ph-7-1",
                            "figure_number": "Figure 7.1",
                            "prompt": ch_ls["title"],
                            "suggested_category": "map",
                            "resolved_asset_id": "chart-long-section",
                            "resolved_url": ch_ls["file_url"],
                            "caption": ch_ls["caption"],
                        }
                    ]
                elif sid == "sec-8-geohazards" and len(scientific_charts) > 4:
                    ch_hz = scientific_charts[4]
                    sec["placeholders"] = [
                        {
                            "id": "ph-8-1",
                            "figure_number": "Figure 8.1",
                            "prompt": ch_hz["title"],
                            "suggested_category": "map",
                            "resolved_asset_id": "chart-geohazard",
                            "resolved_url": ch_hz["file_url"],
                            "caption": ch_hz["caption"],
                        }
                    ]
                elif sid == "sec-10-appendices":
                    used_urls = {
                        ph.get("resolved_url")
                        for s_prev in all_sections
                        for ph in (s_prev.get("placeholders") or [])
                        if ph.get("resolved_url")
                    }
                    extra_cats = (
                        ("field_photo", "lab_equipment", "drill_rig", "vessel")
                        if is_offshore
                        else ("field_photo", "lab_equipment", "drill_rig")
                    )
                    extra_photos = [
                        a
                        for a in gallery_assets
                        if a.category in extra_cats
                        and a.file_url not in used_urls
                        and "chart" not in a.file_url.lower()
                        and (is_offshore or "offshore" not in (a.default_caption or "").lower())
                    ][:2]
                    sec["placeholders"] = [
                        {
                            "id": f"ph-app-{idx_a}",
                            "figure_number": f"Figure A.{idx_a}",
                            "prompt": f"Representative Field & Laboratory Testing Documentation ({idx_a})",
                            "suggested_category": a.category,
                            "resolved_asset_id": a.id,
                            "resolved_url": a.file_url,
                            "caption": f"Figure A.{idx_a}: Representative geotechnical sampling and laboratory testing apparatus ({project.title}).",
                        }
                        for idx_a, a in enumerate(extra_photos, start=1)
                    ]

            all_sections.extend(drafted_batch)

            elapsed_ms = max(1, int((time.perf_counter() - t_start) * 1000))
            sec_labels = ", ".join(
                f"{s['section_number']} {s['title']}" for s in drafted_batch
            )
            tbl_count = sum(len(s.get("tables") or []) for s in drafted_batch)
            fig_count = sum(len(s.get("placeholders") or []) for s in drafted_batch)
            word_count = sum(
                len(re.sub(r"<[^>]+>", " ", s.get("html_content", "")).split())
                for s in drafted_batch
            )
            if step_callback:
                await step_callback(
                    "step_done",
                    {
                        "id": stage["step_id"],
                        "kind": "thought",
                        "status": "done",
                        "title": stage["step_title"],
                        "duration": elapsed_ms,
                        "output": (
                            f"Drafted **{sec_labels}** · `{word_count:,} words` · "
                            f"`{tbl_count} table(s)` · `{fig_count} figure(s)`."
                        ),
                    },
                )

        return {
            "report_title": project.title,
            "report_subtitle": (
                meta_overrides.get("report_subtitle")
                or project.subtitle
                or existing_ast.get("report_subtitle")
                or "GEOTECHNICAL SITE & LABORATORY INVESTIGATION REPORT"
            ),
            "program_title": (
                meta_overrides.get("program_title")
                or project.client_name
                or project.document_type
                or "GEOTECHNICAL ENGINEERING DELIVERABLE"
            ),
            "location_line": (
                meta_overrides.get("location_line")
                or project.subtitle
                or project.title
            ),
            "campaign_dates": (
                meta_overrides.get("campaign_dates")
                or existing_ast.get("campaign_dates")
                or "2026"
            ),
            "layout_blueprint": layout_blueprint,
            "abbreviations": STANDARD_ABBREVIATIONS,
            "sections": all_sections,
        }

    async def _author_section_group(
        self,
        global_sys: str,
        shared_context: dict[str, Any],
        vault_snippets: list[str],
        sections_spec: list[dict[str, Any]],
        include_front_matter_meta: bool,
        openrouter_key: str,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        schema_hint = (
            '{\n'
            + (
                '  "program_title": "...",\n'
                '  "report_subtitle": "...",\n'
                '  "location_line": "...",\n'
                '  "campaign_dates": "...",\n'
                if include_front_matter_meta
                else ""
            )
            + '  "sections": [\n'
            '    {\n'
            '      "id": "...",\n'
            '      "section_number": "...",\n'
            '      "title": "...",\n'
            '      "html_content": "<h3>...</h3><p>...</p>",\n'
            '      "tables": [\n'
            '        {\n'
            '          "table_number": "Table X.Y",\n'
            '          "title": "...",\n'
            '          "columns": ["Col 1", "Col 2", "Col 3", "Col 4"],\n'
            '          "rows": [["...", "...", "...", "..."]]\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            '}'
        )

        sys_msg = (
            f"{global_sys}\n\n"
            "CRITICAL PROJECT ISOLATION RULE:\n"
            "- Write EXCLUSIVELY for the project described in `context.project` and `context.uploaded_intake_excerpts`.\n"
            "- Use Vault reference excerpts ONLY to match writing voice, structural cadence, and standard methodology phrasing — "
            "NEVER copy unrelated client names, vessel names, river/airstrip names, or coordinates from Vault examples into a different project.\n"
            "- Write exhaustive, publication-grade engineering prose (500–900 words per section using `<h3>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, and `<p class=\"formula\">`).\n"
            "- Populate every requested table in `required_tables` with complete, realistic, domain-accurate rows consistent with the project inputs (labeling any unmeasured design estimate transparently as characteristic/indicative).\n"
            f"- Return ONLY valid JSON matching this schema:\n{schema_hint}"
        )

        user_msg = json.dumps(
            {
                "requested_sections": sections_spec,
                "context": shared_context,
                "vault_style_and_methodology_excerpts": vault_snippets,
            }
        )

        raw = await llm_router.complete_tier1(
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.22,
            api_key_override=openrouter_key,
            max_tokens=8192,
        )

        parsed: dict[str, Any] = {}
        try:
            parsed = _extract_json_dict(raw)
        except Exception:
            # Repair pass if model returned slightly malformed JSON
            repaired_raw = await llm_router.complete_tier1(
                messages=[
                    {
                        "role": "system",
                        "content": f"Convert the following technical draft into strictly valid JSON matching:\n{schema_hint}\nReturn ONLY valid JSON.",
                    },
                    {"role": "user", "content": raw[:14000]},
                ],
                temperature=0.05,
                api_key_override=openrouter_key,
                max_tokens=8192,
            )
            parsed = _extract_json_dict(repaired_raw)

        by_id = {
            str(s.get("id") or ""): s for s in (parsed.get("sections") or []) if isinstance(s, dict)
        }
        ordered_list = [s for s in (parsed.get("sections") or []) if isinstance(s, dict)]

        built: list[dict[str, Any]] = []
        for idx, spec in enumerate(sections_spec):
            matched = by_id.get(spec["id"]) or (
                ordered_list[idx] if idx < len(ordered_list) else {}
            )
            html_content = str(matched.get("html_content") or "").strip()
            if not html_content:
                html_content = f"<p>Technical synthesis for {spec['section_number']} {spec['title']}.</p>"

            tables_out: list[dict[str, Any]] = []
            for t_idx, raw_t in enumerate(matched.get("tables") or [], start=1):
                if not isinstance(raw_t, dict):
                    continue
                cols = [str(c) for c in (raw_t.get("columns") or []) if str(c).strip()]
                rows = [
                    [str(cell) for cell in r]
                    for r in (raw_t.get("rows") or [])
                    if isinstance(r, list) and any(str(x).strip() for x in r)
                ]
                if cols and rows:
                    tables_out.append(
                        {
                            "id": f"tbl-{spec['id']}-{t_idx}",
                            "table_number": str(
                                raw_t.get("table_number")
                                or f"Table {spec['section_number'].rstrip('.')}.{t_idx}"
                            ),
                            "title": str(raw_t.get("title") or "Engineering Summary Table"),
                            "columns": cols,
                            "rows": rows,
                            "footnote": str(raw_t["footnote"]) if raw_t.get("footnote") else None,
                        }
                    )

            built.append(
                {
                    "id": spec["id"],
                    "section_number": spec["section_number"],
                    "title": str(matched.get("title") or spec["title"]),
                    "category": spec["category"],
                    "html_content": html_content,
                    "tables": tables_out,
                    "placeholders": [],
                }
            )

        meta: dict[str, str] = {}
        if include_front_matter_meta:
            for k in ("program_title", "report_subtitle", "location_line", "campaign_dates"):
                val = str(parsed.get(k) or "").strip()
                if val:
                    meta[k] = val

        return built, meta
