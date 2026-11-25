import io
import json
from pathlib import Path
import re
from typing import Any
import docx
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
import pymupdf as fitz
from PIL import Image
from app.agents.llm_router import llm_router
from app.core.exceptions import FileParseError
from app.models.vault import GalleryAsset, VaultChunk
from app.services.storage_service import StorageService


SECTION_CLASSIFIERS: list[tuple[str, tuple[str, ...]]] = [
    ("Abbreviations", ("abbreviation", "acronym", "nomenclature", "glossary", "codes, standards", "relevant codes")),
    ("Executive_Summary", ("executive summary", "summary of results")),
    ("Introduction", ("introduction", "background", "purpose", "project description", "project area", "site description", "geology", "regional geology")),
    ("Scope_of_Work", ("scope of work", "sow", "survey location", "test location")),
    ("Equipment_Specs", ("equipment", "vessel", "rig", "winch", "positioning", "dp-2", "seabed frame")),
    ("Procedures", ("procedure", "method", "drilling", "pcpt", "sampling", "laboratory investigation", "moisture content", "particle size", "atterberg", "triaxial", "consolidation", "oedometer", "chemical test", "sulphate", "chloride", "wison")),
    ("Sequence_of_Events", ("sequence of events", "chronology", "daily", "operations log", "standby")),
    ("Field_Results", ("fieldwork", "field results", "stratigraphy", "soil profile", "coordinate", "borehole", "results of laboratory", "engineering analysis", "ground model", "design parameters", "pipeline route", "geohazard", "discussion", "conclusion", "recommendation")),
    ("Appendices", ("appendix", "attachment", "factual report", "borehole log", "pcpt plot", "field pictures", "cone penetration test logs", "particle size distribution curves")),
]


FORENSIC_STYLE_DEFAULTS: dict[str, Any] = {
    "tone": "Authoritative, direct Nigerian offshore & trenchless geotechnical consultancy prose (GEMS / Enviros / Oshone Geosurveys Limited register)",
    "voice_rules": [
        "Express integer counts with parenthetical numerals and 'number' / 'no.': 'ten (10) number boreholes', 'six (6) number boreholes', 'two (2) number Cone Penetration tests (CPT)', '1 no. downhole CPTu borehole'.",
        "State penetration and elevation intervals with explicit datums: '0.0m - 120.0 mBSF', 'below the river-floor (BRF)', 'below the LLWL (Low-Low Water Level)', 'below existing ground level (BGL)', 'Chainage CH 0+025 to CH 0+621'.",
        "Record field operational events in crisp 24-hour log style: 'Standby on weather between 08:14Hrs to 12:00Hrs', 'Vessel bumped over by 2.0m', 'sand was \"blowing-in\" into the drilling casing within the thalweg zones'.",
        "Report CPT refusal and tip resistance explicitly: 'attained refusal at a depth of 21.03m below the river-floor with a cone tip resistance, qc, value of 14.38MPa'.",
        "Write laboratory test procedures in step-by-step BS 1377:1990 / Eurocode 7 EN 1997-2 / ASTM format with explicit variable definitions (M1, M2, M3, V1, V2, V3, Cu, Cc, LL, PL, PI) and mathematical formulas.",
        "Deliver unambiguous engineering recommendations: 'A downhole annular pressure (PWD) sub with a pre-agreed stop-work limit is mandatory, not optional.'",
    ],
    "preferred_nomenclature": [
        "mBSF",
        "LLWL",
        "BRF",
        "BGL",
        "PCPT / CPTu",
        "Wison-APB",
        "TH-30M Heave Compensated Drill Rig",
        "DP-2 Dolphin Geo Survey",
        "BHA",
        "SMYS",
        "PWD Sub",
        "Frac-Out (Inadvertent Returns)",
        "Delft Cavity Expansion Method",
        "BS 1377: 1990",
        "EN 1997-1 & -2",
        "ASTM F1962-20",
        "ASTM C1580-15",
        "ASTM D1411-99",
    ],
    "date_format": "DD Month YYYY / DD/MM/YYYY",
    "time_format": "24-hour Hrs (e.g., 08:14Hrs to 12:00Hrs)",
    "unit_conventions": {
        "penetration": "mBSF / m below BRF / m below LLWL / m BGL",
        "water_depth": "m LAT / m below LLWL",
        "unit_weight": "kN/m³",
        "shear_strength": "kPa",
        "cone_tip_resistance": "MPa",
        "coordinates_local": "Minna / Nigeria West Belt (Easting mE, Northing mN) & UTM Zone 31N/32N",
        "coordinates_geodetic": "WGS84 Latitude / Longitude",
    },
    "standard_equations": [
        "w = [(M2 - M1) / (M3 - M1)] x 100%",
        "PI = LL - PL",
        "Cu = D60 / D10",
        "Cc = (D30)^2 / (D10 x D60)",
        "Sulphate (mg/kg) = (1000 x d x 0.343 x V1 x 1000) / (V2 x M1)  [ASTM C1580-15]",
        "Chloride (mg/L) = (V3 x N x MM x V1 x 1000) / (V2 x M1)  [ASTM D1411-99]",
        "gamma_dry = gamma_bulk / (1 + w)",
        "Fs_frac = Pf / Pa >= 1.5  [Delft / Luger 1989 / Keulen 2001 Cavity Expansion]",
    ],
    "banned_ai_phrases": [
        "delve into",
        "delve",
        "testament to",
        "tapestry",
        "crucial role",
        "it is worth noting",
        "it is important to note",
        "in conclusion",
        "comprehensive overview",
        "moreover",
        "seamlessly",
        "game-changer",
        "cutting-edge",
        "pivotal",
        "underscore",
        "synergy",
    ],
}


