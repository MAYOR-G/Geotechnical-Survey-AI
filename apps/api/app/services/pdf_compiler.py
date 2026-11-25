import io
from pathlib import Path
import re
from typing import Any
import pymupdf as fitz
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from app.core.exceptions import CompilationError
from app.models.project import Project
from app.services.storage_service import StorageService
from app.services.typst_compiler import TypstCompilerService


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "reports"


def strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</div>|</h[1-4]>|</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_blocks(html: str) -> list[tuple[str, str]]:
    """Parse section HTML into ordered ('h3'|'p', plain_text) blocks preserving inline headings."""
    tokens = re.findall(
        r"<h[2-4][^>]*>.*?</h[2-4]>|<p[^>]*>.*?</p>|<li[^>]*>.*?</li>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not tokens:
        plain = strip_html(html)
        return [("p", line.strip()) for line in plain.split("\n") if line.strip()]
    blocks: list[tuple[str, str]] = []
    for tok in tokens:
        tag = "h3" if tok.lower().startswith("<h") else "p"
        txt = strip_html(tok).replace("&amp;", "&").replace("&nbsp;", " ").strip()
        if txt:
            blocks.append((tag, txt))
    return blocks


def wrap_text_exact(
    text: str,
    max_width: float,
    fontname: str = "helv",
    fontsize: float = 9.0,
) -> list[str]:
    """Wrap text accurately using PyMuPDF font metrics so text never overflows or drops."""
    if not text:
        return []
    avail = max(max_width, fontsize * 1.5)
    out: list[str] = []
    for raw_para in str(text).split("\n"):
        para = raw_para.strip()
        if not para:
            out.append("")
            continue
        words = para.split(" ")
        cur = ""
        for word in words:
            candidate = f"{cur} {word}".strip() if cur else word
            if fitz.get_text_length(candidate, fontname=fontname, fontsize=fontsize) <= avail:
                cur = candidate
            else:
                if cur:
                    out.append(cur)
                    cur = ""
                # If single long token exceeds cell width, hyphenless hard-wrap at exact glyph fit
                if fitz.get_text_length(word, fontname=fontname, fontsize=fontsize) <= avail:
                    cur = word
                else:
                    chunk = ""
                    for ch in word:
                        test_c = chunk + ch
                        if fitz.get_text_length(test_c, fontname=fontname, fontsize=fontsize) <= avail:
                            chunk = test_c
                        else:
                            if chunk:
                                out.append(chunk)
                            chunk = ch
                    cur = chunk
        if cur:
            out.append(cur)
    return out


def draw_wrapped_lines(
    page: fitz.Page,
    rect: fitz.Rect,
    lines: list[str],
    fontname: str = "helv",
    fontsize: float = 9.0,
    color: tuple[float, float, float] = (0.1, 0.1, 0.12),
    align: str = "left",
    line_factor: float = 1.32,
) -> None:
    """Render pre-wrapped lines explicitly via insert_text so text is never dropped."""
    if not lines:
        return
    step = fontsize * line_factor
    start_y = rect.y0 + fontsize + 1.0
    for idx, line in enumerate(lines):
        if not line:
            continue
        ly = start_y + idx * step
        if ly > rect.y1 + 2.0:
            break
        if align == "center":
            w = fitz.get_text_length(line, fontname=fontname, fontsize=fontsize)
            lx = rect.x0 + max((rect.width - w) / 2.0, 0.0)
        else:
            lx = rect.x0
        page.insert_text((lx, ly), line, fontsize=fontsize, fontname=fontname, color=color)


class PdfCompilerService:
    """
    Compiles the canonical DocumentAst into a corporate A4 PDF report and merges
    appended external ProjectAttachment PDFs via pypdf.
    """

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()
        self.typst_compiler = TypstCompilerService(self.storage)
        self.jinja = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
        )

    def _resolve_logo_paths(
        self, project: Project
    ) -> tuple[Path | None, Path | None, Path | None]:
        logos = project.header_logos_json or []
        client_url = next(
            (l.get("url") for l in logos if l.get("role") == "client"),
            "",
        )
        contractor_url = next(
            (l.get("url") for l in logos if l.get("role") == "contractor"),
            "",
        )
        partner_url = next(
            (l.get("url") for l in logos if l.get("role") == "partner"),
            "",
        )
        return (
            self.storage.resolve_path(client_url) if client_url else None,
            self.storage.resolve_path(contractor_url) if contractor_url else None,
            self.storage.resolve_path(partner_url) if partner_url else None,
        )

    def _fit_image_box(
        self, img_path: Path, max_w: float, max_h: float
    ) -> tuple[float, float]:
        try:
            with fitz.open(str(img_path)) as img_doc:
                rect = img_doc[0].rect
                iw, ih = max(rect.width, 1.0), max(rect.height, 1.0)
        except Exception:
            return max_w, max_h
        scale = min(max_w / iw, max_h / ih)
        return iw * scale, ih * scale

    def _draw_cell_image(
        self, page: fitz.Page, box: fitz.Rect, img_path: Path | None
    ) -> bool:
        if (
            not img_path
            or not img_path.exists()
            or img_path.suffix.lower() not in (".png", ".jpg", ".jpeg")
        ):
            return False
        try:
            page.insert_image(box, filename=str(img_path), keep_proportion=True)
            return True
        except Exception:
            return False

    def compile_project_pdf(self, project: Project) -> tuple[str, int]:
        """Primary compilation path: native Typst A4 typesetting engine with pypdf attachment merging."""
        try:
            return self.typst_compiler.compile_project_pdf(project)
        except Exception as typst_exc:
            raise CompilationError(f"Failed to compile A4 PDF via Typst: {typst_exc}") from typst_exc

            # Extract PDF bookmarks before merging so pypdf preserves sidebar TOC
            with fitz.open(stream=base_pdf_bytes, filetype="pdf") as base_doc:
                base_toc = base_doc.get_toc()

            # Merge external ProjectAttachment PDFs sequentially using pypdf
            writer = PdfWriter()
            base_reader = PdfReader(io.BytesIO(base_pdf_bytes))
            for page in base_reader.pages:
                writer.add_page(page)

            for _lvl, lbl, pg_1based in base_toc:
                if 1 <= pg_1based <= len(base_reader.pages):
                    writer.add_outline_item(title=lbl, page_number=pg_1based - 1)

            attachments = sorted(
                project.attachments or [], key=lambda a: a.display_order
            )
            current_page_idx = len(base_reader.pages)
            for idx, att in enumerate(attachments, start=1):
                att_path = self.storage.resolve_path(att.file_url)
                att_label = f"{att.attachment_number or f'Attachment {idx}'}: {att.title}"
                if att_path and att_path.exists():
                    try:
                        att_reader = PdfReader(str(att_path))
                        for p in att_reader.pages:
                            writer.add_page(p)
                        writer.add_outline_item(title=att_label, page_number=current_page_idx)
                        current_page_idx += len(att_reader.pages)
                    except Exception:
                        divider = self._make_attachment_divider_pdf(att_label)
                        div_reader = PdfReader(io.BytesIO(divider))
                        for p in div_reader.pages:
                            writer.add_page(p)
                        writer.add_outline_item(title=att_label, page_number=current_page_idx)
                        current_page_idx += len(div_reader.pages)

            out_buf = io.BytesIO()
            writer.write(out_buf)
            final_bytes = out_buf.getvalue()
            total_pages = len(PdfReader(io.BytesIO(final_bytes)).pages)

            safe_ref = re.sub(
                r"[^a-zA-Z0-9_-]+", "_", project.contractor_ref_code or project.id
            )
            url, _ = self.storage.save_bytes(
                "compiled-exports", f"{safe_ref}.pdf", final_bytes
            )
            return url, total_pages
        except Exception as exc:
            raise CompilationError(f"Failed to compile A4 PDF package: {exc}") from exc

    def _render_vector_pdf(self, project: Project, ast: dict[str, Any]) -> bytes:
        doc = fitz.open()
        a4_w, a4_h = 595.0, 842.0
        margin_x = 34.0
        content_w = a4_w - 2 * margin_x
        bottom_limit = a4_h - 42.0
        client_logo, gems_logo, enviros_logo = self._resolve_logo_paths(project)

        def draw_logo_header_band(
            page: fitz.Page, y0: float, h: float = 46.0
        ) -> float:
            mid_x = margin_x + content_w * 0.48
            outer = fitz.Rect(margin_x, y0, a4_w - margin_x, y0 + h)
            page.draw_rect(outer, color=(0.12, 0.12, 0.14), width=0.8)
            page.draw_line(
                (mid_x, y0), (mid_x, y0 + h), color=(0.12, 0.12, 0.14), width=0.8
            )

            left_box = fitz.Rect(margin_x + 10, y0 + 5, mid_x - 10, y0 + h - 5)
            if not self._draw_cell_image(page, left_box, client_logo):
                page.insert_text(
                    (margin_x + 12, y0 + 26),
                    project.client_name[:28],
                    fontsize=9.5,
                    fontname="hebo",
                    color=(0.1, 0.4, 0.25),
                )

            right_w = (a4_w - margin_x) - mid_x
            gems_box = fitz.Rect(
                mid_x + 10, y0 + 6, mid_x + right_w * 0.47, y0 + h - 6
            )
            env_box = fitz.Rect(
                mid_x + right_w * 0.50, y0 + 8, a4_w - margin_x - 10, y0 + h - 8
            )
            self._draw_cell_image(page, gems_box, gems_logo)
            self._draw_cell_image(page, env_box, enviros_logo)
            return y0 + h

        def draw_running_header(page: fitz.Page, page_num: int) -> float:
            band_bottom = draw_logo_header_band(page, 22.0, 44.0)
            page.insert_text(
                (margin_x, a4_h - 22),
                f"{project.contractor_ref_code or project.id}",
                fontsize=7.8,
                fontname="helv",
                color=(0.42, 0.42, 0.45),
            )
            page.insert_text(
                (a4_w - margin_x - 36, a4_h - 22),
                f"Page {page_num}",
                fontsize=7.8,
                fontname="hebo",
                color=(0.25, 0.25, 0.28),
            )
            return band_bottom + 18.0

        def new_page(with_header: bool = True) -> tuple[fitz.Page, float]:
            page = doc.new_page(width=a4_w, height=a4_h)
            if with_header:
                y = draw_running_header(page, len(doc))
                return page, y
            return page, 24.0

        def draw_multi_header(
            pg: fitz.Page,
            cy: float,
            multi_header: list[list[dict[str, Any]]],
            col_count: int,
            col_widths: list[float],
            font_sz: float,
        ) -> float:
            row_h = 20.0
            n_rows = len(multi_header)
            occupied = [[False] * col_count for _ in range(n_rows)]
            x_offsets = [margin_x]
            for w in col_widths[:-1]:
                x_offsets.append(x_offsets[-1] + w)

            for r_idx, header_row in enumerate(multi_header):
                c_cursor = 0
                for cell in header_row:
                    while c_cursor < col_count and occupied[r_idx][c_cursor]:
                        c_cursor += 1
                    if c_cursor >= col_count:
                        break
                    colspan = int(cell.get("colspan") or 1)
                    rowspan = int(cell.get("rowspan") or 1)
                    for rr in range(r_idx, min(n_rows, r_idx + rowspan)):
                        for cc in range(c_cursor, min(col_count, c_cursor + colspan)):
                            occupied[rr][cc] = True
                    x0 = x_offsets[c_cursor]
                    end_col = min(c_cursor + colspan - 1, col_count - 1)
                    x1 = x_offsets[end_col] + col_widths[end_col]
                    y0 = cy + r_idx * row_h
                    y1 = y0 + rowspan * row_h
                    rect = fitz.Rect(x0, y0, x1, y1)
                    pg.draw_rect(
                        rect,
                        color=(0.18, 0.18, 0.2),
                        fill=(0.95, 0.95, 0.96),
                        width=0.6,
                    )
                    lbl = str(cell.get("label") or "")
                    wrapped = wrap_text_exact(
                        lbl, max(rect.width - 4.0, 10.0), "hebo", font_sz
                    )
                    line_step = font_sz * 1.28
                    tot_txt_h = len(wrapped) * line_step
                    top_off = max((rect.height - tot_txt_h) / 2.0, 2.0)
                    draw_wrapped_lines(
                        pg,
                        fitz.Rect(
                            rect.x0 + 2, rect.y0 + top_off, rect.x1 - 2, rect.y1 - 2
                        ),
                        wrapped,
                        fontname="hebo",
                        fontsize=font_sz,
                        align="center",
                        line_factor=1.28,
                    )
                    c_cursor += colspan
            return cy + n_rows * row_h

        def draw_table(
            page: fitz.Page,
            y: float,
            columns: list[str],
            rows: list[list[Any]],
            title: str = "",
            multi_header: list[list[dict[str, Any]]] | None = None,
            footnote: str | None = None,
            col_ratios: list[float] | None = None,
        ) -> tuple[fitz.Page, float]:
            if title:
                if y > bottom_limit - 70:
                    page, y = new_page()
                page.insert_text(
                    (margin_x, y),
                    title[:110],
                    fontsize=9.5,
                    fontname="hebo",
                    color=(0.1, 0.1, 0.12),
                )
                y += 10

            col_count = max(len(columns), 1)
            if col_ratios and len(col_ratios) == col_count:
                total_r = sum(col_ratios)
                col_widths = [content_w * (r / total_r) for r in col_ratios]
            elif col_count == 2:
                col_widths = [content_w * 0.24, content_w * 0.76]
            elif col_count == 3:
                col_widths = [content_w * 0.24, content_w * 0.44, content_w * 0.32]
            elif col_count == 4 and any("ACTIVITY" in c.upper() for c in columns):
                col_widths = [
                    content_w * 0.07,
                    content_w * 0.15,
                    content_w * 0.54,
                    content_w * 0.24,
                ]
            elif col_count == 4 and "Equipment" in columns:
                col_widths = [
                    content_w * 0.06,
                    content_w * 0.20,
                    content_w * 0.22,
                    content_w * 0.52,
                ]
            elif col_count == 6 and "Facility" in str(columns[1]):
                col_widths = [
                    content_w * 0.06,
                    content_w * 0.26,
                    content_w * 0.13,
                    content_w * 0.13,
                    content_w * 0.14,
                    content_w * 0.28,
                ]
            elif col_count == 15:
                # 527pt total: give Minna Easting/Northing 36pt+ and Lat/Long 44pt+ so numbers stay on 1 line
                raw = [
                    0.55,
                    2.25,
                    1.08,
                    1.08,
                    1.32,
                    1.32,
                    1.08,
                    1.08,
                    1.32,
                    1.32,
                    0.78,
                    0.78,
                    0.78,
                    0.78,
                    0.88,
                ]
                s_raw = sum(raw)
                col_widths = [content_w * (r / s_raw) for r in raw]
            else:
                col_widths = [content_w / col_count] * col_count

            font_sz = 5.0 if col_count > 8 else 8.2
            hdr_font_sz = 4.9 if col_count > 8 else 8.3
            pad_x = 2.0 if col_count > 8 else 4.5
            pad_y = 3.5

            def render_header(pg: fitz.Page, cy: float) -> float:
                if multi_header:
                    return draw_multi_header(
                        pg, cy, multi_header, col_count, col_widths, hdr_font_sz
                    )
                hdr_wrapped = [
                    wrap_text_exact(
                        str(c), max(col_widths[idx] - 2 * pad_x, 8.0), "hebo", hdr_font_sz
                    )
                    for idx, c in enumerate(columns)
                ]
                max_hdr_lines = max(max(len(w), 1) for w in hdr_wrapped)
                hdr_h = max(20.0, max_hdr_lines * (hdr_font_sz * 1.32) + pad_y * 2)
                cx = margin_x
                for idx in range(col_count):
                    cw = col_widths[idx]
                    r = fitz.Rect(cx, cy, cx + cw, cy + hdr_h)
                    pg.draw_rect(
                        r,
                        color=(0.18, 0.18, 0.2),
                        fill=(0.95, 0.95, 0.96),
                        width=0.6,
                    )
                    draw_wrapped_lines(
                        pg,
                        fitz.Rect(r.x0 + pad_x, r.y0 + pad_y, r.x1 - pad_x, r.y1 - 2),
                        hdr_wrapped[idx],
                        fontname="hebo",
                        fontsize=hdr_font_sz,
                    )
                    cx += cw
                return cy + hdr_h

            y = render_header(page, y)
            for row in rows:
                cell_lines: list[list[str]] = []
                max_lines = 1
                for c_idx in range(col_count):
                    val = str(row[c_idx]) if c_idx < len(row) else ""
                    wrapped = wrap_text_exact(
                        val, max(col_widths[c_idx] - 2 * pad_x, 8.0), "helv", font_sz
                    )
                    cell_lines.append(wrapped)
                    if len(wrapped) > max_lines:
                        max_lines = len(wrapped)
                row_h = max(17.5, max_lines * (font_sz * 1.32) + pad_y * 2)

                if y + row_h > bottom_limit:
                    page, y = new_page()
                    y = render_header(page, y)

                cx = margin_x
                for c_idx in range(col_count):
                    cw = col_widths[c_idx]
                    r = fitz.Rect(cx, y, cx + cw, y + row_h)
                    page.draw_rect(r, color=(0.35, 0.35, 0.38), width=0.5)
                    draw_wrapped_lines(
                        page,
                        fitz.Rect(r.x0 + pad_x, r.y0 + pad_y, r.x1 - pad_x, r.y1 - 2),
                        cell_lines[c_idx],
                        fontname="helv",
                        fontsize=font_sz,
                    )
                    cx += cw
                y += row_h

            if footnote:
                y += 4
                if y + 14 > bottom_limit:
                    page, y = new_page()
                page.insert_text(
                    (margin_x, y + 9),
                    footnote,
                    fontsize=8.0,
                    fontname="helv",
                    color=(0.25, 0.25, 0.28),
                )
                y += 14

            return page, y + 10

        def draw_figure(
            page: fitz.Page, y: float, ph: dict[str, Any]
        ) -> tuple[fitz.Page, float]:
            resolved_url = ph.get("resolved_url")
            secondary_url = ph.get("secondary_url")
            layout = ph.get("layout") or (
                "side_by_side" if secondary_url else "single"
            )
            caption = (
                ph.get("caption")
                or f"{ph.get('figure_number', 'Figure')}: {ph.get('prompt', '')}"
            )
            sec_caption = ph.get("secondary_caption")

            primary_path = (
                self.storage.resolve_path(resolved_url) if resolved_url else None
            )
            sec_path = (
                self.storage.resolve_path(secondary_url) if secondary_url else None
            )

            if (
                secondary_url
                and sec_path
                and sec_path.exists()
                and layout == "side_by_side"
            ):
                gap = 10.0
                each_w = (content_w - gap) / 2.0
                max_h = 265.0
                _, h1 = (
                    self._fit_image_box(primary_path, each_w, max_h)
                    if primary_path and primary_path.exists()
                    else (each_w, 180.0)
                )
                _, h2 = self._fit_image_box(sec_path, each_w, max_h)
                draw_h = max(h1, h2, 150.0)
                block_h = draw_h + 24.0
                if y + block_h > bottom_limit:
                    page, y = new_page()
                self._draw_cell_image(
                    page,
                    fitz.Rect(margin_x, y, margin_x + each_w, y + draw_h),
                    primary_path,
                )
                self._draw_cell_image(
                    page,
                    fitz.Rect(
                        margin_x + each_w + gap, y, margin_x + content_w, y + draw_h
                    ),
                    sec_path,
                )
                if sec_caption:
                    draw_wrapped_lines(
                        page,
                        fitz.Rect(
                            margin_x, y + draw_h + 4, margin_x + each_w, y + draw_h + 22
                        ),
                        [caption],
                        fontname="hebo",
                        fontsize=9.0,
                        align="center",
                    )
                    draw_wrapped_lines(
                        page,
                        fitz.Rect(
                            margin_x + each_w + gap,
                            y + draw_h + 4,
                            margin_x + content_w,
                            y + draw_h + 22,
                        ),
                        [sec_caption],
                        fontname="hebo",
                        fontsize=9.0,
                        align="center",
                    )
                else:
                    draw_wrapped_lines(
                        page,
                        fitz.Rect(
                            margin_x, y + draw_h + 4, a4_w - margin_x, y + draw_h + 22
                        ),
                        [caption],
                        fontname="hebo",
                        fontsize=9.0,
                        align="center",
                    )
                return page, y + block_h + 8

            if secondary_url and sec_path and sec_path.exists() and layout == "stacked":
                w1, ch1 = (
                    self._fit_image_box(primary_path, content_w, 185.0)
                    if primary_path and primary_path.exists()
                    else (content_w, 150.0)
                )
                w2, ch2 = self._fit_image_box(sec_path, content_w, 185.0)
                block_h = ch1 + ch2 + 30.0
                if y + block_h > bottom_limit:
                    page, y = new_page()
                if primary_path and primary_path.exists():
                    x0_1 = margin_x + (content_w - w1) / 2.0
                    self._draw_cell_image(
                        page, fitz.Rect(x0_1, y, x0_1 + w1, y + ch1), primary_path
                    )
                else:
                    ch1 = 0.0
                x0_2 = margin_x + (content_w - w2) / 2.0
                self._draw_cell_image(
                    page,
                    fitz.Rect(x0_2, y + ch1 + 6, x0_2 + w2, y + ch1 + 6 + ch2),
                    sec_path,
                )
                draw_wrapped_lines(
                    page,
                    fitz.Rect(
                        margin_x,
                        y + ch1 + ch2 + 10,
                        a4_w - margin_x,
                        y + ch1 + ch2 + 26,
                    ),
                    [caption],
                    fontname="hebo",
                    fontsize=9.0,
                    align="center",
                )
                return page, y + ch1 + ch2 + 34

            if primary_path and primary_path.exists():
                img_w, img_h = self._fit_image_box(primary_path, content_w, 280.0)
                block_h = img_h + 26.0
                if y + block_h > bottom_limit:
                    page, y = new_page()
                x0 = margin_x + (content_w - img_w) / 2.0
                self._draw_cell_image(
                    page, fitz.Rect(x0, y, x0 + img_w, y + img_h), primary_path
                )
                draw_wrapped_lines(
                    page,
                    fitz.Rect(
                        margin_x, y + img_h + 5, a4_w - margin_x, y + img_h + 23
                    ),
                    [caption],
                    fontname="hebo",
                    fontsize=9.0,
                    align="center",
                )
                return page, y + block_h + 8

            if y + 40 > bottom_limit:
                page, y = new_page()
            draw_wrapped_lines(
                page,
                fitz.Rect(margin_x, y, a4_w - margin_x, y + 24),
                [f"[{caption}]"],
                fontname="helv",
                fontsize=9.0,
                color=(0.45, 0.45, 0.48),
                align="center",
            )
            return page, y + 30

        # =========================================================================
        # PAGE 1: FULL CORPORATE BORDERED COVER PAGE (MATCHING REFERENCE PDF)
        # =========================================================================
        page, _ = new_page(with_header=False)
        top_y = 26.0
        bot_y = 810.0
        page.draw_rect(
            fitz.Rect(margin_x, top_y, a4_w - margin_x, bot_y),
            color=(0.1, 0.1, 0.12),
            width=0.9,
        )

        r1_bot = draw_logo_header_band(page, top_y, 52.0)

        r2_bot = r1_bot + 340.0
        page.draw_line(
            (margin_x, r2_bot), (a4_w - margin_x, r2_bot), color=(0.1, 0.1, 0.12), width=0.8
        )
        program = ast.get("program_title") or project.document_type or "Geotechnical Engineering Report"
        if program:
            draw_wrapped_lines(
                page,
                fitz.Rect(margin_x + 24, r1_bot + 72, a4_w - margin_x - 24, r1_bot + 108),
                [program],
                fontname="hebo",
                fontsize=17,
                align="center",
            )
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 24, r1_bot + 132, a4_w - margin_x - 24, r1_bot + 190),
            [project.title or "Geotechnical Survey Field Report"],
            fontname="hebo",
            fontsize=20,
            align="center",
        )
        subtitle_line = ast.get("report_subtitle") or project.subtitle or ""
        if subtitle_line:
            draw_wrapped_lines(
                page,
                fitz.Rect(margin_x + 24, r1_bot + 216, a4_w - margin_x - 24, r1_bot + 266),
                [subtitle_line],
                fontname="hebo",
                fontsize=16,
                align="center",
            )

        r3_bot = r2_bot + 54.0
        page.draw_line(
            (margin_x, r3_bot), (a4_w - margin_x, r3_bot), color=(0.1, 0.1, 0.12), width=0.8
        )
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 20, r2_bot + 18, a4_w - margin_x - 20, r3_bot - 10),
            [f"Revision: {project.revision_number}"],
            fontname="hebo",
            fontsize=12.5,
            align="center",
        )

        r4_bot = r3_bot + 62.0
        page.draw_line(
            (margin_x, r4_bot), (a4_w - margin_x, r4_bot), color=(0.1, 0.1, 0.12), width=0.8
        )
        client_label = project.client_name or "Client"
        contractor_label = project.contractor_name or "Contractor"
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 20, r3_bot + 14, a4_w - margin_x - 20, r3_bot + 34),
            [
                f"{client_label} Document Ref. {project.client_ref_code or 'Pending'}"
            ],
            fontname="hebo",
            fontsize=10.5,
            align="center",
        )
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 20, r3_bot + 34, a4_w - margin_x - 20, r4_bot - 8),
            [
                f"{contractor_label} Document Ref. {project.contractor_ref_code or 'Pending'}"
            ],
            fontname="hebo",
            fontsize=10.5,
            align="center",
        )

        r5_bot = r4_bot + 92.0
        page.draw_line(
            (margin_x, r5_bot), (a4_w - margin_x, r5_bot), color=(0.1, 0.1, 0.12), width=0.8
        )
        owner_name = project.contractor_name or "the Contractor"
        conf_text = (
            f"This document is proprietary and confidential. Copyright is vested in {owner_name}. All rights reserved. "
            "Neither the whole nor any part of this document may be disclosed to any third party nor reproduced, stored in any "
            "retrieval system, or transmitted in any form or by any means without the prior written consent of the copyright owner."
        )
        conf_lines = wrap_text_exact(conf_text, content_w - 24, "helv", 8.5)
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 12, r4_bot + 14, a4_w - margin_x - 12, r5_bot - 6),
            conf_lines,
            fontname="helv",
            fontsize=8.5,
            color=(0.15, 0.15, 0.18),
        )

        rev_grid_h = bot_y - r5_bot
        n_grid_rows = 6
        g_row_h = rev_grid_h / n_grid_rows
        rev_cols = [0.10, 0.14, 0.37, 0.13, 0.13, 0.13]
        col_x = [margin_x]
        for ratio in rev_cols[:-1]:
            col_x.append(col_x[-1] + content_w * ratio)
        col_x.append(a4_w - margin_x)

        for cx in col_x[1:-1]:
            page.draw_line((cx, r5_bot), (cx, bot_y), color=(0.1, 0.1, 0.12), width=0.7)
        for rr in range(1, n_grid_rows):
            ry = r5_bot + rr * g_row_h
            page.draw_line(
                (margin_x, ry), (a4_w - margin_x, ry), color=(0.1, 0.1, 0.12), width=0.7
            )

        revs = project.revision_history_json or []
        row_data_slots: list[tuple[int, list[str], bool]] = []
        if len(revs) >= 1:
            r0 = revs[0]
            row_data_slots.append(
                (
                    3,
                    [
                        r0.get("rev", ""),
                        r0.get("date", ""),
                        r0.get("description", ""),
                        r0.get("prepared_by", ""),
                        r0.get("checked_by", ""),
                        r0.get("approved_by", ""),
                    ],
                    False,
                )
            )
        if len(revs) >= 2:
            r1 = revs[1]
            row_data_slots.append(
                (
                    4,
                    [
                        r1.get("rev", ""),
                        r1.get("date", ""),
                        r1.get("description", ""),
                        r1.get("prepared_by", ""),
                        r1.get("checked_by", ""),
                        r1.get("approved_by", ""),
                    ],
                    False,
                )
            )
        row_data_slots.append(
            (
                5,
                ["Rev", "Date", "Reason for Revision", "Prepared", "Checked", "Approved"],
                True,
            )
        )

        for slot_idx, vals, is_hdr in row_data_slots:
            ry0 = r5_bot + slot_idx * g_row_h
            for c_i, val in enumerate(vals):
                draw_wrapped_lines(
                    page,
                    fitz.Rect(
                        col_x[c_i] + 3, ry0 + 4, col_x[c_i + 1] - 3, ry0 + g_row_h - 2
                    ),
                    [val],
                    fontname="hebo" if is_hdr else "helv",
                    fontsize=8.5,
                    align="center",
                )

        # =========================================================================
        # PAGE 2: DOCUMENT AUTHORISATION AND DISTRIBUTION + SIGNATURE MATRIX
        # =========================================================================
        page, y = new_page()
        page.insert_text(
            (margin_x, y),
            "DOCUMENT AUTHORISATION AND DISTRIBUTION",
            fontsize=11.0,
            fontname="hebo",
            color=(0.1, 0.1, 0.12),
        )
        y += 14

        auths = project.authorization_matrix_json or []
        prep = next((a for a in auths if "prepar" in a.get("role", "").lower()), {})
        revw = next((a for a in auths if "review" in a.get("role", "").lower()), {})
        aprv_list = [a for a in auths if "approv" in a.get("role", "").lower()]
        aprv1 = aprv_list[0] if len(aprv_list) > 0 else {}
        aprv2 = aprv_list[1] if len(aprv_list) > 1 else {}

        def draw_auth_row(
            pg: fitz.Page,
            cy: float,
            cells: list[tuple[float, str, bool]],
            min_h: float = 22.0,
            fill: tuple[float, float, float] | None = None,
            fontsize: float = 8.5,
        ) -> float:
            wrapped_cells = [
                wrap_text_exact(txt, max(cw - 10, 12.0), "hebo" if bold else "helv", fontsize)
                for cw, txt, bold in cells
            ]
            max_lines = max(max(len(wc), 1) for wc in wrapped_cells)
            h = max(min_h, max_lines * (fontsize * 1.35) + 10.0)
            cx = margin_x
            for idx, (cw, _txt, bold) in enumerate(cells):
                rect = fitz.Rect(cx, cy, cx + cw, cy + h)
                pg.draw_rect(rect, color=(0.15, 0.15, 0.18), fill=fill, width=0.6)
                draw_wrapped_lines(
                    pg,
                    fitz.Rect(cx + 5, cy + 4, cx + cw - 5, cy + h - 2),
                    wrapped_cells[idx],
                    fontname="hebo" if bold else "helv",
                    fontsize=fontsize,
                )
                cx += cw
            return cy + h

        c1_w = content_w * 0.24
        c2_w = content_w * 0.50
        c3_w = content_w * 0.26
        y = draw_auth_row(
            page,
            y,
            [(content_w, "Document Authorisation and Distribution", True)],
            min_h=24.0,
            fill=(0.95, 0.95, 0.96),
        )
        y = draw_auth_row(
            page, y, [(c1_w, "Contractor", True), (c2_w + c3_w, project.contractor_name, True)]
        )
        y = draw_auth_row(
            page, y, [(c1_w, "Client", True), (c2_w + c3_w, project.client_name, False)]
        )
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "FAO", True), (c2_w + c3_w, project.fao_text or "Pending", False)],
        )
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "Document Ref.", True), (c2_w + c3_w, project.contractor_ref_code or "", False)],
        )
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "Title", True), (c2_w + c3_w, f"{project.title}{(' - ' + project.subtitle) if project.subtitle else ''}", False)],
        )
        prep_line = ", ".join(x for x in (prep.get("name", ""), prep.get("email", "")) if x) or "Pending"
        revw_line = "; ".join(x for x in (revw.get("name", ""), revw.get("email", "")) if x) or "Pending"
        aprv_line = "; ".join(x for x in (aprv1.get("name", ""), aprv1.get("email", "")) if x) or "Pending"
        y = draw_auth_row(
            page,
            y,
            [
                (c1_w, "Author", True),
                (c2_w, prep_line, False),
                (c3_w, f"Date: {prep.get('date') or 'Pending'}", False),
            ],
        )
        y = draw_auth_row(
            page,
            y,
            [
                (c1_w, "Checked", True),
                (c2_w, revw_line, False),
                (c3_w, f"Date: {revw.get('date') or 'Pending'}", False),
            ],
        )
        y = draw_auth_row(
            page,
            y,
            [
                (c1_w, "Approved", True),
                (c2_w, aprv_line, False),
                (c3_w, f"Date: {aprv1.get('date') or 'Pending'}", False),
            ],
        )
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "", True), (content_w * 0.28, "DOCUMENT", True), (content_w * 0.48, "ISSUED TO", True)],
            min_h=22.0,
            fill=(0.95, 0.95, 0.96),
        )

        ac_top = y
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "", False), (content_w * 0.28, "Original", False), (content_w * 0.48, project.client_name or "Client", False)],
            min_h=22.0,
        )
        y = draw_auth_row(
            page,
            y,
            [(c1_w, "", False), (content_w * 0.28, "Copy No. 1", False), (content_w * 0.48, project.contractor_name or "Contractor", False)],
            min_h=22.0,
        )
        page.draw_rect(
            fitz.Rect(margin_x, ac_top, margin_x + c1_w, y),
            color=(0.15, 0.15, 0.18),
            fill=(1, 1, 1),
            width=0.6,
        )
        draw_wrapped_lines(
            page,
            fitz.Rect(margin_x + 5, ac_top + 14, margin_x + c1_w - 5, y - 4),
            ["Authorised Copies"],
            fontname="hebo",
            fontsize=8.5,
        )

        y += 20.0
        page.insert_text(
            (margin_x, y),
            "This document has been approved and authorised by the authorities whose signatures appear below:",
            fontsize=8.8,
            fontname="helv",
            color=(0.1, 0.1, 0.12),
        )
        y += 14.0

        sig_cols = [
            content_w * 0.16,
            content_w * 0.21,
            content_w * 0.21,
            content_w * 0.21,
            content_w * 0.21,
        ]
        y = draw_auth_row(
            page,
            y,
            [
                (sig_cols[0], "", True),
                (sig_cols[1], "Prepared By", True),
                (sig_cols[2], "Reviewed By", True),
                (sig_cols[3], "Approved By", True),
                (sig_cols[4], "Approved By", True),
            ],
            min_h=24.0,
            fill=(0.95, 0.95, 0.96),
        )

        sig_y0 = y
        y = draw_auth_row(
            page,
            y,
            [
                (sig_cols[0], "Signature", True),
                (sig_cols[1], "", False),
                (sig_cols[2], "", False),
                (sig_cols[3], "", False),
                (sig_cols[4], "", False),
            ],
            min_h=48.0,
        )
        sig_url = prep.get("signature_url") or ""
        sig_path = self.storage.resolve_path(sig_url)
        if sig_path and sig_path.exists():
            self._draw_cell_image(
                page,
                fitz.Rect(
                    margin_x + sig_cols[0] + 6,
                    sig_y0 + 4,
                    margin_x + sig_cols[0] + sig_cols[1] - 6,
                    y - 4,
                ),
                sig_path,
            )

        y = draw_auth_row(
            page,
            y,
            [
                (sig_cols[0], "Name", True),
                (sig_cols[1], prep.get("name", ""), False),
                (sig_cols[2], revw.get("name", ""), False),
                (sig_cols[3], aprv1.get("name", ""), False),
                (sig_cols[4], aprv2.get("name", ""), False),
            ],
            min_h=24.0,
        )
        y = draw_auth_row(
            page,
            y,
            [
                (sig_cols[0], "Designation", True),
                (sig_cols[1], prep.get("designation", ""), False),
                (sig_cols[2], revw.get("designation", ""), False),
                (sig_cols[3], aprv1.get("designation", ""), False),
                (sig_cols[4], aprv2.get("designation", ""), False),
            ],
            min_h=34.0,
        )
        y = draw_auth_row(
            page,
            y,
            [
                (sig_cols[0], "Date", True),
                (sig_cols[1], prep.get("date", ""), False),
                (sig_cols[2], revw.get("date", ""), False),
                (sig_cols[3], aprv1.get("date", ""), False),
                (sig_cols[4], aprv2.get("date", ""), False),
            ],
            min_h=24.0,
        )

        # =========================================================================
        # PAGE 3: RESERVE CLICKABLE TOC PAGE (POPULATED AFTER BODY LAYOUT FOR EXACT PAGES)
        # =========================================================================
        toc_page, toc_start_y = new_page()
        toc_page_idx = len(doc) - 1

        toc_destinations: list[tuple[int, str, int, float]] = []
        fig_destinations: list[tuple[str, int, float]] = []
        tbl_destinations: list[tuple[str, int, float]] = []
        app_destinations: list[tuple[str, int, float]] = []

        # =========================================================================
        # PAGE 4+: ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS
        # =========================================================================
        abbrs = ast.get("abbreviations", [])
        if abbrs:
            page, y = new_page()
            toc_destinations.append(
                (1, "ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS", page.number, y)
            )
            page.insert_text(
                (margin_x, y),
                "ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS",
                fontsize=11.0,
                fontname="hebo",
                color=(0.1, 0.1, 0.12),
            )
            y += 15
            page.insert_text(
                (margin_x, y),
                "A list of abbreviations that have been used within the main body of the report as follows:",
                fontsize=9.2,
                fontname="helv",
                color=(0.15, 0.15, 0.18),
            )
            y += 12
            page, y = draw_table(
                page,
                y,
                ["Acronym", "Definition"],
                [[a.get("term", ""), a.get("definition", "")] for a in abbrs],
                col_ratios=[0.28, 0.72],
            )

        # =========================================================================
        # REPORT SECTIONS (PAGES 5+)
        # =========================================================================
        for sec in ast.get("sections", []):
            page, y = new_page()
            sec_heading = f"{sec.get('section_number', '')}  {sec.get('title', '')}".strip()
            toc_destinations.append((1, sec_heading, page.number, y))
            if sec.get("category") == "Appendices":
                app_destinations.append(("Appendix - A : Field Pictures", page.number, y))

            page.insert_text(
                (margin_x, y),
                sec_heading,
                fontsize=12.0,
                fontname="hebo",
                color=(0.1, 0.1, 0.12),
            )
            page.draw_line(
                (margin_x, y + 5),
                (a4_w - margin_x, y + 5),
                color=(0.12, 0.12, 0.14),
                width=0.9,
            )
            y += 18

            for kind, text_block in html_to_blocks(sec.get("html_content", "")):
                if kind == "h3":
                    if y + 26 > bottom_limit:
                        page, y = new_page()
                    page.insert_text(
                        (margin_x, y + 4),
                        text_block,
                        fontsize=10.2,
                        fontname="hebo",
                        color=(0.1, 0.1, 0.12),
                    )
                    y += 18
                else:
                    lines = wrap_text_exact(text_block, content_w, "helv", 9.5)
                    box_h = len(lines) * 13.0 + 6.0
                    if y + box_h > bottom_limit:
                        page, y = new_page()
                    draw_wrapped_lines(
                        page,
                        fitz.Rect(margin_x, y, a4_w - margin_x, y + box_h),
                        lines,
                        fontname="helv",
                        fontsize=9.5,
                        color=(0.12, 0.12, 0.14),
                        line_factor=1.35,
                    )
                    y += box_h + 4

            for tbl in sec.get("tables") or []:
                if y > bottom_limit - 70:
                    page, y = new_page()
                tbl_title = f"{tbl.get('table_number') or 'Table'}: {tbl.get('title', '')}"
                tbl_destinations.append((tbl_title, page.number, y))
                page, y = draw_table(
                    page,
                    y,
                    tbl.get("columns", []),
                    tbl.get("rows", []),
                    title=tbl_title,
                    multi_header=tbl.get("multi_header"),
                    footnote=tbl.get("footnote"),
                )

            for ph in sec.get("placeholders") or []:
                fig_num = str(ph.get("figure_number", ""))
                cap = ph.get("caption") or f"{fig_num}: {ph.get('prompt', '')}"
                pre_pg, pre_y = page.number, y
                page, y = draw_figure(page, y, ph)
                if fig_num.startswith("Figure"):
                    # If draw_figure paginated to a new page, destination starts near top of ending page
                    dest_pg = page.number if page.number > pre_pg else pre_pg
                    dest_y = toc_start_y if page.number > pre_pg else pre_y
                    fig_destinations.append((cap, dest_pg, dest_y))

        # =========================================================================
        # POPULATE PAGE 3: CLICKABLE TOC, FIGURES, TABLES, APPENDICES + PDF BOOKMARKS
        # =========================================================================
        toc_pg = doc[toc_page_idx]
        ty = toc_start_y

        def render_toc_row(label: str, dest_pg_idx: int, dest_y: float, bold: bool = False) -> None:
            nonlocal ty
            if ty > bottom_limit - 12:
                return
            fontn = "hebo" if bold else "helv"
            fsize = 9.0
            clean_lbl = label[:84]
            pg_str = str(dest_pg_idx + 1)
            lw = fitz.get_text_length(clean_lbl, fontname=fontn, fontsize=fsize)
            pw = fitz.get_text_length(pg_str, fontname="helv", fontsize=fsize)

            toc_pg.insert_text((margin_x, ty), clean_lbl, fontsize=fsize, fontname=fontn, color=(0.1, 0.1, 0.12))
            leader_x0 = margin_x + lw + 6.0
            leader_x1 = a4_w - margin_x - pw - 6.0
            if leader_x1 > leader_x0 + 8.0:
                toc_pg.draw_line(
                    (leader_x0, ty - 1.5),
                    (leader_x1, ty - 1.5),
                    color=(0.65, 0.65, 0.70),
                    width=0.6,
                    dashes="[1 2]",
                )
            toc_pg.insert_text(
                (a4_w - margin_x - pw, ty),
                pg_str,
                fontsize=fsize,
                fontname="helv",
                color=(0.1, 0.1, 0.12),
            )
            toc_pg.insert_link(
                {
                    "kind": fitz.LINK_GOTO,
                    "from": fitz.Rect(margin_x, ty - 9.0, a4_w - margin_x, ty + 3.0),
                    "page": dest_pg_idx,
                    "to": fitz.Point(margin_x, max(dest_y - 12.0, 20.0)),
                }
            )
            ty += 14.0

        toc_pg.insert_text((margin_x, ty), "TABLE OF CONTENTS", fontsize=11.0, fontname="hebo", color=(0.1, 0.1, 0.12))
        ty += 15.0
        for _lvl, lbl, dest_pg, dest_y in toc_destinations:
            render_toc_row(lbl, dest_pg, dest_y, bold=True)

        if fig_destinations and ty < bottom_limit - 36:
            ty += 10.0
            toc_pg.insert_text((margin_x, ty), "LIST OF FIGURES", fontsize=11.0, fontname="hebo", color=(0.1, 0.1, 0.12))
            ty += 15.0
            for lbl, dest_pg, dest_y in fig_destinations:
                render_toc_row(lbl, dest_pg, dest_y)

        if tbl_destinations and ty < bottom_limit - 36:
            ty += 10.0
            toc_pg.insert_text((margin_x, ty), "LIST OF TABLES", fontsize=11.0, fontname="hebo", color=(0.1, 0.1, 0.12))
            ty += 15.0
            for lbl, dest_pg, dest_y in tbl_destinations:
                render_toc_row(lbl, dest_pg, dest_y)

        if app_destinations and ty < bottom_limit - 24:
            ty += 10.0
            toc_pg.insert_text((margin_x, ty), "LIST OF APPENDICES", fontsize=11.0, fontname="hebo", color=(0.1, 0.1, 0.12))
            ty += 15.0
            for lbl, dest_pg, dest_y in app_destinations:
                render_toc_row(lbl, dest_pg, dest_y)

        # Attach PDF Sidebar Bookmarks
        pdf_bookmarks: list[list[Any]] = [
            [1, "Cover", 1],
            [1, "Document Authorisation & Distribution", 2],
            [1, "Table of Contents", toc_page_idx + 1],
        ]
        for _lvl, lbl, dest_pg, _dy in toc_destinations:
            pdf_bookmarks.append([1, lbl, dest_pg + 1])
        doc.set_toc(pdf_bookmarks)

        return doc.tobytes()

    def _make_attachment_divider_pdf(self, title: str) -> bytes:
        doc = fitz.open()
        page = doc.new_page(width=595.0, height=842.0)
        lines = wrap_text_exact(title, 490.0, "hebo", 18.0)
        draw_wrapped_lines(
            page,
            fitz.Rect(48, 360, 547, 460),
            lines,
            fontname="hebo",
            fontsize=18,
            align="center",
        )
        return doc.tobytes()
