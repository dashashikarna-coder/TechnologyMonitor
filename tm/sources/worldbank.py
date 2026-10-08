"""Закупки по проектам Всемирного банка (страны Азии, Африки, Восточной Европы и др.), открытый API без ключа."""
import re
import time
from datetime import datetime

from ..http import request, session

URL = "https://search.worldbank.org/api/v2/procnotices"
TYPES = {"Invitation for Bids": "Приглашение к торгам", "Request for Expression of Interest": "Запрос выражения интереса",
         "General Procurement Notice": "Общее уведомление", "Contract Award": "Контракт заключён"}


def _iso(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def collect(queries: list[tuple[str, str]], per_query: int = 30, log=print) -> list[dict]:
    s = session(Accept="application/json")
    docs = []
    for topic, q in queries:
        try:
            r = request(s, "GET", URL, params={"format": "json", "qterm": f'"{q}"', "rows": per_query,
                                               "srt": "submission_date", "order": "desc"})
            notices = r.json().get("procnotices") or []
        except Exception as e:
            log(f"  Всемирный банк [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
            continue
        for n in notices:
            text = re.sub(r"<[^>]+>|&nbsp;", " ", n.get("notice_text") or "")
            docs.append({
                "type": "tender", "source": "Всемирный банк", "source_id": n["id"],
                "url": f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{n['id']}",
                "title": n.get("bid_description") or n.get("project_name") or "",
                "summary": re.sub(r"\s+", " ", text)[:1200],
                "date": _iso(n.get("noticedate")), "deadline": _iso(n.get("submission_deadline_date")),
                "country_code": n.get("project_ctry_name") or n.get("contact_ctry_name") or "",
                "customer": n.get("contact_organization") or "", "price": None, "currency": "USD",
                "status": TYPES.get(n.get("notice_type"), n.get("notice_type") or ""),
                "law": "", "procedure": n.get("procurement_method_name") or "", "query_topic": topic,
            })
        log(f"  Всемирный банк [{topic}] «{q}»: {len(notices)}")
        time.sleep(0.5)
    return docs
