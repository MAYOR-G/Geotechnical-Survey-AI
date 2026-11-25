import io
from pathlib import Path
import re
from typing import Any
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from PIL import Image
from app.core.exceptions import CompilationError
from app.models.project import Project
from app.services.pdf_compiler import html_to_blocks
from app.services.storage_service import StorageService


def set_cell_shading(cell, fill_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tr_pr.append(tbl_header)


def _image_stream_for_docx(path: Path | None) -> io.BytesIO | None:
    """Ensure PNG/JPEG/WEBP images load cleanly into python-docx without format errors."""
    if not path or not path.exists():
        return None
    ext = path.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg"):
        return io.BytesIO(path.read_bytes())
    if ext == ".webp":
        try:
            out = io.BytesIO()
            with Image.open(path) as im:
                im.convert("RGB").save(out, format="PNG")
            out.seek(0)
            return out
        except Exception:
            return None
    return None


class DocxCompilerService:
    """Compiles the canonical DocumentAst into a fully editable A4 MS Word (.docx) deliverable."""

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()

    def _logo_paths(self, project: Project):
        logos = project.header_logos_json or []
        c_url = next((l.get("url") for l in logos if l.get("role") == "client"), "")
        g_url = next((l.get("url") for l in logos if l.get("role") == "contractor"), "")
        p_url = next((l.get("url") for l in logos if l.get("role") == "partner"), "")
        return (
            self.storage.resolve_path(c_url) if c_url else None,
            self.storage.resolve_path(g_url) if g_url else None,
            self.storage.resolve_path(p_url) if p_url else None,
        )

    def compile_project_docx(self, project: Project) -> str:
        try:
            doc = Document()
            section = doc.sections[0]
            section.page_width = Mm(210)
            section.page_height = Mm(297)
            section.top_margin = Mm(22)
            section.bottom_margin = Mm(18)
            section.left_margin = Mm(18)
            section.right_margin = Mm(18)

            ast = project.document_ast_json or {}
            client_logo, contractor_logo, partner_logo = self._logo_paths(project)

            # Running Corporate 2-Cell Header (Client | Contractor)
            header = section.header
            htbl = header.add_table(rows=1, cols=2, width=Inches(6.8))
            htbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            htbl.style = "Table Grid"
            hc0, hc1 = htbl.rows[0].cells
            p0 = hc0.paragraphs[0]
            c_stream = _image_stream_for_docx(client_logo)
            if c_stream:
                p0.add_run().add_picture(c_stream, height=Inches(0.42))
            else:
                p0.add_run(project.client_name or "Client / Operator").font.size = Pt(8.5)

            p1 = hc1.paragraphs[0]
            p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            g_stream = _image_stream_for_docx(contractor_logo)
            p_stream = _image_stream_for_docx(partner_logo)
            if g_stream:
                p1.add_run().add_picture(g_stream, height=Inches(0.38))
                p1.add_run("   ")
            else:
                p1.add_run(project.contractor_name or "Geotechnical Consultant").font.size = Pt(8.5)
            if p_stream:
                p1.add_run().add_picture(p_stream, height=Inches(0.32))

            # Cover Title Block
            cover_lines = [
                (ast.get("program_title") or project.document_type or "Geotechnical Engineering Report", 14),
                (ast.get("report_title") or project.title or "Geotechnical Investigation Report", 20),
            ]
            sub_line = ast.get("report_subtitle") or project.subtitle
            if sub_line:
                cover_lines.append((sub_line, 14))
            for line, sz in cover_lines:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(16 if sz == 20 else 8)
                r = p.add_run(line)
                r.bold = True
                r.font.size = Pt(sz)
                r.font.color.rgb = RGBColor(0x1D, 0x1D, 0x1F)

            rev_p = doc.add_paragraph()
            rev_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rev_p.paragraph_format.space_before = Pt(18)
            rev_r = rev_p.add_run(f"Revision: {project.revision_number or 'Rev 01'}")
            rev_r.bold = True
            rev_r.font.size = Pt(12)

            ref_p = doc.add_paragraph()
            ref_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            client_lbl = project.client_name or "Client"
            contractor_lbl = project.contractor_name or "Contractor"
            ref_r = ref_p.add_run(
                f"{client_lbl} Document Ref.: {project.client_ref_code or project.id.upper()}\n"
                f"{contractor_lbl} Document Ref.: {project.contractor_ref_code or project.id.upper()}"
            )
            ref_r.bold = True
            ref_r.font.size = Pt(10)

            conf_p = doc.add_paragraph()
            conf_p.paragraph_format.space_before = Pt(22)
            owner_lbl = project.contractor_name or "the Contractor"
            conf_r = conf_p.add_run(
                f"This document is proprietary and confidential. Copyright is vested in {owner_lbl}. All rights reserved. "
                "Neither the whole nor any part of this document may be disclosed to any third party nor reproduced without prior written consent."
            )
            conf_r.font.size = Pt(8.5)

            if project.revision_history_json:
                self._add_styled_table(
                    doc,
                    ["Rev", "Date", "Reason for Revision", "Prepared", "Checked", "Approved"],
                    [
                        [
                            r.get("rev", ""),
                            r.get("date", ""),
                            r.get("description", ""),
                            r.get("prepared_by", ""),
                            r.get("checked_by", ""),
                            r.get("approved_by", ""),
                        ]
                        for r in project.revision_history_json
                    ],
                )

            # Page 2: DOCUMENT AUTHORISATION AND DISTRIBUTION
            doc.add_page_break()
            h_auth = doc.add_heading("DOCUMENT AUTHORISATION AND DISTRIBUTION", level=1)
            h_auth.paragraph_format.keep_with_next = True

            auths = project.authorization_matrix_json or []
            prep = next((a for a in auths if "prepar" in a.get("role", "").lower()), {})
            revw = next((a for a in auths if "review" in a.get("role", "").lower() or "check" in a.get("role", "").lower()), {})
            aprv_list = [a for a in auths if "approv" in a.get("role", "").lower()]
            aprv1 = aprv_list[0] if len(aprv_list) > 0 else {}
            aprv2 = aprv_list[1] if len(aprv_list) > 1 else {}

            prep_str = ", ".join(x for x in (prep.get("name", ""), prep.get("email", "")) if x) or "Lead Geotechnical Engineer"
            revw_str = "; ".join(x for x in (revw.get("name", ""), revw.get("email", "")) if x) or "Principal Reviewer"
            aprv_str = "; ".join(x for x in (aprv1.get("name", ""), aprv1.get("email", "")) if x) or "Technical Director"

            self._add_styled_table(
                doc,
                ["Document Authorisation and Distribution", "Details"],
                [
                    ["Contractor", project.contractor_name or "—"],
                    ["Client", project.client_name or "—"],
                    ["FAO", project.fao_text or project.client_name or "—"],
                    ["Document Ref.", project.contractor_ref_code or project.id.upper()],
                    ["Title", f"{project.title}{(' — ' + project.subtitle) if project.subtitle else ''}"],
                    ["Author", f"{prep_str}  (Date: {prep.get('date') or '2026'})"],
                    ["Checked", f"{revw_str}  (Date: {revw.get('date') or '2026'})"],
                    ["Approved", f"{aprv_str}  (Date: {aprv1.get('date') or '2026'})"],
                    ["Authorised Copies (Original)", project.client_name or "Client"],
                    ["Authorised Copies (Copy No. 1)", project.contractor_name or "Contractor"],
                ],
            )

            sig_tbl = doc.add_table(rows=5, cols=5)
            sig_tbl.style = "Table Grid"
            sig_headers = ["Role", "Prepared By", "Reviewed By", "Approved By", "Approved By"]
            set_repeat_table_header(sig_tbl.rows[0])
            for idx, txt in enumerate(sig_headers):
                c = sig_tbl.rows[0].cells[idx]
                set_cell_shading(c, "F5F5F7")
                r = c.paragraphs[0].add_run(txt)
                r.bold = True
                r.font.size = Pt(8.5)

            sig_tbl.rows[1].cells[0].paragraphs[0].add_run("Signature").bold = True
            sig_stream = _image_stream_for_docx(self.storage.resolve_path(prep.get("signature_url") or ""))
            if sig_stream:
                try:
                    sig_tbl.rows[1].cells[1].paragraphs[0].add_run().add_picture(sig_stream, height=Inches(0.42))
                except Exception:
                    pass

            for row_i, label, vals in [
                (2, "Name", [prep.get("name", ""), revw.get("name", ""), aprv1.get("name", ""), aprv2.get("name", "")]),
                (3, "Designation", [prep.get("designation", ""), revw.get("designation", ""), aprv1.get("designation", ""), aprv2.get("designation", "")]),
                (4, "Date", [prep.get("date", ""), revw.get("date", ""), aprv1.get("date", ""), aprv2.get("date", "")]),
            ]:
                sig_tbl.rows[row_i].cells[0].paragraphs[0].add_run(label).bold = True
                for c_i, val in enumerate(vals, start=1):
                    r = sig_tbl.rows[row_i].cells[c_i].paragraphs[0].add_run(val or "—")
                    r.font.size = Pt(8.5)

            doc.add_page_break()

            abbrs = ast.get("abbreviations", [])
            if abbrs:
                h_ab = doc.add_heading("ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS", level=1)
                h_ab.paragraph_format.keep_with_next = True
                self._add_styled_table(
                    doc,
                    ["Abbreviation / Symbol", "Expression in Full"],
                    [[a.get("term", ""), a.get("definition", "")] for a in abbrs],
                )

            # Continuous chapter flow (no forced blank half-pages between sections)
            for sec in ast.get("sections", []):
                h_sec = doc.add_heading(
                    f"{sec.get('section_number', '')} {sec.get('title', '')}".strip(),
                    level=1,
                )
                h_sec.paragraph_format.space_before = Pt(18)
                h_sec.paragraph_format.space_after = Pt(6)
                h_sec.paragraph_format.keep_with_next = True

                for kind, text_block in html_to_blocks(sec.get("html_content", "")):
                    if kind == "h3":
                        h_sub = doc.add_heading(text_block, level=2)
                        h_sub.paragraph_format.space_before = Pt(11)
                        h_sub.paragraph_format.keep_with_next = True
                    else:
                        p = doc.add_paragraph(text_block)
                        p.paragraph_format.space_after = Pt(6)
                        p.paragraph_format.widow_control = True
                        for r in p.runs:
                            r.font.size = Pt(10.0)

                for tbl in sec.get("tables") or []:
                    t_cap = doc.add_heading(
                        f"{tbl.get('table_number') or 'Table'}: {tbl.get('title', '')}",
                        level=3,
                    )
                    t_cap.paragraph_format.keep_with_next = True
                    self._add_styled_table(
                        doc,
                        tbl.get("columns", []),
                        tbl.get("rows", []),
                        multi_header=tbl.get("multi_header"),
                        footnote=tbl.get("footnote"),
                    )

                for ph in sec.get("placeholders") or []:
                    resolved_url = ph.get("resolved_url")
                    secondary_url = ph.get("secondary_url")
                    layout = ph.get("layout") or ("side_by_side" if secondary_url else "single")
                    caption = ph.get("caption") or f"{ph.get('figure_number', 'Figure')}: {ph.get('prompt', '')}"
                    p1_stream = _image_stream_for_docx(self.storage.resolve_path(resolved_url) if resolved_url else None)
                    p2_stream = _image_stream_for_docx(self.storage.resolve_path(secondary_url) if secondary_url else None)

                    if p1_stream and p2_stream and layout == "side_by_side":
                        pair_tbl = doc.add_table(rows=1, cols=2)
                        pair_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                        c_l = pair_tbl.rows[0].cells[0].paragraphs[0]
                        c_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        c_l.add_run().add_picture(p1_stream, width=Inches(3.1))
                        c_r = pair_tbl.rows[0].cells[1].paragraphs[0]
                        c_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        c_r.add_run().add_picture(p2_stream, width=Inches(3.1))
                        cap_p = doc.add_paragraph()
                        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap_r = cap_p.add_run(caption)
                        cap_r.bold = True
                        cap_r.font.size = Pt(9.5)
                    elif p1_stream:
                        fig_p = doc.add_paragraph()
                        fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        fig_p.paragraph_format.keep_with_next = True
                        try:
                            fig_p.add_run().add_picture(p1_stream, width=Inches(5.8))
                        except Exception:
                            fig_p.add_run(f"[{caption}]").italic = True
                        cap_p = doc.add_paragraph()
                        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap_r = cap_p.add_run(caption)
                        cap_r.bold = True
                        cap_r.font.size = Pt(9.5)

            if project.attachments:
                h_att = doc.add_heading("APPENDED EXTERNAL PDF ATTACHMENTS", level=1)
                h_att.paragraph_format.space_before = Pt(18)
                h_att.paragraph_format.keep_with_next = True
                self._add_styled_table(
                    doc,
                    ["Order", "Attachment No.", "Document Title", "Pages"],
                    [
                        [
                            str(att.display_order),
                            att.attachment_number,
                            att.title,
                            str(att.page_count),
                        ]
                        for att in sorted(
                            project.attachments, key=lambda a: a.display_order
                        )
                    ],
                )

            buf = io.BytesIO()
            doc.save(buf)
            safe_ref = re.sub(
                r"[^a-zA-Z0-9_-]+", "_", project.contractor_ref_code or project.id
            )
            url, _ = self.storage.save_bytes(
                "compiled-exports", f"{safe_ref}.docx", buf.getvalue(), deterministic=True
            )
            return url
        except Exception as exc:
            raise CompilationError(f"Failed to compile Word (.docx) file: {exc}") from exc

    def _add_styled_table(
        self,
        doc: Document,
        columns: list[str],
        rows: list[list[Any]],
        multi_header: list[list[dict[str, Any]]] | None = None,
        footnote: str | None = None,
    ) -> None:
        if not columns:
            return
        n_hdr = len(multi_header) if multi_header else 1
        n_cols = len(columns)
        tbl = doc.add_table(rows=n_hdr + len(rows), cols=n_cols)
        tbl.style = "Table Grid"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        font_sz = Pt(6.8) if n_cols > 8 else Pt(8.5)

        for hr_i in range(n_hdr):
            set_repeat_table_header(tbl.rows[hr_i])

        if multi_header:
            occupied = [[False] * n_cols for _ in range(n_hdr)]
            for r_idx, h_row in enumerate(multi_header):
                c_cursor = 0
                for cell_spec in h_row:
                    while c_cursor < n_cols and occupied[r_idx][c_cursor]:
                        c_cursor += 1
                    if c_cursor >= n_cols:
                        break
                    colspan = int(cell_spec.get("colspan") or 1)
                    rowspan = int(cell_spec.get("rowspan") or 1)
                    for rr in range(r_idx, min(n_hdr, r_idx + rowspan)):
                        for cc in range(c_cursor, min(n_cols, c_cursor + colspan)):
                            occupied[rr][cc] = True
                    target = tbl.rows[r_idx].cells[c_cursor]
                    if colspan > 1 or rowspan > 1:
                        end_cell = tbl.rows[min(n_hdr - 1, r_idx + rowspan - 1)].cells[min(n_cols - 1, c_cursor + colspan - 1)]
                        target.merge(end_cell)
                    set_cell_shading(target, "F5F5F7")
                    p = target.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p.add_run(str(cell_spec.get("label") or ""))
                    r.bold = True
                    r.font.size = font_sz
                    c_cursor += colspan
        else:
            for idx, col in enumerate(columns):
                cell = tbl.rows[0].cells[idx]
                set_cell_shading(cell, "F5F5F7")
                p = cell.paragraphs[0]
                r = p.add_run(str(col))
                r.bold = True
                r.font.size = font_sz

        for r_idx, row in enumerate(rows, start=n_hdr):
            for c_idx in range(n_cols):
                val = str(row[c_idx]) if c_idx < len(row) else ""
                cell = tbl.rows[r_idx].cells[c_idx]
                p = cell.paragraphs[0]
                r = p.add_run(val)
                r.font.size = font_sz

        if footnote:
            fp = doc.add_paragraph()
            fr = fp.add_run(footnote)
            fr.italic = True
            fr.font.size = Pt(8.0)
