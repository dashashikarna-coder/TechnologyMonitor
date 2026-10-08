"""Госзакупки Канады: открытые данные CanadaBuys (CSV-выгрузки, без ключа)."""
import csv
import io
import re
from datetime import date

from ..http import request, session

BASE = "https://canadabuys.canada.ca/opendata/pub/"


def _files() -> list[str]:
    y = date.today().year
    years = [f"{y}-{y + 1}", f"{y - 1}-{y}", f"{y - 2}-{y - 1}"]
    return ["openTenderNotice-ouvertAvisAppelOffres.csv"] + [f"{p}-TenderNotice-AvisAppelOffres.csv" for p in years]


def collect(queries: list[tuple[str, str]], log=print) -> list[dict]:
    """Скачивает выгрузки и оставляет закупки, в названии которых есть английское ключевое слово темы."""
    s = session()
    words = [(t, re.compile(rf"(?<!\w){re.escape(q.lower())}(?!\w)")) for t, q in queries]
    docs, seen = [], set()
    for name in _files():
        try:
            r = request(s, "GET", BASE + name, timeout=180)
            if r.status_code != 200:
                continue
            rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig", "replace"))))
        except Exception as e:
            log(f"  Канада {name}: ОШИБКА {type(e).__name__}")
            continue
        found = 0
        for row in rows:
            ref = row.get("referenceNumber-numeroReference") or ""
            title = (row.get("title-titre-eng") or "").strip()
            low = title.lower()
            topic = next((t for t, w in words if w.search(low)), None)
            if not topic or not ref or ref in seen:
                continue
            seen.add(ref)
            found += 1
            docs.append({
                "type": "tender", "source": "CanadaBuys (Канада)", "source_id": ref,
                "url": row.get("noticeURL-URLavis-eng") or f"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/{ref}",
                "title": title, "summary": " ".join((row.get("tenderDescription-descriptionAppelOffres-eng") or "").split())[:1200],
                "date": (row.get("publicationDate-datePublication") or "")[:10] or None,
                "deadline": (row.get("tenderClosingDate-appelOffresDateCloture") or "")[:10] or None,
                "country_code": "CA", "customer": row.get("contractingEntityName-nomEntitContractante-eng") or "",
                "price": None, "currency": "CAD", "status": row.get("tenderStatus-appelOffresStatut-eng") or "",
                "law": "", "procedure": row.get("procurementMethod-methodeApprovisionnement-eng") or "",
                "query_topic": topic,
            })
        log(f"  Канада {name}: строк {len(rows)}, по темам {found}")
    return docs
