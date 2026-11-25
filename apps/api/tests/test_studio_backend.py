import io
import json
import os
from pathlib import Path
import tempfile

_TEST_DB = Path(tempfile.gettempdir()) / "geotech_studio_pytest.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"

from fastapi.testclient import TestClient  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402
import pymupdf as fitz  # noqa: E402

from app.agents.llm_router import llm_router  # noqa: E402
from app.agents.qa_humanizer_agent import QaHumanizerAgent  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.intake_parser import IntakeParserService  # noqa: E402
from app.services.storage_service import StorageService  # noqa: E402
from app.services.vault_ingestor import VaultIngestorService  # noqa: E402


def test_intake_parser_preserves_exact_decimals():
    csv_bytes = (
        "Location,Minna Easting,Minna Northing,Water Depth (m LAT)\n"
        "BH-01,389949.9720,-9190.0210,49.4\n"
    ).encode("utf-8")
    parser = IntakeParserService()
    parsed = parser.parse_file("coords.csv", csv_bytes)
    assert parsed["kind"] == "coordinate_table"
    row = parsed["tables"][0]["rows"][0]
    assert row[1] == "389949.9720"
    assert row[2] == "-9190.0210"
    assert row[3] == "49.4"


def test_qa_humanizer_strips_banned_phrases():
    qa = QaHumanizerAgent()
    raw = "<p>Moreover, we delve into the soil profile as a testament to our crucial role.</p>"
    cleaned, count = qa.humanize_html(raw, {"banned_ai_phrases": []})
    assert count >= 3
    assert "delve into" not in cleaned.lower()
    assert "testament to" not in cleaned.lower()
    assert "crucial role" not in cleaned.lower()


def test_clean_slate_boot_and_project_export_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", tmp_path)
    with TestClient(app) as client:
        r_health = client.get("/api/v1/health")
        assert r_health.status_code == 200
        assert r_health.json()["success"] is True

        assert client.get("/api/v1/projects").json()["data"] == []
        assert client.get("/api/v1/vault/documents").json()["data"] == []
        assert client.get("/api/v1/vault/gallery").json()["data"] == []
        assert client.get("/api/v1/research/threads").json()["data"] == []

        r_settings = client.get("/api/v1/settings")
        assert r_settings.status_code == 200
        ws = r_settings.json()["data"]
        assert ws["default_contractor_name"] == ""
        assert ws["author_name"] == ""
        assert ws["author_email"] == ""
        assert ws["author_designation"] == ""

        r_create = client.post(
            "/api/v1/projects",
            json={
                "title": "Verification Offshore Field Report",
                "subtitle": "Block Test Survey",
                "client_name": "Operator Ltd",
                "contractor_name": "Survey Contractor Ltd",
                "revision_number": "01",
            },
        )
        assert r_create.status_code == 200
        proj = r_create.json()["data"]
        assert proj["compiled_pdf_url"]
        assert proj["compiled_docx_url"]

        r_pdf = client.get(proj["compiled_pdf_url"].split("?")[0])
        assert r_pdf.status_code == 200
        assert r_pdf.content[:4] == b"%PDF"

        r_docx = client.post(
            f"/api/v1/projects/{proj['id']}/export", json={"format": "docx"}
        )
        assert r_docx.status_code == 200
        assert r_docx.json()["data"]["format"] == "docx"

        r_del = client.delete(f"/api/v1/projects/{proj['id']}")
        assert r_del.status_code == 200