def classify_section(heading: str, content: str) -> str:
    combined = f"{heading} {content[:320]}".lower()
    for section_type, keywords in SECTION_CLASSIFIERS:
        if any(kw in combined for kw in keywords):
            return section_type
    return "Procedures"


def classify_forensic_image(
    caption: str,
    source_context: str = "",
    width: int = 0,
    height: int = 0,
    is_header: bool = False,
) -> tuple[str, str]:
    """
    Returns (forensic_category, ui_gallery_category).
    Forensic categories:
      logo, signature, regional_map, site_satellite_map, vessel_or_rig_photo,
      lab_chart_plasticity, lab_chart_density_moisture, lab_chart_shear_triaxial,
      lab_chart_oedometer, stratigraphic_fence_diagram, hdd_long_section,
      geohazard_chart, cpt_log_plot, field_appendix_photo
    """
    c = f"{caption} {source_context}".lower()
    if is_header or any(k in c for k in ("logo", "brand", "header", "oshone", "hddtec", "hddtel", "first e&p", "gems", "enviros", "fisas")):
        if not any(k in c for k in ("figure", "map", "chart", "borehole", "vessel", "rig")):
            return "logo", "logo"
    if any(k in c for k in ("signature", "authorised by", "approved by", "prepared by")) or (0 < width <= 460 and 0 < height <= 210 and "sign" in c):
        return "signature", "signature"
    if any(k in c for k in ("casagrande", "plasticity chart", "atterberg", "hydrometer")):
        return "lab_chart_plasticity", "lab_equipment"
    if any(k in c for k in ("bulk density", "moisture content", "unit weight with depth")):
        return "lab_chart_density_moisture", "lab_equipment"
    if any(k in c for k in ("direct shear", "friction angle", "triaxial", "shear strength with depth")):
        if "performing triaxial" in c:
            return "field_appendix_photo", "lab_equipment"
        return "lab_chart_shear_triaxial", "lab_equipment"
    if any(k in c for k in ("oedometer", "consolidation", "compression curve", "preconsolidation", "overconsolidation")):
        return "lab_chart_oedometer", "lab_equipment"
    if any(k in c for k in ("fence diagram", "stratigraphic correlation", "schematic profile")):
        return "stratigraphic_fence_diagram", "map"
    if any(k in c for k in ("long-section", "long section", "hdd profile", "bore path", "centreline")):
        return "hdd_long_section", "map"
    if any(k in c for k in ("geohazard exposure", "geohazard")):
        return "geohazard_chart", "map"
    if any(k in c for k in ("cpt", "cone penetration", "pcpt plot")):
        if "verifying cpt" in c:
            return "vessel_or_rig_photo", "drill_rig"
        return "cpt_log_plot", "drill_rig"
    if any(k in c for k in ("google map", "focus area", "satellite", "borehole bh")):
        return "site_satellite_map", "map"
    if any(k in c for k in ("map of", "geological map", "regional geology", "oml 83")):
        return "regional_map", "map"
    if any(k in c for k in ("vessel", "dp-2", "dolphin geo", "rig", "th-30m", "winch", "moonpool", "bha", "doghouse", "drillers", "mud mixing")):
        if "vessel" in c or "dolphin" in c:
            return "vessel_or_rig_photo", "vessel"
        return "vessel_or_rig_photo", "drill_rig"
    if any(k in c for k in ("extrusion", "extruded", "laboratory", "samples")):
        return "field_appendix_photo", "lab_equipment"
    return "field_appendix_photo", "field_photo"


