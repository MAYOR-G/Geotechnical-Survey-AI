import html as html_lib
import io
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any
from PIL import Image
from pypdf import PdfReader, PdfWriter
import typst
from app.core.exceptions import CompilationError
from app.models.project import Project
from app.services.storage_service import StorageService

TYPST_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "typst"


def escape_typst_text(raw: Any) -> str:
    """Safely escape arbitrary user or table text for Typst content blocks [...] without syntax errors."""
    if raw is None:
        return ""
    s = html_lib.unescape(str(raw))
    s = s.replace("\\", "\\\\")
    for ch in ("#", "$", "@", "<", ">", "*", "_", "`", "~", "[", "]", "="):
        s = s.replace(ch, f"\\{ch}")
    return re.sub(r"[ \t]+", " ", s).strip()


def escape_typst_string(raw: Any) -> str:
    """Safely escape text for a Typst quoted string literal "..."."""
    if raw is None:
        return ""
    s = html_lib.unescape(str(raw))
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return s.strip()


def _inline_html_to_typst(fragment: str) -> str:
    """Convert inline HTML (`<strong>`, `<em>`, `<sub>`, `<sup>`) into safe Typst inline markup."""
    if not fragment:
        return ""
    token_re = re.compile(
        r"<(strong|b|em|i|sub|sup)>(.*?)</\1>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    parts: list[str] = []
    last = 0
    for m in token_re.finditer(fragment):
        if m.start() > last:
            raw_chunk = re.sub(r"<[^>]+>", " ", fragment[last : m.start()])
            esc_chunk = escape_typst_text(raw_chunk)
            if esc_chunk:
                parts.append(esc_chunk)
        tag = m.group(1).lower()
        inner_raw = re.sub(r"<[^>]+>", " ", m.group(2))
        inner_esc = escape_typst_text(inner_raw)
        if inner_esc:
            if tag in ("strong", "b"):
                parts.append(f"#strong[{inner_esc}]")
            elif tag in ("em", "i"):
                parts.append(f"#emph[{inner_esc}]")
            elif tag == "sub":
                parts.append(f"#sub[{inner_esc}]")
            elif tag == "sup":
                parts.append(f"#super[{inner_esc}]")
        last = m.end()

    if last < len(fragment):
        tail_raw = re.sub(r"<[^>]+>", " ", fragment[last:])
        tail_esc = escape_typst_text(tail_raw)
        if tail_esc:
            parts.append(tail_esc)

    return " ".join(parts).strip()


def _formula_to_typst_math(formula_text: str) -> str:
    """Map standard geotechnical formula lines to native Typst math equations."""
    low = formula_text.lower()
    if "m2" in low and "m1" in low and "m3" in low:
        return '$ w = ((M_2 - M_1) / (M_3 - M_1)) times 100% $'
    if "d60" in low and "d10" in low:
        return '$ C_u = D_60 / D_10, quad C_c = (D_30)^2 / (D_10 times D_60), quad k = C_H times (D_10)^2 $'
    if "ll" in low and "pl" in low and "pi" in low:
        return '$ "PI" = "LL" - "PL", quad "LI" = (w - "PL") / "PI" $'
    if "tau_f" in low or "tan(" in low or "mohr" in low:
        return '$ tau_f = c\' + sigma\'_n tan(phi\'), quad c_u = (sigma_1 - sigma_3)_f / 2 $'
    if "log10" in low or "t50" in low or "ocr" in low:
        return '$ C_c = (-Delta e) / (Delta log_10(sigma\'_v)), quad m_v = (Delta e / (1 + e_0)) (1 / (Delta sigma\'_v)), quad c_v = (T_50 H_d^2) / t_50, quad "OCR" = p\'_c / sigma\'_(v 0) $'
    if "gamma_bulk" in low or "γ_bulk" in low:
        return '$ gamma_"bulk" = rho_"bulk" times g, quad gamma_"dry" = gamma_"bulk" / (1 + w), quad gamma\' = gamma_"bulk" - gamma_w $'
    if "sulphate" in low and "0.343" in low:
        return '$ "Sulphate (mg/kg)" = (1000 times d times 0.343 times V_1 times 1000) / (V_2 times M_1) $'
    if "chloride" in low and "mm" in low:
        return '$ "Chloride (mg/L)" = (V_3 times N times "MM" times V_1 times 1000) / (V_2 times M_1) $'
    if "p_f" in low or "delft" in low or "ln(g" in low:
        return '$ P_(f,"clay") = u_0 + sigma\'_0 (1 + ln(G / c_u)), quad F_s = P_f / P_a >= 1.50 $'
    return ""


def html_to_typst_blocks(html: str) -> str:
    """Convert section HTML (`<p>`, `<h3>`, `<h4>`, `<ul>`, `<ol>`, `<li>`, `<p class="formula">`) into Typst markup."""
    if not html or not html.strip():
        return ""

    block_re = re.compile(
        r'<p[^>]*class=["\']?formula["\']?[^>]*>.*?</p>'
        r"|<h([2-4])[^>]*>(.*?)</h\1>"
        r"|<ol[^>]*>(.*?)</ol>"
        r"|<ul[^>]*>(.*?)</ul>"
        r"|<li[^>]*>(.*?)</li>"
        r"|<p[^>]*>(.*?)</p>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    matches = list(block_re.finditer(html))
    if not matches:
        plain = re.sub(r"<[^>]+>", " ", html)
        lines = [escape_typst_text(ln) for ln in plain.splitlines() if ln.strip()]
        return "\n\n".join(lines)

    out_lines: list[str] = []
    for m in matches:
        full_tok = m.group(0)
        tok_low = full_tok.lower()

        if tok_low.startswith("<p") and ("class=\"formula\"" in tok_low or "class='formula'" in tok_low):
            clean_inner = re.sub(r"<[^>]+>", " ", full_tok)
            clean_inner = re.sub(r"\s+", " ", html_lib.unescape(clean_inner)).strip()
            if not clean_inner:
                continue
            native_math = _formula_to_typst_math(clean_inner)
            escaped_lbl = escape_typst_text(clean_inner)
            if native_math:
                out_lines.append(
                    f'#block(width: 100%, fill: rgb("#FAFAFC"), stroke: (left: 2.2pt + rgb("#0066CC"), rest: 0.45pt + rgb("#E0E0E0")), inset: 8pt, radius: 3pt, breakable: false)[\n'
                    f'  #text(size: 8.8pt, weight: "bold", fill: rgb("#0066CC"))[{escaped_lbl}]\n'
                    f"  #v(4pt)\n"
                    f"  #align(center)[{native_math}]\n"
                    f"]"
                )
            else:
                out_lines.append(
                    f'#block(width: 100%, fill: rgb("#FAFAFC"), stroke: (left: 2.2pt + rgb("#0066CC"), rest: 0.45pt + rgb("#E0E0E0")), inset: 8pt, radius: 3pt, breakable: false)[#text(weight: "bold")[{escaped_lbl}]]'
                )
        elif m.group(1) is not None:
            h_lvl = int(m.group(1))
            h_txt = escape_typst_text(re.sub(r"<[^>]+>", " ", m.group(2) or ""))
            if h_txt:
                prefix = "==" if h_lvl <= 3 else "==="
                out_lines.append(f"{prefix} {h_txt}")
        elif m.group(3) is not None:
            items = re.findall(r"<li[^>]*>(.*?)</li>", m.group(3), flags=re.IGNORECASE | re.DOTALL)
            li_lines = [f"+ {_inline_html_to_typst(it)}" for it in items if _inline_html_to_typst(it)]
            if li_lines:
                out_lines.append("\n".join(li_lines))
        elif m.group(4) is not None:
            items = re.findall(r"<li[^>]*>(.*?)</li>", m.group(4), flags=re.IGNORECASE | re.DOTALL)
            li_lines = [f"- {_inline_html_to_typst(it)}" for it in items if _inline_html_to_typst(it)]
            if li_lines:
                out_lines.append("\n".join(li_lines))
        elif m.group(5) is not None:
            li_txt = _inline_html_to_typst(m.group(5))
            if li_txt:
                out_lines.append(f"- {li_txt}")
        elif m.group(6) is not None:
            p_txt = _inline_html_to_typst(m.group(6))
            if p_txt:
                out_lines.append(p_txt)

    return "\n\n".join(out_lines)


def _compute_column_weights(columns: list[str], rows: list[list[Any]]) -> str:
    """Compute proportional Typst column weights (`fr`) so narrow IDs don't steal width from descriptions."""
    weights: list[str] = []
    for idx, col in enumerate(columns):
        c_low = str(col).strip().lower()
        sample_lens = [
            len(str(r[idx])) for r in rows[:15] if idx < len(r) and r[idx] is not None
        ]
        avg_len = (sum(sample_lens) / len(sample_lens)) if sample_lens else len(c_low)

        if c_low in ("s/n", "sn", "no.", "no", "rev", "order", "#"):
            w = 0.55
        elif any(k in c_low for k in ("description", "remarks", "significance", "mitigation", "title", "scope", "expression", "definition", "interpretation")):
            w = 2.45
        elif avg_len > 48:
            w = 2.2
        elif avg_len > 24:
            w = 1.45
        elif avg_len < 8 and len(c_low) < 12:
            w = 0.78
        else:
            w = 1.05
        weights.append(f"{w:.2f}fr")
    return ", ".join(weights)


class TypstCompilerService:
    """
    Compiles the canonical DocumentAst into a publication-grade A4 PDF via Typst (`typst.compile`)
    and merges external ProjectAttachment PDFs via `pypdf` while preserving clickable TOC/LOF/LOT links.
    """

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()

    def _is_offshore_project(self, project: Project, ast: dict[str, Any]) -> bool:
        combined = f"{project.title} {project.subtitle} {project.document_type} {project.vessel_name}".lower()
        if any(k in combined for k in ("hdd", "directional drilling", "river crossing", "bore path", "trenchless")):
            return False
        if any(k in combined for k in ("offshore", "marine", "oml", "dp-2", "vessel", "mbsf", "pcpt")):
            return True
        return False

    def _copy_image_to_workdir(
        self, url_or_path: str | None, workdir: Path, prefix: str
    ) -> str | None:
        if not url_or_path:
            return None
        resolved = self.storage.resolve_path(url_or_path)
        if not resolved or not resolved.exists():
            return None
        ext = resolved.suffix.lower()
        safe_base = re.sub(r"[^a-zA-Z0-9._-]+", "_", f"{prefix}_{resolved.stem}")
        if ext in (".png", ".jpg", ".jpeg", ".svg"):
            dest_name = f"{safe_base}{ext}"
            dest_path = workdir / dest_name
            try:
                shutil.copyfile(resolved, dest_path)
                return dest_name
            except Exception:
                return None
        if ext == ".webp":
            dest_name = f"{safe_base}.png"
            dest_path = workdir / dest_name
            try:
                with Image.open(resolved) as im:
                    im.convert("RGBA").save(dest_path, format="PNG")
                return dest_name
            except Exception:
                return None
        return None

    def _render_table_typst(self, tbl: dict[str, Any], tbl_idx: int) -> str:
        columns = list(tbl.get("columns") or [])
        rows = list(tbl.get("rows") or [])
        if not columns:
            return ""

        col_count = len(columns)
        tbl_num = str(tbl.get("table_number") or f"Table {tbl_idx}")
        raw_title = str(tbl.get("title") or "Engineering Data Table")
        clean_title = re.sub(r"^Table\s+[A-Za-z0-9.]+\s*[:—-]?\s*", "", raw_title, flags=re.IGNORECASE).strip()
        full_caption = escape_typst_text(clean_title or raw_title)

        is_wide = col_count >= 10
        font_sz = "6.6pt" if col_count >= 12 else ("7.8pt" if col_count >= 7 else "8.6pt")
        col_spec = _compute_column_weights(columns, rows)

        multi_header = tbl.get("multi_header")
        header_cells: list[str] = []
        if isinstance(multi_header, list) and len(multi_header) > 0:
            for h_row in multi_header:
                for cell in h_row:
                    lbl = escape_typst_text(cell.get("label", ""))
                    cs = int(cell.get("colspan") or 1)
                    rs = int(cell.get("rowspan") or 1)
                    args = ['fill: rgb("#F5F5F7")']
                    if cs > 1:
                        args.append(f"colspan: {cs}")
                    if rs > 1:
                        args.append(f"rowspan: {rs}")
                    header_cells.append(f"table.cell({', '.join(args)})[#strong[#text(size: {font_sz})[{lbl}]]]")
        else:
            for col in columns:
                lbl = escape_typst_text(col)
                header_cells.append(f'table.cell(fill: rgb("#F5F5F7"))[#strong[#text(size: {font_sz})[{lbl}]]]')

        body_cells: list[str] = []
        for r_idx, row in enumerate(rows):
            row_fill = 'rgb("#FFFFFF")' if r_idx % 2 == 0 else 'rgb("#FAFAFC")'
            for c_idx in range(col_count):
                val = row[c_idx] if c_idx < len(row) else ""
                esc_val = escape_typst_text(val)
                body_cells.append(
                    f"table.cell(fill: {row_fill})[#text(size: {font_sz})[{esc_val}]]"
                )

        footnote_block = ""
        if tbl.get("footnote"):
            fn_esc = escape_typst_text(tbl.get("footnote"))
            footnote_block = f'\n#v(2pt)\n#align(left)[#text(size: 7.8pt, style: "italic", fill: rgb("#4B5565"))[{fn_esc}]]'

        table_markup = (
            f"#figure(\n"
            f"  kind: table,\n"
            f"  supplement: [Table],\n"
            f"  caption: [{full_caption}],\n"
            f")[\n"
            f"  #set text(number-type: \"lining\", number-width: \"tabular\")\n"
            f"  #table(\n"
            f"    columns: ({col_spec}),\n"
            f"    stroke: 0.6pt + rgb(\"#1D1D1F\"),\n"
            f"    inset: (x: 5pt, y: 4.5pt),\n"
            f"    align: left + horizon,\n"
            f"    table.header(repeat: true,\n      "
            + ",\n      ".join(header_cells)
            + "\n    ),\n    "
            + ",\n    ".join(body_cells)
            + "\n  )"
            + footnote_block
            + "\n]"
        )

        if is_wide:
            return (
                f"\n#page(paper: \"a4\", flipped: true, margin: (top: 2.6cm, bottom: 2.0cm, left: 1.5cm, right: 1.5cm))[\n"
                f"  {table_markup}\n"
                f"]\n"
            )
        return f"\n#v(6pt)\n{table_markup}\n#v(6pt)\n"

    def _render_figure_typst(
        self, ph: dict[str, Any], workdir: Path, fig_idx: int
    ) -> str:
        primary_rel = self._copy_image_to_workdir(
            ph.get("resolved_url"), workdir, f"fig_{fig_idx}_a"
        )
        sec_rel = self._copy_image_to_workdir(
            ph.get("secondary_url"), workdir, f"fig_{fig_idx}_b"
        )
        raw_cap = str(
            ph.get("caption")
            or f"{ph.get('figure_number', f'Figure {fig_idx}')}: {ph.get('prompt', 'Engineering Figure')}"
        )
        clean_cap = re.sub(r"^Figure\s+[A-Za-z0-9.]+\s*[:—-]?\s*", "", raw_cap, flags=re.IGNORECASE).strip()
        esc_cap = escape_typst_text(clean_cap or raw_cap)

        if not primary_rel:
            return ""

        if sec_rel and (ph.get("layout") or "side_by_side") == "side_by_side":
            return (
                f"\n#v(6pt)\n"
                f"#figure(\n"
                f"  kind: image,\n"
                f"  supplement: [Figure],\n"
                f"  caption: [{esc_cap}],\n"
                f")[\n"
                f"  #grid(\n"
                f"    columns: (1fr, 1fr),\n"
                f"    gutter: 10pt,\n"
                f'    image("{escape_typst_string(primary_rel)}", width: 100%, height: 6.0cm, fit: "contain"),\n'
                f'    image("{escape_typst_string(sec_rel)}", width: 100%, height: 6.0cm, fit: "contain"),\n'
                f"  )\n"
                f"]\n#v(6pt)\n"
            )

        return (
            f"\n#v(6pt)\n"
            f"#figure(\n"
            f"  kind: image,\n"
            f"  supplement: [Figure],\n"
            f"  caption: [{esc_cap}],\n"
            f")[\n"
            f'  #image("{escape_typst_string(primary_rel)}", width: 92%, height: 7.4cm, fit: "contain")\n'
            f"]\n#v(6pt)\n"
        )

    def compile_project_pdf(self, project: Project) -> tuple[str, int]:
        try:
            ast = project.document_ast_json or {}
            is_offshore = self._is_offshore_project(project, ast)
            template_name = (
                "offshore_field_report.typ"
                if is_offshore
                else "hdd_geotechnical_report.typ"
            )
            entry_func = (
                "render-offshore-report" if is_offshore else "render-hdd-report"
            )

            with tempfile.TemporaryDirectory(prefix="geotech_typst_") as tmp_str:
                workdir = Path(tmp_str)
                shutil.copyfile(
                    TYPST_TEMPLATES_DIR / template_name, workdir / template_name
                )

                # Copy strictly project-configured corporate logos & signature (no cross-project leakage)
                logos = project.header_logos_json or []
                c_url = next((l.get("url") for l in logos if l.get("role") == "client"), "")
                g_url = next((l.get("url") for l in logos if l.get("role") == "contractor"), "")
                p_url = next((l.get("url") for l in logos if l.get("role") == "partner"), "")

                c_logo_rel = self._copy_image_to_workdir(c_url, workdir, "logo_client")
                g_logo_rel = self._copy_image_to_workdir(g_url, workdir, "logo_contractor")
                p_logo_rel = self._copy_image_to_workdir(p_url, workdir, "logo_partner")

                auths = project.authorization_matrix_json or []
                prep = next((a for a in auths if "prepar" in a.get("role", "").lower()), {})
                revw = next((a for a in auths if "review" in a.get("role", "").lower() or "check" in a.get("role", "").lower()), {})
                aprv_list = [a for a in auths if "approv" in a.get("role", "").lower()]
                aprv1 = aprv_list[0] if len(aprv_list) > 0 else {}
                aprv2 = aprv_list[1] if len(aprv_list) > 1 else {}

                sig_url = prep.get("signature_url") or ""
                sig_rel = self._copy_image_to_workdir(sig_url, workdir, "sig_prepared")

                body_parts: list[str] = []

                abbrs = list(ast.get("abbreviations") or [])
                if abbrs:
                    body_parts.append("= ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS\n")
                    body_parts.append(
                        "The following technical abbreviations, symbols, and nomenclature are utilized throughout the interpretative and factual sections of this report:\n"
                    )
                    abbr_tbl = {
                        "table_number": "Table 1.1",
                        "title": "Abbreviations, Symbols and Geotechnical Nomenclature",
                        "columns": ["Abbreviation / Symbol", "Expression in Full"],
                        "rows": [
                            [a.get("term", ""), a.get("definition", "")]
                            for a in abbrs
                        ],
                    }
                    body_parts.append(self._render_table_typst(abbr_tbl, 1))

                tbl_counter = 2
                fig_counter = 1
                sections = list(ast.get("sections") or [])

                if not sections:
                    body_parts.append("= 1.0 PROJECT INITIALIZATION\n")
                    body_parts.append(
                        escape_typst_text(
                            f"This deliverable workspace has been initialized for {project.title}. "
                            "Use the Studio Agent to run intake verification and iterative section-by-section drafting."
                        )
                    )

                for sec in sections:
                    sec_num = str(sec.get("section_number") or "").strip()
                    sec_title = str(sec.get("title") or "SECTION").strip()
                    heading_str = escape_typst_text(f"{sec_num} {sec_title}".strip())
                    body_parts.append(f"\n= {heading_str}\n")

                    prose_typst = html_to_typst_blocks(sec.get("html_content", ""))
                    if prose_typst:
                        body_parts.append(prose_typst + "\n")

                    for tbl in sec.get("tables") or []:
                        body_parts.append(self._render_table_typst(tbl, tbl_counter))
                        tbl_counter += 1

                    for ph in sec.get("placeholders") or []:
                        fig_typ = self._render_figure_typst(ph, workdir, fig_counter)
                        if fig_typ:
                            body_parts.append(fig_typ)
                            fig_counter += 1

                rev_rows = project.revision_history_json or [
                    {
                        "rev": project.revision_number or "01",
                        "date": "2026",
                        "description": "Issued for Review",
                        "prepared_by": prep.get("name") or "—",
                        "checked_by": revw.get("name") or "—",
                        "approved_by": aprv1.get("name") or "—",
                    }
                ]
                typ_rev_rows = []
                for r in rev_rows[:5]:
                    typ_rev_rows.append(
                        "("
                        + ", ".join(
                            f"[{escape_typst_text(r.get(k) or '—')}]"
                            for k in (
                                "rev",
                                "date",
                                "description",
                                "prepared_by",
                                "checked_by",
                                "approved_by",
                            )
                        )
                        + ")"
                    )
                rev_tuple_str = (
                    "(" + ", ".join(typ_rev_rows) + ("," if len(typ_rev_rows) == 1 else "") + ")"
                    if typ_rev_rows
                    else "(([01], [2026], [Issued for Review], [—], [—], [—]),)"
                )

                def _opt_str(val: str | None) -> str:
                    return f'"{escape_typst_string(val)}"' if val else "none"

                def _auth_dict(d: dict[str, Any], default_name: str, default_role: str) -> str:
                    nm = escape_typst_string(d.get("name") or default_name)
                    ds = escape_typst_string(d.get("designation") or default_role)
                    dt = escape_typst_string(d.get("date") or "2026")
                    return f'(name: "{nm}", designation: "{ds}", date: "{dt}")'

                client_display = project.client_name or "Client / Operator"
                contractor_display = project.contractor_name or "Geotechnical Engineering Consultant"
                doc_ref_contractor = project.contractor_ref_code or project.id.upper()
                doc_ref_client = project.client_ref_code or doc_ref_contractor

                consultant_arg = (
                    f'  consultant-name: "{escape_typst_string(contractor_display)}",\n'
                    if not is_offshore
                    else ""
                )

                main_typ = (
                    f'#import "{template_name}": {entry_func}\n\n'
                    f"#{entry_func}(\n"
                    f'  client-name: "{escape_typst_string(client_display)}",\n'
                    f'  contractor-name: "{escape_typst_string(contractor_display)}",\n'
                    f"{consultant_arg}"
                    f'  program-title: "{escape_typst_string(ast.get("program_title") or project.document_type)}",\n'
                    f'  report-title: "{escape_typst_string(ast.get("report_title") or project.title)}",\n'
                    f'  report-subtitle: "{escape_typst_string(ast.get("report_subtitle") or project.subtitle or "FINAL REPORT")}",\n'
                    f'  client-ref: "{escape_typst_string(doc_ref_client)}",\n'
                    f'  contractor-ref: "{escape_typst_string(doc_ref_contractor)}",\n'
                    f'  revision-number: "{escape_typst_string(project.revision_number or "Rev 01")}",\n'
                    f'  fao-text: "{escape_typst_string(project.fao_text or client_display)}",\n'
                    f"  client-logo: {_opt_str(c_logo_rel)},\n"
                    f"  contractor-logo: {_opt_str(g_logo_rel)},\n"
                    f"  partner-logo: {_opt_str(p_logo_rel)},\n"
                    f"  signature-img: {_opt_str(sig_rel)},\n"
                    f"  revision-rows: {rev_tuple_str},\n"
                    f"  auth-prepared: {_auth_dict(prep, 'Lead Geotechnical Engineer', 'Lead Geotechnical Engineer')},\n"
                    f"  auth-reviewed: {_auth_dict(revw, 'Principal Reviewer', 'Principal Geoscientist')},\n"
                    f"  auth-approved1: {_auth_dict(aprv1, 'Technical Director', 'Technical Director')},\n"
                    f"  auth-approved2: {_auth_dict(aprv2, 'Client Representative', 'Project Lead')},\n"
                    f"  body-content: [\n"
                    + "\n".join(body_parts)
                    + "\n  ]\n)\n"
                )

                main_typ_path = workdir / "main_report.typ"
                main_typ_path.write_text(main_typ, encoding="utf-8")
                base_pdf_bytes = typst.compile(str(main_typ_path))

            # Preserve 100% of Typst's clickable internal links & outline bookmarks via writer.append()
            attachments = sorted(
                project.attachments or [], key=lambda a: a.display_order
            )
            if not attachments:
                final_bytes = base_pdf_bytes
                total_pages = len(PdfReader(io.BytesIO(final_bytes)).pages)
            else:
                writer = PdfWriter()
                writer.append(io.BytesIO(base_pdf_bytes))
                for idx, att in enumerate(attachments, start=1):
                    att_path = self.storage.resolve_path(att.file_url)
                    att_label = f"{att.attachment_number or f'Attachment {idx}'}: {att.title}"
                    if att_path and att_path.exists():
                        try:
                            writer.append(str(att_path), outline_item=att_label)
                        except Exception:
                            pass
                out_buf = io.BytesIO()
                writer.write(out_buf)
                final_bytes = out_buf.getvalue()
                total_pages = len(PdfReader(io.BytesIO(final_bytes)).pages)

            safe_ref = re.sub(
                r"[^a-zA-Z0-9_-]+", "_", project.contractor_ref_code or project.id
            )
            url, _ = self.storage.save_bytes(
                "compiled-exports", f"{safe_ref}.pdf", final_bytes, deterministic=True
            )
            return url, total_pages
        except Exception as exc:
            raise CompilationError(
                f"Typst A4 PDF Typesetting Engine failed: {exc}"
            ) from exc
