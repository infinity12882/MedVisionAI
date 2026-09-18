from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_article_text(file_path: str, file_type: str) -> str:
    path = Path(file_path)

    if file_type == "pdf":
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    if file_type == "docx":
        import docx

        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs)

    # markdown / text
    return path.read_text(encoding="utf-8", errors="ignore")