def extract_entity_graph(filename: str, full_text: str) -> dict[str, Any]:
    """Forensically extract Client/Operators, Lead Contractors, Consultants, and Subcontractors."""
    combined = f"{filename}\n{full_text}"
    clients: list[str] = []
    contractors: list[str] = []
    consultants: list[str] = []
    subcontractors: list[str] = []
    personnel: list[str] = []
    equipment_and_vessels: list[str] = []

    client_patterns = [
        ("FIRST Exploration and Petroleum Development Company Limited (FIRST E&P)", r"FIRST\s+Exploration|FIRST\s+E\s*&\s*P"),
        ("Matrix Energy Limited", r"Matrix\s+Energy\s+Limited"),
        ("SNEPCO Nigeria Limited", r"SNEPCO"),
        ("NNPC / FIRST E&P Joint Venture", r"NNPC/FIRST\s+E&P"),
    ]
    contractor_patterns = [
        ("GEMS Global Resources Nigeria Limited (GEMS)", r"GEMS\s+Global\s+Resources"),
        ("HDD Thailand - Enikkom Construction Limited (HDDTEC)", r"HDDTEC|HDD\s*Thailand\s*[-–]\s*Enikkom\s+Construction"),
        ("HDD Thailand - Enikkom Limited (HDDTEL)", r"HDDTEL|HDD\s*Thailand\s*[-–]?\s*Enikkom\s+Limited"),
        ("Enikkom Construction Limited (ECL)", r"Enikkom\s+Construction\s+Limited"),
    ]
    consultant_patterns = [
        ("Oshone Geosurveys Limited (OGL)", r"Oshone\s+Geosurveys\s+Limited"),
        ("Enviros", r"enviros\.com|Enviros"),
    ]
    subcontractor_patterns = [
        ("FISAS", r"\bFISAS\b"),
        ("Sitech Nigeria Limited", r"Sitech\s+Nigeria\s+Limited"),
        ("Eadro Nigeria Limited", r"Eadro\s+Nigeria\s+Limited"),
        ("Bough Resources", r"Bough\s+Resources"),
    ]
    personnel_patterns = [
        "Ike Iheanyi",
        "F.U.Nmiri",
        "S.I.Jegede",
        "O.K.Okon",
        "Tope",
        "Emeka",
        "Chris",
    ]
    equip_patterns = [
        ("DP-2 Dolphin Geo Survey (Geotechnical Survey Vessel)", r"Dolphin\s+Geo\s+Survey"),
        ("TH-30M Heave Compensated Drill Rig & Umbilical Winch", r"TH-30[mM]"),
        ("AP Van Den Berg Wison Wireline Downhole CPTu System (50/100 kN)", r"Wison|AP\s+[vV]an\s+Den\s+Berg"),
        ("Over-Water Drilling Barge with Moon-Pool", r"drilling\s+barge"),
        ("Seabed Frame with Re-Entry Guide, Clamp & Shear Ram", r"seabed\s+frame"),
    ]

    for label, pat in client_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            clients.append(label)
    for label, pat in contractor_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            contractors.append(label)
    for label, pat in consultant_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            consultants.append(label)
    for label, pat in subcontractor_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            subcontractors.append(label)
    for person in personnel_patterns:
        if person.lower() in combined.lower():
            personnel.append(person)
    for label, pat in equip_patterns:
        if re.search(pat, combined, re.IGNORECASE):
            equipment_and_vessels.append(label)

    # Extract document reference code if present
    doc_refs = re.findall(
        r"\b(?:\d{4}\s*[-–]\s*\d{3}\s*[-–]\s*[A-Z]{2,6}\s*[-–]\s*[A-Z]{2,8}\s*[-–]\s*[A-Z]{2,6}\s*[-–]\s*\d{3}|8385-[A-Z0-9-]+|GEMS-[A-Z0-9-]+)\b",
        combined,
    )

    return {
        "client_operators": clients,
        "lead_contractors": contractors,
        "geotechnical_consultants": consultants,
        "field_and_lab_subcontractors": subcontractors,
        "key_personnel": personnel,
        "equipment_and_vessels": equipment_and_vessels,
        "document_reference_codes": list(dict.fromkeys(doc_refs))[:6],
    }


def extract_formulas_from_text(full_text: str) -> list[dict[str, str]]:
    """Extract mathematical formulas and laboratory equations from the report text."""
    formulas: list[dict[str, str]] = []
    known = [
        (
            "Moisture Content (BS 1377: Part 2)",
            r"w\s*=\s*\[\(M2\s*-\s*M1\)",
            "w = [(M2 - M1) / (M3 - M1)] × 100%",
            "$ w = ((M_2 - M_1) / (M_3 - M_1)) times 100% $",
        ),
        (
            "Plasticity Index (BS 1377 / ASTM D4318)",
            r"PI\s*=\s*LL\s*-\s*PL",
            "PI = LL - PL",
            "$ \"PI\" = \"LL\" - \"PL\" $",
        ),
        (
            "Coefficients of Uniformity & Curvature (PSD)",
            r"Cu\s*=\s*D60\s*/\s*D10",
            "Cu = D60 / D10 ;  Cc = (D30)² / (D10 × D60)",
            "$ C_u = D_60 / D_10, quad C_c = (D_30)^2 / (D_10 times D_60) $",
        ),
        (
            "Sulphate Content (ASTM C1580-15)",
            r"Sulphate\s*\(mg/kg\)\s*=",
            "Sulphate (mg/kg) = (1000 × d × 0.343 × V1 × 1000) / (V2 × M1)",
            "$ \"Sulphate (mg/kg)\" = (1000 times d times 0.343 times V_1 times 1000) / (V_2 times M_1) $",
        ),
        (
            "Chloride Content (ASTM D1411-99)",
            r"Chloride\s*\(mg/L\)\s*=",
            "Chloride (mg/L) = (V3 × N × MM × V1 × 1000) / (V2 × M1)",
            "$ \"Chloride (mg/L)\" = (V_3 times N times \"MM\" times V_1 times 1000) / (V_2 times M_1) $",
        ),
        (
            "Bulk & Dry Unit Weight",
            r"bulk\s+unit\s+weight\s+of\s+the\s+soil\s+is\s+obtained",
            "γ_bulk = ρ × g ;  γ_dry = γ_bulk / (1 + w)",
            "$ gamma_\"bulk\" = rho times g, quad gamma_\"dry\" = gamma_\"bulk\" / (1 + w) $",
        ),
        (
            "Delft Cavity Expansion Hydraulic Fracture Criterion",
            r"Delft|frac-out\s+limit|Pf,\(non-cohesive\)",
            "Fs = P_f / P_a ≥ 1.5 (Delft / Luger 1989 / Keulen 2001)",
            "$ F_s = P_f / P_a >= 1.5 $",
        ),
    ]
    for name, pattern, plain, typst_math in known:
        if re.search(pattern, full_text, re.IGNORECASE):
            formulas.append(
                {
                    "name": name,
                    "formula_plain": plain,
                    "formula_typst": typst_math,
                }
            )
    return formulas


