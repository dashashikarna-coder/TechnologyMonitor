"""Госзакупки США — SAM.gov (поиск, которым пользуется сам сайт; без ключа)."""
import html
import re
import time

from ..http import request, session

URL = "https://sam.gov/api/prod/sgs/v1/search/"


def collect(queries: list[tuple[str, str]], per_query: int = 100, log=print) -> list[dict]:
    s = session(Accept="*/*")  # на application/json SAM.gov отвечает 406
    docs = []
    for topic, q in queries:
        try:
            r = request(s, "GET", URL, params={"index": "opp", "q": f'"{q}"', "page": 0, "size": per_query,
                                               "mode": "search", "is_active": "false"}, timeout=60)
            rows = (r.json().get("_embedded") or {}).get("results") or []
        except Exception as e:
            log(f"  SAM.gov [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
            continue
        for n in rows:
            if n.get("isCanceled"):
                continue
            desc = (n.get("descriptions") or [{}])[0].get("content") or ""
            orgs = sorted(n.get("organizationHierarchy") or [], key=lambda o: o.get("level") or 0)
            customer = " / ".join(o["name"].title() for o in orgs[:2] if o.get("name"))
            docs.append({
                "type": "tender", "source": "SAM.gov (США)", "source_id": n["_id"],
                "url": f"https://sam.gov/opp/{n['_id']}/view",
                "title": " ".join((n.get("title") or "").split()),
                "summary": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", desc))).strip()[:1200],
                "date": (n.get("publishDate") or "")[:10] or None,
                "deadline": (n.get("responseDate") or "")[:10] or None,
                "country_code": "US", "customer": customer, "price": None, "currency": "USD",
                "status": "Активна" if n.get("isActive") else "Архив",
                "law": "", "procedure": (n.get("type") or {}).get("value") or "",
                "number": None, "solicitation": n.get("solicitationNumber") or "", "query_topic": topic,
            })
        log(f"  SAM.gov [{topic}] «{q}»: {len(rows)}")
        time.sleep(0.7)
    return docs
