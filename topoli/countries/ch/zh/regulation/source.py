"""Fetch the consolidated BZO 2016 text of the City of Zürich.

Source: the cantonal ÖREB document server publishes the consolidated ordinance the zoning layer
itself references (``dokument`` attribute lists ``docid=6``):
``GET https://oerebdocs.zh.ch/getDoc?docid=6`` → PDF "700.100 Bauordnung der Stadt Zürich,
Bau- und Zonenordnung (BZO 2016), Gemeinderatsbeschluss vom 23. Oktober 1991 mit Änderungen bis
<date>" (56 pages, text layer, read 2026-09-08). The same document is the official AS 700.100.

Official publications are not copyright-protected in Switzerland (Art. 5 URG), so a local cache
of the extracted text is lawful; Topoli still fetches on demand and only commits the *generated*
rule table (``generated/zones.yaml``), never the ordinance.

The cached payload is ``{"text", "pages", "sha256", "version_line"}``; ``version_line`` is the
"mit Änderungen bis …" line, used as the consolidation date of the regulation.
"""

from __future__ import annotations

import hashlib
import io
import re
from datetime import timedelta
from typing import Any

from pypdf import PdfReader

from topoli.core.adapters import Record, get_client

BZO_URL = "https://oerebdocs.zh.ch/getDoc"
BZO_DOCID = 6
BZO_TTL = timedelta(days=30)


def extract_text(data: bytes) -> dict[str, Any]:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    m = re.search(r"mit Änderungen bis\s+(\d{1,2}\.\s*\w+\s+\d{4})", text)
    return {
        "text": text,
        "pages": len(pages),
        "sha256": hashlib.sha256(data).hexdigest(),
        "version_line": m.group(0) if m else "",
    }


def fetch_bzo(adapter_id: str) -> Record:
    return get_client().get_bytes(
        adapter_id, BZO_URL, {"docid": BZO_DOCID}, wrap=extract_text, ttl=BZO_TTL
    )


def bzo_text(record: Record) -> str:
    payload = record.payload
    return str(payload.get("text", "")) if isinstance(payload, dict) else ""


def bzo_version(record: Record) -> str:
    payload = record.payload
    return str(payload.get("version_line", "")) if isinstance(payload, dict) else ""
