from __future__ import annotations

import hashlib
import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ElementTree

from app.domain.models import ParsedDocument
from app.ports.storage import StoragePort

HEADING_RE = re.compile(
    r"^(?:#{1,6}\s*)?(SUMMARY|EXPERIENCE|EDUCATION|SKILLS|LINKS|CONTACT)\s*:?\s*$", re.I
)
MAX_CHARS = 4000
MAX_CHUNKS = 200


def split_chunks(text: str) -> list[str]:
    """Split normalized text into bounded chunks on headings and blank lines."""
    chunks: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        joined = "\n".join(line for line in buffer if line).strip()
        buffer.clear()
        if not joined:
            return
        for start in range(0, len(joined), MAX_CHARS):
            chunks.append(joined[start : start + MAX_CHARS])

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if HEADING_RE.match(line):
            flush()
            chunks.append(line)
        elif not line:
            flush()
        else:
            buffer.append(line)
    flush()
    return chunks[:MAX_CHUNKS]


def _decode(raw_bytes: bytes) -> str:
    return re.sub(r"\n{3,}", "\n\n", raw_bytes.decode("utf-8", errors="replace")).strip()


def _pdf_text(raw_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        return _decode("\n".join(page.extract_text() or "" for page in reader.pages))
    except Exception:
        return ""


def _docx_text(raw_bytes: bytes) -> str:
    try:
        import docx

        document = docx.Document(io.BytesIO(raw_bytes))
        return _decode("\n".join(paragraph.text for paragraph in document.paragraphs))
    except Exception:
        pass
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        return _decode("\n".join(node.text or "" for node in root.iter(namespace + "t")))
    except Exception:
        return ""


class DocumentParser:
    """Extracts normalized text, stores the original, and computes its SHA-256."""

    def __init__(self, storage: StoragePort) -> None:
        self._storage = storage

    def parse(
        self, filename: str, raw_bytes: bytes, *, tenant_id: str = ""
    ) -> ParsedDocument:
        suffix = Path(filename).suffix.lower()
        file_hash = hashlib.sha256(raw_bytes).hexdigest()
        if suffix == ".pdf":
            text = _pdf_text(raw_bytes)
        elif suffix == ".docx":
            text = _docx_text(raw_bytes)
        else:
            text = _decode(raw_bytes)
        chunks = split_chunks(text)
        storage_key = f"resumes/{tenant_id or 'global'}/{file_hash}{suffix}"
        self._storage.put(storage_key, raw_bytes)
        return ParsedDocument(
            filename=filename,
            file_hash=file_hash,
            storage_key=storage_key,
            text=text,
            chunks=chunks,
        )
