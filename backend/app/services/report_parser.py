import csv
import io
import re
from pathlib import Path

from PyPDF2 import PdfReader

from app.exceptions import InvalidFileError


class ReportParser:
    """Extracts text content from uploaded financial report files."""

    def extract_text(self, file_path: str, file_type: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise InvalidFileError(f"File not found at {file_path}")

        file_type = file_type.lower()
        if file_type == "pdf":
            return self._extract_pdf(path)
        if file_type == "txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        if file_type == "csv":
            return self._extract_csv(path)
        if file_type in {"xlsx", "xls", "docx"}:
            return self._extract_placeholder(path, file_type)

        raise InvalidFileError(f"Unsupported file type for parsing: {file_type}")

    def _extract_pdf(self, path: Path) -> str:
        try:
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if not text:
                raise InvalidFileError("Could not extract text from PDF. The file may be scanned or empty.")
            return text
        except InvalidFileError:
            raise
        except Exception as exc:
            raise InvalidFileError(f"Failed to parse PDF: {exc}") from exc

    def _extract_csv(self, path: Path) -> str:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(raw))
            rows = [", ".join(row) for row in reader]
            return "\n".join(rows)
        except Exception as exc:
            raise InvalidFileError(f"Failed to parse CSV: {exc}") from exc

    def _extract_placeholder(self, path: Path, file_type: str) -> str:
        # Placeholder: full parsing for xlsx/docx requires additional libraries.
        # Return filename hint so analysis can still proceed with limited context.
        return (
            f"[Placeholder extraction for .{file_type} file: {path.name}]\n"
            "Install openpyxl/python-docx for full text extraction. "
            "Analysis will use available metadata and heuristic patterns."
        )

    def extract_financial_figures(self, text: str) -> dict[str, str | None]:
        """Heuristic extraction of financial figures from report text."""
        patterns = {
            "revenue": r"(?:total\s+)?revenue[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            "expenses": r"(?:total\s+)?expenses?[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            "profit_loss": r"(?:net\s+)?(?:profit|loss|income)[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            "cash_flow": r"(?:net\s+)?cash\s+flow[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            "assets": r"(?:total\s+)?assets[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            "liabilities": r"(?:total\s+)?liabilities[:\s]*\$?([\d,]+(?:\.\d{2})?)",
        }
        results: dict[str, str | None] = {}
        lower_text = text.lower()
        for key, pattern in patterns.items():
            match = re.search(pattern, lower_text, re.IGNORECASE)
            results[key] = f"${match.group(1)}" if match else None
        return results
