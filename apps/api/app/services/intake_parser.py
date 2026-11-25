import io
from pathlib import Path
import re
from typing import Any
import docx
import pandas as pd
import pymupdf as fitz
from app.core.exceptions import FileParseError


class IntakeParserService:
    """
    Deterministic parser for raw engineering spreadsheets (.xlsx/.csv) and field logs (.docx/.pdf/.txt).
    Reads tabular values with dtype=str so decimal precision (e.g., 389949.9720) is never rounded.
    """

    def parse_file(self, filename: str, content: bytes) -> dict[str, Any]:
        ext = Path(filename).suffix.lower()
        if ext in (".csv", ".tsv"):
            return self._parse_csv(filename, content)
        if ext in (".xlsx", ".xls"):
            return self._parse_excel(filename, content)
        if ext == ".docx":
            return self._parse_docx(filename, content)
        if ext == ".pdf":
            return self._parse_pdf(filename, content)
        if ext in (".txt", ".md", ".log"):
            text = content.decode("utf-8", errors="replace")
            return self._parse_text(filename, text)
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            return {
                "kind": "image",
                "filename": filename,
                "tables": [],
                "raw_text": f"Uploaded field photograph: {filename}",
                "extracted_metrics": {},
            }
        raise FileParseError(f"Unsupported intake file type '{ext}' for {filename}.")

    def _dataframe_to_table(self, name: str, df: pd.DataFrame) -> dict[str, Any]:
        df = df.dropna(how="all").fillna("")
        columns = [str(c).strip() for c in df.columns]
        rows = [[str(cell).strip() for cell in row] for row in df.values.tolist()]
        kind = "generic_table"
        joined_cols = " ".join(columns).lower()
        if any(k in joined_cols for k in ("easting", "northing", "wgs84", "lat", "long", "chainage")):
            kind = "coordinate_table"
        elif any(k in joined_cols for k in ("depth", "mbsf", "soil", "lithology", "strata", "cu", "cpt", "moisture")):
            kind = "borehole_profile"
        return {
            "id": f"tbl-{abs(hash(name)) % 100000}",
            "title": name,
            "kind": kind,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

    def _extract_metrics_from_tables_and_text(
        self, tables: list[dict[str, Any]], raw_text: str
    ) -> dict[str, Any]:
        metrics: dict[str, Any] = {
            "locations": [],
            "coordinates": [],
            "water_depths": [],
            "penetrations": [],
            "dates": re.findall(r"\b\d{2}/\d{2}/\d{4}\b", raw_text)[:12],
            "vessel_mentions": [],
        }

        for tbl in tables:
            cols = [c.lower() for c in tbl.get("columns", [])]
            for row in tbl.get("rows", []):
                for idx, val in enumerate(row):
                    if not val:
                        continue
                    col = cols[idx] if idx < len(cols) else ""
                    if any(k in col for k in ("location", "bh", "station", "borehole", "cpt")):
                        if val not in metrics["locations"]:
                            metrics["locations"].append(val)
                    if any(k in col for k in ("easting", "northing", "latitude", "longitude")):
                        if val not in metrics["coordinates"] and len(metrics["coordinates"]) < 40:
                            metrics["coordinates"].append(val)
                    if "water" in col and ("depth" in col or "height" in col):
                        if val not in metrics["water_depths"]:
                            metrics["water_depths"].append(val)
                    if any(k in col for k in ("penetration", "depth", "terminal", "mbsf", "refusal")):
                        if val not in metrics["penetrations"]:
                            metrics["penetrations"].append(val)

        for match in re.findall(r"\b(?:MV|M/V|R/V|DP-2)\s+[A-Z][A-Za-z0-9\s-]{2,28}", raw_text):
            cleaned_vessel = " ".join(match.split())
            if cleaned_vessel not in metrics["vessel_mentions"]:
                metrics["vessel_mentions"].append(cleaned_vessel)

        return metrics

    def _parse_csv(self, filename: str, content: bytes) -> dict[str, Any]:
        try:
            sep = "\t" if filename.lower().endswith(".tsv") else ","
            df = pd.read_csv(
                io.BytesIO(content),
                sep=sep,
                dtype=str,
                keep_default_na=False,
            )
        except Exception as exc:
            raise FileParseError(
                f"Could not parse '{filename}'. Please ensure it is a valid UTF-8 CSV file."
            ) from exc

        table = self._dataframe_to_table(Path(filename).stem.replace("_", " ").title(), df)
        raw_text = df.to_csv(index=False)
        return {
            "kind": table["kind"],
            "filename": filename,
            "tables": [table],
            "raw_text": raw_text,
            "extracted_metrics": self._extract_metrics_from_tables_and_text([table], raw_text),
        }

    def _parse_excel(self, filename: str, content: bytes) -> dict[str, Any]:
        try:
            sheets = pd.read_excel(
                io.BytesIO(content),
                sheet_name=None,
                dtype=str,
                keep_default_na=False,
                engine="openpyxl",
            )
        except Exception as exc:
            raise FileParseError(
                f"Could not parse '{filename}'. Ensure the workbook is not password-protected or corrupted."
            ) from exc

        tables: list[dict[str, Any]] = []
        raw_parts: list[str] = []
        for sheet_name, df in sheets.items():
            if df.empty:
                continue
            tbl = self._dataframe_to_table(f"{Path(filename).stem} — {sheet_name}", df)
            tables.append(tbl)
            raw_parts.append(f"## Sheet: {sheet_name}\n{df.to_csv(index=False)}")

        raw_text = "\n\n".join(raw_parts)
        return {
            "kind": tables[0]["kind"] if tables else "spreadsheet",
            "filename": filename,
            "tables": tables,
            "raw_text": raw_text,
            "extracted_metrics": self._extract_metrics_from_tables_and_text(tables, raw_text),
        }

    def _parse_docx(self, filename: str, content: bytes) -> dict[str, Any]:
        try:
            doc = docx.Document(io.BytesIO(content))
        except Exception as exc:
            raise FileParseError(f"Could not read Word document '{filename}'.") from exc

        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        tables: list[dict[str, Any]] = []
        for idx, t in enumerate(doc.tables):
            rows_raw = [[cell.text.strip() for cell in row.cells] for row in t.rows]
            if len(rows_raw) >= 2:
                joined_hdr = " ".join(rows_raw[0]).lower()
                kind = (
                    "coordinate_table"
                    if any(k in joined_hdr for k in ("easting", "northing", "wgs84", "chainage"))
                    else "borehole_profile"
                    if any(k in joined_hdr for k in ("depth", "strata", "lithology", "moisture"))
                    else "generic_table"
                )
                tables.append(
                    {
                        "id": f"docx-tbl-{idx + 1}",
                        "title": f"{Path(filename).stem} — Table {idx + 1}",
                        "kind": kind,
                        "columns": rows_raw[0],
                        "rows": rows_raw[1:],
                        "row_count": len(rows_raw) - 1,
                    }
                )
        raw_text = "\n".join(paragraphs)
        return {
            "kind": "field_notes",
            "filename": filename,
            "tables": tables,
            "raw_text": raw_text,
            "extracted_metrics": self._extract_metrics_from_tables_and_text(tables, raw_text),
        }

    def _parse_pdf(self, filename: str, content: bytes) -> dict[str, Any]:
        try:
            pdf = fitz.open(stream=content, filetype="pdf")
            pages = [page.get_text("text") for page in pdf]
            tables: list[dict[str, Any]] = []
            for p_idx, page in enumerate(pdf, start=1):
                try:
                    found = page.find_tables()
                    for t_idx, tab in enumerate(found.tables, start=1):
                        extracted = tab.extract()
                        clean_rows = [
                            [str(c or "").strip() for c in r]
                            for r in extracted
                            if any(str(c or "").strip() for c in r)
                        ]
                        if len(clean_rows) >= 2 and len(clean_rows[0]) >= 2:
                            tables.append(
                                {
                                    "id": f"pdf-tbl-{p_idx}-{t_idx}",
                                    "title": f"{Path(filename).stem} (Page {p_idx} Table {t_idx})",
                                    "kind": "generic_table",
                                    "columns": clean_rows[0],
                                    "rows": clean_rows[1:],
                                    "row_count": len(clean_rows) - 1,
                                }
                            )
                except Exception:
                    continue
        except Exception as exc:
            raise FileParseError(f"Could not extract text from PDF '{filename}'.") from exc
        raw_text = "\n\n".join(pages).strip()
        return {
            "kind": "pdf_notes",
            "filename": filename,
            "tables": tables,
            "raw_text": raw_text,
            "extracted_metrics": self._extract_metrics_from_tables_and_text(tables, raw_text),
        }

    def _parse_text(self, filename: str, text: str) -> dict[str, Any]:
        return {
            "kind": "daily_log",
            "filename": filename,
            "tables": [],
            "raw_text": text,
            "extracted_metrics": self._extract_metrics_from_tables_and_text([], text),
        }