def build_layout_blueprint(
    filename: str,
    full_text: str,
    headings: list[str],
    table_schemas: list[dict[str, Any]],
    figure_count: int,
    page_count: int,
) -> dict[str, Any]:
    """Synthesize a deep Forensic Report Blueprint from the uploaded report structure."""
    text_lower = full_text.lower()
    is_hdd = "hdd" in text_lower or "horizontal directional drilling" in text_lower or "bore path" in text_lower
    splits_interpretative_factual = (
        "interpretative report" in text_lower and "factual report" in text_lower
    )
    archetype = (
        "HDD_GEOTECHNICAL_LAB_INTERPRETATIVE_FACTUAL_REPORT"
        if is_hdd
        else "OFFSHORE_MARINE_GEOTECHNICAL_FIELD_REPORT"
    )

    front_matter = []
    if "authorisation" in text_lower or "authorization" in text_lower:
        front_matter.append("Document Authorisation & Distribution Matrix")
    if "signature" in text_lower:
        front_matter.append("5-Column Approval Signature Table")
    if "rev" in text_lower and ("issued by" in text_lower or "checked" in text_lower):
        front_matter.append("6-Column Revision Control Matrix (Rev, Date, Description, Issued/Prepared, Checked, Approved)")
    if "table of contents" in text_lower or "content" in text_lower or headings:
        front_matter.append("Clickable Table of Contents (Dot Leaders)")
    if "list of figures" in text_lower or figure_count > 0:
        front_matter.append("List of Figures & List of Tables")
    if "abbreviations" in text_lower or "glossary" in text_lower:
        front_matter.append("Abbreviations, Acronyms & Glossary of Terms + Referenced Standards Tables")
    if splits_interpretative_factual:
        front_matter.append("Dual-Part Structure: INTERPRETATIVE REPORT (Sections 1.0–8.0/10.0) + FACTUAL REPORT Appendices")

    entities = extract_entity_graph(filename, full_text)
    formulas = extract_formulas_from_text(full_text)

    return {
        "source_document": filename,
        "report_archetype": archetype,
        "splits_interpretative_factual": splits_interpretative_factual,
        "page_size": "A4 Portrait (210mm x 297mm) with Auto-Landscape Rotation for 10+ Column Coordinate Sheets",
        "running_header": "Corporate multi-logo header table (Client/Contractor logo left · Consultant/Partner logo right) + Document Ref",
        "cover_structure": (
            [
                "Top dual/triple corporate logo band (HDDTEC / HDDTEL / Matrix / SNEPCO + Oshone Geosurveys Limited)",
                "Document Reference Code banner (e.g., 2026 – 004 – OGL – ECL – PR - 001)",
                "Centered Project Title, Crossing Length/Diameter & GEOTECHNICAL LABORATORY INVESTIGATIONS FINAL REPORT",
                "6-Column Revision Control Matrix (Rev, Date, Description, Issued by, Checked by, Approved by)",
                "Dedicated Executive Summary & Interpretative Report Title Divider",
            ]
            if is_hdd
            else [
                "Top dual/triple corporate logo header band (FIRST E&P left · GEMS & Enviros right)",
                "Centered Program Title, Survey Type & Location Subtitle (OML 83 & 85)",
                "Revision line & Dual Document Ref codes (Client Ref + Contractor Ref)",
                "Proprietary confidentiality & copyright block",
                "Bottom 6-column Revision Control matrix + Page 2 Document Authorisation & Signature Matrix",
            ]
        ),
        "front_matter_sections": front_matter,
        "heading_hierarchy": (
            [
                "EXECUTIVE SUMMARY",
                "1.0 INTRODUCTION (1.1 Purpose, 1.2 Scope of Work, 1.3 Abbreviations, 1.4 Codes & Texts, 1.5 HDD Relevant Standards)",
                "2.0 SITE DESCRIPTION AND GEOLOGY (2.1 Site Description, 2.2 Site Geology, 2.3 Regional Geology of the Niger Delta)",
                "3.0 FIELDWORK (3.1 Ground & Surface Water Conditions, 3.2 Coordinates of Drilled Positions, 3.3 CPT Positions & Refusal)",
                "4.0 SITE SOIL STRATIGRAPHY (Table 4.1 Sequence of the Strata & Borehole Correlation)",
                "5.0 LABORATORY INVESTIGATION (5.1 Moisture Content, 5.2 PSD, 5.3/5.4 Atterberg Limits, 5.5 UU Triaxial, 5.6 Oedometer, 5.7 Unit Weight, 5.8 Chemical Tests: pH, Sulphate, Chloride)",
                "6.0 RESULTS OF LABORATORY INVESTIGATION & ENGINEERING ANALYSIS (CLAY & SAND Parameter Tables, Casagrande, Density/Moisture, Shear, Oedometer Charts)",
                "7.0 GROUND MODEL / PIPELINE ROUTE – INPUTS AND DESIGN (Pipe, Drilling & Mud, Geometric, Geotechnical Design Inputs & Long-Section)",
                "8.0 / 9.0 GEOHAZARD EVALUATION (9.1 Frac-Out, 9.2 Borehole Instability, 9.3 Fluid Loss, 9.4 Organic Horizons, 9.5 Reactive Clays, 9.6 Cuttings Transport, 9.7 Settlement, 9.8 Obstructions, 9.9 Saline Pore Water)",
                "10.0 DISCUSSION, RECOMMENDATIONS AND CONCLUSION + FACTUAL REPORT APPENDICES",
            ]
            if is_hdd
            else [
                "ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS",
                "1. EXECUTIVE SUMMARY (Table 1: Summary of Results)",
                "2. INTRODUCTION (2.1 Project Description, 2.2 Project Area & OML Maps)",
                "3. SCOPE OF WORK (3.1 Location SOW, Sampling Regime & Specified Offshore Laboratory Tests)",
                "4. FIELD ACTIVITIES - GEOTECHNICAL INVESTIGATION (4.1 Survey Vessel & Equipment, 4.2 Drilling, Sampling, PCPT & Offshore Lab Procedures, 4.3 Chronological Sequence of Events)",
                "5. FIELD RESULTS (5.1 15-Column Target vs Actual Coordinates, 5.2 Borehole Log & Soil Profile, 5.3 CPT Logs, 5.4 Summary of Offshore Lab Results)",
                "APPENDICES (Appendix A: Field Pictures & Merged External Attachments)",
            ]
        ),
        "toc_style": "Typst native clickable outline (#outline) with automatic dot leaders and page numbering",
        "table_style": "0.6pt solid charcoal engineering borders (#1D1D1F), #F5F5F7 shaded repeating headers, tabular-nums",
        "figure_style": "Grouped Typst figures (#figure) with high-DPI images/charts and bold centered captions",
        "detected_headings": headings[:32],
        "table_schemas": table_schemas[:20],
        "extracted_formulas": formulas,
        "entities_json": entities,
        "metrics": {
            "table_count": len(table_schemas),
            "figure_count": figure_count,
            "formula_count": len(formulas),
            "page_count": page_count,
        },
    }