def test_upload_vault_document_persists_chunks_blueprint_and_style(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", tmp_path)

    async def fake_complete(*args, **kwargs):
        return json.dumps(
            {
                "tone": "Objective geotechnical field register",
                "voice_rules": ["Use 24-hour Hrs format."],
                "preferred_nomenclature": ["mBSF", "PCPT"],
                "date_format": "DD/MM/YYYY",
                "time_format": "24-hour Hrs",
                "unit_conventions": {"penetration": "mBSF"},
                "banned_ai_phrases": ["delve into"],
            }
        )

    async def fake_embed(texts, *args, **kwargs):
        return [[0.01] * 1536 for _ in texts]

    monkeypatch.setattr(llm_router, "complete", fake_complete)
    monkeypatch.setattr(llm_router, "embed", fake_embed)

    sample_txt = (
        b"1. EXECUTIVE SUMMARY\n"
        b"Downhole PCPT testing reached 120.0 mBSF.\n\n"
        b"2. FIELD PROCEDURES\n"
        b"Continuous 24-hour operations were maintained from 06:00Hrs.\n"
    )
    with TestClient(app) as client:
        r_up = client.post(
            "/api/v1/vault/documents",
            files={"file": ("test_report.txt", sample_txt, "text/plain")},
            data={"document_category": "field_report"},
        )
        assert r_up.status_code == 200, r_up.text
        doc = r_up.json()["data"]
        assert doc["id"].startswith("vdoc-")
        assert doc["chunk_count"] >= 2
        assert doc["pdf_layout_blueprint"]["source_document"] == "test_report.txt"
        assert all(c["id"].startswith("vchk-") for c in doc["chunks"])

        r_del = client.delete(f"/api/v1/vault/documents/{doc['id']}")
        assert r_del.status_code == 200


def test_missing_api_keys_raise_actionable_external_provider_error(monkeypatch):
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-or-v1-test-key-present")

    with TestClient(app) as client:
        # Even when OPENROUTER_API_KEY is present, missing TAVILY_API_KEY must fail loudly (zero canned web sources)
        r_research = client.post(
            "/api/v1/research/query",
            json={"query": "ISO 19901-8 PCPT testing", "scope": "web"},
        )
        assert r_research.status_code == 502
        err_payload = r_research.json()["error"]
        assert err_payload["code"] == "EXTERNAL_PROVIDER_ERROR"
        assert "TAVILY_API_KEY" in err_payload["message"]

        r_img = client.post(
            "/api/v1/vault/images/search",
            json={"query": "Niger Delta geological map", "max_results": 4},
        )
        assert r_img.status_code == 502
        assert r_img.json()["error"]["code"] == "EXTERNAL_PROVIDER_ERROR"


def test_vault_ingestor_extracts_images_from_reference_docx(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        repo_root
        / "sample_reports"
        / "Geotechnical Survey Field Report - Anyala East and Anyala Central_01.docx",
        repo_root
        / "Geotechnical Survey Field Report - Anyala East and Anyala Central_01.docx",
    ]
    ref_docx = next((p for p in candidates if p.exists()), None)
    assert ref_docx is not None, "Expected reference .docx in sample_reports/"

    monkey_storage = StorageService()
    orig_root = settings.STORAGE_ROOT
    settings.STORAGE_ROOT = tmp_path
    try:
        ingestor = VaultIngestorService(storage=monkey_storage)
        chunks, assets, meta, blueprint = ingestor.ingest_with_blueprint(
            "test-vdoc", ref_docx.name, ref_docx.read_bytes()
        )
        assert len(chunks) >= 8
        assert len(assets) >= 12
        assert len(meta) == len(assets)
        assert blueprint["detected_headings"]
        assert blueprint["entities_json"]["client_operators"]
    finally:
        settings.STORAGE_ROOT = orig_root


def test_scientific_chart_generator_creates_all_5_charts(tmp_path):
    from app.services.chart_generator import ScientificChartGenerator

    orig_root = settings.STORAGE_ROOT
    settings.STORAGE_ROOT = tmp_path
    try:
        gen = ScientificChartGenerator(StorageService())
        suite = gen.generate_all_suite("pytest_hdd_report", is_offshore=False)
        assert len(suite) == 5
        for ch in suite:
            assert ch["file_url"]
            resolved = StorageService().resolve_path(ch["file_url"])
            assert resolved and resolved.exists()
            assert resolved.stat().st_size > 15_000
    finally:
        settings.STORAGE_ROOT = orig_root


def test_typst_compiler_preserves_clickable_toc_after_attachment_merge(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", tmp_path)

    ext_writer = PdfWriter()
    ext_writer.add_blank_page(width=595, height=842)
    ext_buf = io.BytesIO()
    ext_writer.write(ext_buf)

    ast = {
        "report_title": "Offshore Pipeline Crossing Geotechnical Investigation",
        "report_subtitle": "Interpretative & Factual Report",
        "program_title": "SUBSEA PIPELINE PROGRAM",
        "location_line": "",
        "campaign_dates": "",
        "abbreviations": [{"term": "PCPT", "definition": "Piezocone Penetration Test"}],
        "sections": [
            {
                "id": "sec-1",
                "section_number": "1.0",
                "title": "EXECUTIVE SUMMARY",
                "category": "Front Matter",
                "html_content": "<h3>1.1 Campaign Overview</h3><p>Field operations reached <strong>42.50 mBSF</strong> across ten boreholes.</p>",
                "tables": [
                    {
                        "id": "tbl-1",
                        "table_number": "Table 1.1",
                        "title": "Borehole Summary Coordinates",
                        "columns": ["Borehole ID", "Easting (m)", "Northing (m)", "Terminal Depth (mBSF)"],
                        "rows": [["BH-01", "389949.9720", "-9190.0210", "42.50"]],
                    }
                ],
                "placeholders": [],
            }
        ],
    }

    with TestClient(app) as client:
        proj = client.post(
            "/api/v1/projects",
            json={
                "title": "Offshore Pipeline Crossing Geotechnical Investigation",
                "client_name": "Atlantic Energy Ltd",
                "contractor_name": "Marine GeoConsult Ltd",
                "contractor_ref_code": "MGC-2026-014",
                "revision_number": "01",
            },
        ).json()["data"]
        r_ast = client.patch(
            f"/api/v1/projects/{proj['id']}/document", json={"document_ast_json": ast}
        )
        assert r_ast.status_code == 200, r_ast.text
        r_att = client.post(
            f"/api/v1/projects/{proj['id']}/attachments",
            files={"file": ("lab_appendix.pdf", ext_buf.getvalue(), "application/pdf")},
            data={"title": "Laboratory Appendix"},
        )
        assert r_att.status_code == 200, r_att.text
        r_comp = client.post(f"/api/v1/projects/{proj['id']}/compile-preview")
        assert r_comp.status_code == 200, r_comp.text
        data = r_comp.json()["data"]
        assert data["page_count"] >= 4
        pdf_bytes = client.get(data["compiled_pdf_url"].split("?")[0]).content
        assert pdf_bytes[:4] == b"%PDF"

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_links = sum(len(page.get_links()) for page in doc)
    assert total_links >= 2, "Expected clickable TOC / List of Tables links in merged PDF"
    assert len(PdfReader(io.BytesIO(pdf_bytes)).pages) == data["page_count"]