class VaultIngestorService:
    """
    Deep Multi-Pass Forensic Ingestion Pipeline for historical .docx/.pdf/.txt geotechnical reports:
      1) Report Archetype & Section Blueprint (report_blueprint_json / pdf_layout_blueprint_json)
      2) Corporate & Entity Graph (entities_json)
      3) Embedded Visuals, Logos, Maps, Engineering Plots & Signatures (GalleryAsset)
      4) Author Style Fingerprint & Domain Lexicon (style_guide_json)
    """

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()

    def ingest_bytes(
        self, vault_document_id: str, filename: str, content: bytes
    ) -> tuple[list[VaultChunk], list[GalleryAsset], list[dict[str, Any]]]:
        chunks, assets, meta, _blueprint = self.ingest_with_blueprint(
            vault_document_id, filename, content
        )
        return chunks, assets, meta

    def ingest_with_blueprint(
        self, vault_document_id: str, filename: str, content: bytes
    ) -> tuple[list[VaultChunk], list[GalleryAsset], list[dict[str, Any]], dict[str, Any]]:
        ext = Path(filename).suffix.lower()
        blocks: list[tuple[str, str, list]] = []
        assets: list[GalleryAsset] = []
        extracted_meta: list[dict[str, Any]] = []
        blueprint: dict[str, Any] = {}

        if ext == ".docx":
            blocks, assets, extracted_meta, blueprint = self._extract_docx_all(filename, content)
        elif ext == ".pdf":
            blocks, assets, extracted_meta, blueprint = self._extract_pdf_all(filename, content)
        elif ext in (".txt", ".md"):
            txt = content.decode("utf-8", errors="replace")
            blocks = self._extract_text_blocks(txt)
            headings = [h for h, _t, _tbl in blocks]
            blueprint = build_layout_blueprint(filename, txt, headings, [], 0, 1)
        else:
            raise FileParseError(
                f"Vault ingestion supports .docx, .pdf, and .txt files (got '{ext}')."
            )

        chunks: list[VaultChunk] = []
        for heading, text, tables in blocks:
            if not text.strip() and not tables:
                continue
            chunks.append(
                VaultChunk(
                    vault_document_id=vault_document_id,
                    section_type=classify_section(heading, text),
                    heading_title=heading[:250],
                    content_text=text.strip(),
                    tables_json=tables,
                )
            )

        if not chunks:
            raise FileParseError(
                f"No readable geotechnical sections or tables could be extracted from '{filename}'."
            )
        return chunks, assets, extracted_meta, blueprint

    async def extract_style_fingerprint(
        self,
        filename: str,
        chunks: list[VaultChunk],
        openrouter_key: str = "",
    ) -> dict[str, Any]:
        """
        Extracts the Author Style Fingerprint & Domain Lexicon combining deterministic forensic
        patterns from the document with Tier-1 AI analysis.
        """
        full_text = "\n".join(c.content_text for c in chunks)
        formulas = [f["formula_plain"] for f in extract_formulas_from_text(full_text)]
        base_style = dict(FORENSIC_STYLE_DEFAULTS)
        if formulas:
            base_style["standard_equations"] = list(
                dict.fromkeys(base_style["standard_equations"] + formulas)
            )

        sample_excerpts = "\n\n".join(
            f"### {c.heading_title}\n{c.content_text[:900]}" for c in chunks[:8]
        )
        sys_prompt = (
            "You are a Geotechnical Style Fingerprint & Forensic Lexicon Extractor. Analyze the historical "
            "engineering report excerpts below and extract the author's exact writing voice, units, numeric count phrasing "
            "(e.g. 'ten (10) number boreholes'), depth/datum conventions (mBSF, LLWL, BRF, BGL), field operational phrasing, "
            "and formatting conventions. Return ONLY valid JSON matching:\n"
            '{"tone":"...","voice_rules":["..."],"preferred_nomenclature":["..."],'
            '"date_format":"...","time_format":"...",'
            '"unit_conventions":{"penetration":"...","water_depth":"...","coordinates_local":"..."},'
            '"banned_ai_phrases":["delve into","testament to","crucial role","moreover","seamlessly","tapestry"]}'
        )
        try:
            raw = await llm_router.complete_tier1(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Report: {filename}\n\n{sample_excerpts}"},
                ],
                temperature=0.1,
                api_key_override=openrouter_key,
                max_tokens=1400,
            )
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.strip("`").strip()
                if clean.lower().startswith("json"):
                    clean = clean[4:].strip()
            parsed = json.loads(clean)
            return {
                "tone": str(parsed.get("tone") or base_style["tone"]),
                "voice_rules": list(
                    dict.fromkeys(base_style["voice_rules"] + list(parsed.get("voice_rules") or []))
                ),
                "preferred_nomenclature": list(
                    dict.fromkeys(
                        base_style["preferred_nomenclature"]
                        + list(parsed.get("preferred_nomenclature") or [])
                    )
                ),
                "date_format": str(parsed.get("date_format") or base_style["date_format"]),
                "time_format": str(parsed.get("time_format") or base_style["time_format"]),
                "unit_conventions": {
                    **base_style["unit_conventions"],
                    **dict(parsed.get("unit_conventions") or {}),
                },
                "standard_equations": base_style["standard_equations"],
                "banned_ai_phrases": list(
                    dict.fromkeys(
                        base_style["banned_ai_phrases"]
                        + list(parsed.get("banned_ai_phrases") or [])
                    )
                ),
            }
        except Exception:
            return base_style

    def _save_valid_raster_image(
        self,
        stem: str,
        target_ref: str,
        img_bytes: bytes,
        caption: str,
        source_context: str = "",
        is_header: bool = False,
    ) -> tuple[GalleryAsset | None, dict[str, Any] | None]:
        """Validate image is a web/Typst-compatible raster (.png/.jpg/.jpeg/.webp), classify it, and persist."""
        if len(img_bytes) < 1_000:
            return None, None
        ext = Path(target_ref).suffix.lower()
        if ext in (".emf", ".wmf"):
            return None, None
        try:
            with Image.open(io.BytesIO(img_bytes)) as im:
                width, height = im.size
                fmt = (im.format or "PNG").lower()
                if width < 40 or height < 30:
                    return None, None
                if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                    ext = f".{fmt}" if fmt in ("png", "jpeg", "webp") else ".png"
        except Exception:
            return None, None

        clean_title = re.sub(r"\s+", " ", caption).strip() or f"{stem} Extracted Visual"
        forensic_cat, ui_cat = classify_forensic_image(
            clean_title,
            source_context=source_context,
            width=width,
            height=height,
            is_header=is_header,
        )
        bucket = "branding-assets" if forensic_cat in ("logo", "signature") else "equipment-gallery"
        safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", stem)[:48]
        img_url, _ = self.storage.save_bytes(
            bucket,
            f"{safe_stem}_{Path(target_ref).stem}{ext}",
            img_bytes,
        )
        asset = GalleryAsset(
            title=clean_title[:240],
            default_caption=clean_title,
            category=ui_cat if ui_cat in ("vessel", "drill_rig", "lab_equipment", "map", "field_photo") else "map",
            file_url=img_url,
            tags=[stem, forensic_cat, ui_cat],
        )
        meta = {
            "title": clean_title[:240],
            "caption": clean_title,
            "category": forensic_cat,
            "ui_category": ui_cat,
            "dimensions": f"{width}x{height}",
            "file_url": img_url,
        }
        return asset, meta

    def _extract_docx_all(
        self, filename: str, content: bytes
    ) -> tuple[list[tuple[str, str, list]], list[GalleryAsset], list[dict[str, Any]], dict[str, Any]]:
        try:
            doc = docx.Document(io.BytesIO(content))
        except Exception as exc:
            raise FileParseError("Could not parse uploaded .docx file.") from exc

        stem = Path(filename).stem
        seen_targets: set[str] = set()
        assets: list[GalleryAsset] = []
        extracted_meta: list[dict[str, Any]] = []

        # 1. Extract Corporate Logos from Section Headers
        for s_idx, sec in enumerate(doc.sections):
            try:
                hdr_xml = sec.header._element.xml
                hdr_rids = re.findall(r'r:(?:embed|id)="(rId\d+)"', hdr_xml)
                hdr_text = " ".join(p.text.strip() for p in sec.header.paragraphs if p.text.strip())
                for l_idx, rid in enumerate(hdr_rids, start=1):
                    rel = sec.header.part.rels.get(rid)
                    if not rel or "image" not in rel.target_ref:
                        continue
                    target_key = f"hdr_{rel.target_ref}"
                    if target_key in seen_targets:
                        continue
                    seen_targets.add(target_key)
                    seen_targets.add(rel.target_ref)
                    logo_label = self._infer_logo_name(filename, rel.target_ref, l_idx, hdr_text)
                    asset, meta = self._save_valid_raster_image(
                        stem=stem,
                        target_ref=rel.target_ref,
                        img_bytes=rel.target_part.blob,
                        caption=logo_label,
                        source_context="Corporate Header Logo",
                        is_header=True,
                    )
                    if asset and meta:
                        assets.append(asset)
                        extracted_meta.append(meta)
            except Exception:
                continue

        # 2. Extract Cover Logos & Digital Signatures from Document Tables
        doc_rels = doc.part.rels
        for t_idx, tbl in enumerate(doc.tables):
            t_xml = tbl._element.xml
            t_rids = re.findall(r'r:(?:embed|id)="(rId\d+)"', t_xml)
            t_text = " ".join(
                c.text.strip() for row in tbl.rows[:5] for c in row.cells if c.text.strip()
            )[:300]
            for r_i, rid in enumerate(t_rids, start=1):
                rel = doc_rels.get(rid)
                if not rel or "image" not in rel.target_ref:
                    continue
                target_key = rel.target_ref
                if target_key in seen_targets:
                    continue
                seen_targets.add(target_key)
                is_sig = "signature" in t_text.lower() or "prepared by" in t_text.lower()
                caption = (
                    f"Authorised Signatory Digital Signature ({stem})"
                    if is_sig
                    else self._infer_logo_name(filename, target_key, r_i, t_text)
                )
                asset, meta = self._save_valid_raster_image(
                    stem=stem,
                    target_ref=target_key,
                    img_bytes=rel.target_part.blob,
                    caption=caption,
                    source_context="Signature Table" if is_sig else "Cover Page Logo",
                    is_header=not is_sig,
                )
                if asset and meta:
                    assets.append(asset)
                    extracted_meta.append(meta)

        # 3. Extract Paragraphs, Inline Images (both r:embed and r:id) & Tables in Exact Document Order
        paras = doc.paragraphs
        for pidx, p in enumerate(paras):
            xml = p._p.xml
            embeds = re.findall(r'r:(?:embed|id)="(rId\d+)"', xml)
            if not embeds:
                continue
            caption = ""
            # Search nearby paragraphs for an explicit Figure caption first
            for look_idx in (pidx + 1, pidx + 2, pidx - 1, pidx + 3, pidx - 2):
                if 0 <= look_idx < len(paras):
                    cand = paras[look_idx].text.strip()
                    if re.match(r"^(?:Figure|Fig\.?)\s+\d+", cand, re.IGNORECASE):
                        caption = cand
                        break
            if not caption:
                for look_idx in (pidx + 1, pidx - 1, pidx + 2):
                    if 0 <= look_idx < len(paras):
                        cand = paras[look_idx].text.strip()
                        if cand and 4 < len(cand) < 160 and not cand.startswith("Table"):
                            caption = cand
                            break
            if not caption:
                caption = f"Extracted Figure ({stem})"

            for rid in embeds:
                rel = doc_rels.get(rid)
                if not rel or "image" not in rel.target_ref:
                    continue
                target_key = rel.target_ref
                if target_key in seen_targets:
                    continue
                seen_targets.add(target_key)
                is_cover_logo = pidx < 35 and not caption.lower().startswith("figure")
                final_cap = (
                    self._infer_logo_name(filename, target_key, pidx, caption)
                    if is_cover_logo
                    else caption
                )
                asset, meta = self._save_valid_raster_image(
                    stem=stem,
                    target_ref=target_key,
                    img_bytes=rel.target_part.blob,
                    caption=final_cap,
                    source_context=caption,
                    is_header=is_cover_logo,
                )
                if asset and meta:
                    assets.append(asset)
                    extracted_meta.append(meta)

        # Iterate body children in order to associate paragraphs AND tables with their section headings
        blocks: list[tuple[str, str, list]] = []
        current_heading = "1.0 GENERAL TECHNICAL OVERVIEW & FRONT MATTER"
        current_lines: list[str] = []
        current_tables: list[dict[str, Any]] = []
        headings: list[str] = []
        all_table_schemas: list[dict[str, Any]] = []
        last_table_caption = ""
        table_counter = 0

        for child in doc.element.body.iterchildren():
            if isinstance(child, CT_P):
                p = Paragraph(child, doc)
                text = p.text.strip()
                if not text:
                    continue
                style_name = (p.style.name or "").lower() if p.style else ""
                if "toc" in style_name or "table of figures" in style_name:
                    continue
                if re.match(r"^Table\s+\d+(?:\.\d+)?[:\s—-]", text, re.IGNORECASE) and len(text) < 150:
                    last_table_caption = text

                is_heading = (
                    "heading" in style_name
                    or bool(re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z]", text) and len(text) < 110)
                    or (
                        text.isupper()
                        and 4 <= len(text) <= 85
                        and any(
                            k in text
                            for k in (
                                "EXECUTIVE SUMMARY",
                                "INTRODUCTION",
                                "SCOPE OF WORK",
                                "FIELD ACTIVITIES",
                                "FIELDWORK",
                                "FIELD RESULTS",
                                "STRATIGRAPHY",
                                "LABORATORY",
                                "ENGINEERING ANALYSIS",
                                "GROUND MODEL",
                                "DESIGN PARAMETERS",
                                "PIPELINE ROUTE",
                                "GEOHAZARD",
                                "DISCUSSION",
                                "RECOMMENDATIONS",
                                "CONCLUSION",
                                "ABBREVIATIONS",
                                "APPENDICES",
                            )
                        )
                    )
                )
                if is_heading:
                    headings.append(text)
                    if current_lines or current_tables:
                        blocks.append((current_heading, "\n".join(current_lines), current_tables))
                    current_heading = text
                    current_lines = []
                    current_tables = []
                else:
                    current_lines.append(text)

            elif isinstance(child, CT_Tbl):
                tbl = Table(child, doc)
                table_counter += 1
                parsed_tbl = self._parse_docx_table(tbl, table_counter, last_table_caption or current_heading)
                last_table_caption = ""
                if parsed_tbl:
                    current_tables.append(parsed_tbl)
                    all_table_schemas.append(
                        {
                            "table_number": parsed_tbl["table_number"],
                            "title": parsed_tbl["title"],
                            "columns": parsed_tbl["columns"],
                            "row_count": parsed_tbl["row_count"],
                            "section": current_heading,
                        }
                    )

        if current_lines or current_tables:
            blocks.append((current_heading, "\n".join(current_lines), current_tables))

        table_text = "\n".join(
            c.text.strip()
            for t in doc.tables
            for r in t.rows
            for c in r.cells
            if c.text.strip()
        )
        full_text = "\n".join(p.text for p in paras if p.text.strip()) + "\n" + table_text
        blueprint = build_layout_blueprint(
            filename,
            full_text,
            headings,
            table_schemas=all_table_schemas,
            figure_count=len(assets),
            page_count=max(len(blocks) + 6, 12),
        )
        return blocks, assets, extracted_meta, blueprint

    def _infer_logo_name(self, filename: str, target_ref: str, idx: int, context_text: str) -> str:
        fn_lower = filename.lower()
        t_name = Path(target_ref).name.lower()
        if "anyala" in fn_lower:
            if "image1." in t_name:
                return "FIRST E&P Corporate Logo (Client / Operator)"
            if "image2." in t_name or "image5." in t_name:
                return "GEMS Global Resources Nigeria Limited Corporate Logo (Lead Survey Contractor)"
            if "image3." in t_name:
                return "Enviros Corporate Logo (Geotechnical Partner)"
        elif "escravos" in fn_lower:
            if "image1." in t_name:
                return "HDDTEC / Matrix Energy / FISAS Project Header Logo"
            if "image2." in t_name:
                return "Oshone Geosurveys Limited (OGL) Corporate Logo (Geotechnical Consultant)"
        elif "finima" in fn_lower:
            if "image1." in t_name or "image10." in t_name:
                return "HDD Thailand - Enikkom Limited (HDDTEL) Corporate Logo (Lead HDD Contractor)"
            if "image2." in t_name:
                return "Oshone Geosurveys Limited (OGL) Corporate Logo (Geotechnical Consultant)"
        return f"Corporate Logo #{idx} ({Path(filename).stem})"

    def _parse_docx_table(
        self, tbl: Table, table_idx: int, caption_or_heading: str
    ) -> dict[str, Any] | None:
        raw_rows: list[list[str]] = []
        for row in tbl.rows:
            cells = [re.sub(r"\s+", " ", c.text.strip()) for c in row.cells]
            if not any(cells):
                continue
            raw_rows.append(cells)

        if len(raw_rows) < 2:
            return None

        # Deduplicate horizontally merged header cells if needed while keeping column structure
        columns = raw_rows[0]
        data_rows = raw_rows[1:]
        m_num = re.match(r"^(Table\s+\d+(?:\.\d+)?)\s*[:—-]?\s*(.*)$", caption_or_heading, re.IGNORECASE)
        if m_num:
            tbl_num = m_num.group(1)
            tbl_title = m_num.group(2).strip() or f"Engineering Table {table_idx}"
        else:
            tbl_num = f"Table {table_idx}"
            tbl_title = caption_or_heading[:120]

        return {
            "id": f"vtbl-{table_idx}",
            "table_number": tbl_num,
            "title": tbl_title,
            "columns": columns,
            "rows": data_rows,
            "row_count": len(data_rows),
        }

    def _extract_pdf_all(
        self, filename: str, content: bytes
    ) -> tuple[list[tuple[str, str, list]], list[GalleryAsset], list[dict[str, Any]], dict[str, Any]]:
        try:
            pdf = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise FileParseError("Could not parse uploaded .pdf file.") from exc

        stem = Path(filename).stem
        full_text = "\n".join(page.get_text("text") for page in pdf)
        blocks = self._extract_text_blocks(full_text)
        headings = [h for h, _t, _tbl in blocks]
        assets: list[GalleryAsset] = []
        extracted_meta: list[dict[str, Any]] = []
        seen_xrefs: set[int] = set()

        for page_num, page in enumerate(pdf, start=1):
            page_text = page.get_text("text")
            fig_matches = re.findall(r"(Figure\s+\d+(?:\.\d+)?[:.\s—-][^\n]{4,120})", page_text)
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    extracted = pdf.extract_image(xref)
                    img_bytes = extracted.get("image", b"")
                    ext = extracted.get("ext", "png")
                    caption = (
                        fig_matches.pop(0).strip()
                        if fig_matches
                        else f"{stem} — Page {page_num} Figure"
                    )
                    asset, meta = self._save_valid_raster_image(
                        stem=stem,
                        target_ref=f"p{page_num}_{xref}.{ext}",
                        img_bytes=img_bytes,
                        caption=caption,
                        source_context=page_text[:300],
                    )
                    if asset and meta:
                        assets.append(asset)
                        extracted_meta.append(meta)
                except Exception:
                    continue

        blueprint = build_layout_blueprint(
            filename,
            full_text,
            headings,
            table_schemas=[],
            figure_count=len(assets),
            page_count=len(pdf),
        )
        return blocks, assets, extracted_meta, blueprint

    def _extract_text_blocks(self, full_text: str) -> list[tuple[str, str, list]]:
        lines = full_text.splitlines()
        blocks: list[tuple[str, str, list]] = []
        current_heading = "1.0 DOCUMENT EXTRACT"
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^(#{1,3}\s+|\d+(?:\.\d+)*\.?\s+[A-Z])", stripped) and len(stripped) < 120:
                if current_lines:
                    blocks.append((current_heading, "\n".join(current_lines), []))
                current_heading = stripped.lstrip("# ").strip()
                current_lines = []
            else:
                current_lines.append(stripped)

        if current_lines:
            blocks.append((current_heading, "\n".join(current_lines), []))
        return blocks
