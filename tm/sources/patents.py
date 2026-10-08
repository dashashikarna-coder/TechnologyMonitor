"""Патенты.

  * Роспатент (searchplatform.rospatent.gov.ru) — российские патенты, нужен ROSPATENT_TOKEN.
  * EPO OPS (ops.epo.org) — патенты всего мира (RU, CN, US, EP, WO, JP…), нужны EPO_KEY и EPO_SECRET.
  * Google Patents — без ключа, но часто блокирует запросы (ответ 503); тогда пропускается.
"""
import os
import re
import time
from datetime import date
from urllib.parse import quote

from ..http import request, session

ROSPATENT_URL = "https://searchplatform.rospatent.gov.ru/patsearch/v0.2/search"
EPO_TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
EPO_SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"
GOOGLE_URL = "https://patents.google.com/xhr/query"


def _doc(**kw) -> dict:
    return {"type": "patent", "summary": "", "applicants": [], "inventors": [], "ipc": [], **kw}


def _iso(value: str | None) -> str | None:
    m = re.search(r"(\d{4})[.\-]?(\d{2})[.\-]?(\d{2})", str(value or ""))
    return f"{m[1]}-{m[2]}-{m[3]}" if m else None


# ---------- Роспатент ----------

def rospatent(queries, per_query: int = 30, log=print) -> list[dict]:
    token = os.environ.get("ROSPATENT_TOKEN")
    if not token:
        log("  Роспатент: пропущен — нет ROSPATENT_TOKEN в .env")
        return []
    s = session(Authorization=f"Bearer {token}", Accept="application/json")
    docs = []
    for topic, q in queries:
        try:
            r = request(s, "POST", ROSPATENT_URL, json={"qn": q, "limit": per_query, "sort": "publication_date:desc"})
            r.raise_for_status()
            hits = r.json().get("hits", [])
            for h in hits:
                common, biblio = h.get("common", {}), h.get("biblio", {})
                bib = biblio.get("ru") or biblio.get("en") or {}
                office = common.get("publishing_office", "RU")
                number = f"{office}{common.get('document_number', '')}{common.get('kind', '')}"
                docs.append(_doc(
                    source="Роспатент",
                    source_id=h.get("id") or number,
                    url=f"https://searchplatform.rospatent.gov.ru/doc/{h.get('id')}",
                    title=bib.get("title") or (h.get("snippet") or {}).get("title") or "",
                    summary=re.sub(r"<[^>]+>", "", (h.get("snippet") or {}).get("description") or "")[:1200],
                    date=_iso(common.get("publication_date")),
                    country_code=office,
                    number=number,
                    applicants=[p.get("name") for p in (bib.get("patentee") or bib.get("applicant") or []) if p.get("name")],
                    inventors=[p.get("name") for p in bib.get("inventor") or [] if p.get("name")],
                    ipc=[c.get("fullname") for c in (common.get("classification") or {}).get("ipc", []) if c.get("fullname")],
                    query_topic=topic,
                ))
            log(f"  Роспатент [{topic}] «{q}»: {len(hits)}")
        except Exception as e:
            log(f"  Роспатент [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
    return docs


# ---------- EPO OPS ----------

def _v(node):
    """OPS JSON: значения лежат в ключе '$'."""
    if isinstance(node, dict):
        return node.get("$", "")
    return node or ""


def _as_list(node):
    return node if isinstance(node, list) else [node] if node else []


def _epo_parse(doc: dict, topic: str) -> dict | None:
    ex = doc.get("exchange-document") or {}
    bib = ex.get("bibliographic-data") or {}
    country, number, kind = ex.get("@country", ""), ex.get("@doc-number", ""), ex.get("@kind", "")
    titles = {t.get("@lang"): _v(t) for t in _as_list(bib.get("invention-title"))}
    title = titles.get("ru") or titles.get("en") or next(iter(titles.values()), "")
    if not title:
        return None
    pub = next((d for d in _as_list((bib.get("publication-reference") or {}).get("document-id"))
                if d.get("@document-id-type") == "docdb"), {})
    parties = bib.get("parties") or {}
    applicants = [_v((a.get("applicant-name") or {}).get("name")) for a in _as_list((parties.get("applicants") or {}).get("applicant"))
                  if a.get("@data-format") == "epodoc"]
    inventors = [_v((a.get("inventor-name") or {}).get("name")) for a in _as_list((parties.get("inventors") or {}).get("inventor"))
                 if a.get("@data-format") == "epodoc"]
    ipc = [" ".join(_v(c.get("text")).split()[:2]) for c in _as_list((bib.get("classifications-ipcr") or {}).get("classification-ipcr"))]
    abstracts = {a.get("@lang"): " ".join(_v(p) for p in _as_list(a.get("p"))) for a in _as_list(ex.get("abstract"))}
    pn = f"{country}{number}{kind}"
    return _doc(
        source="EPO (Espacenet)",
        source_id=pn,
        url=f"https://worldwide.espacenet.com/patent/search?q=pn%3D{country}{number}",
        title=title,
        summary=(abstracts.get("ru") or abstracts.get("en") or next(iter(abstracts.values()), ""))[:1200],
        date=_iso(_v(pub.get("date"))),
        country_code=country,
        number=pn,
        applicants=[a for a in dict.fromkeys(applicants) if a],
        inventors=[i for i in dict.fromkeys(inventors) if i],
        ipc=[c for c in dict.fromkeys(ipc) if c][:6],
        query_topic=topic,
    )


def epo(queries, per_query: int = 25, years: int = 2, log=print) -> list[dict]:
    key, secret = os.environ.get("EPO_KEY"), os.environ.get("EPO_SECRET")
    if not key or not secret:
        log("  EPO: пропущен — нет EPO_KEY / EPO_SECRET в .env")
        return []
    s = session()
    try:
        r = request(s, "POST", EPO_TOKEN_URL, auth=(key, secret), data={"grant_type": "client_credentials"})
        r.raise_for_status()
        s.headers.update({"Authorization": f"Bearer {r.json()['access_token']}", "Accept": "application/json"})
    except Exception as e:
        log(f"  EPO: не удалось получить токен — {e}")
        return []

    period = f'pd within "{date.today().year - years + 1} {date.today().year}"'
    docs = []
    for topic, q in queries:
        cql = f'ta all "{q}" and {period}'
        try:
            r = request(s, "GET", EPO_SEARCH_URL, params={"q": cql, "Range": f"1-{per_query}"})
            if r.status_code == 404:  # ничего не найдено
                log(f"  EPO   [{topic}] «{q}»: 0")
                continue
            r.raise_for_status()
            res = (((r.json().get("ops:world-patent-data") or {}).get("ops:biblio-search") or {})
                   .get("ops:search-result") or {}).get("exchange-documents")
            found = [d for d in (_epo_parse(x, topic) for x in _as_list(res)) if d]
            docs += found
            log(f"  EPO   [{topic}] «{q}»: {len(found)}")
        except Exception as e:
            log(f"  EPO   [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
        time.sleep(0.5)
    return docs


# ---------- Google Patents ----------

def google(queries, per_query: int = 20, log=print) -> list[dict]:
    s = session(Accept="application/json", Referer="https://patents.google.com/")
    docs = []
    for topic, q in queries:
        inner = f"q=({q})&num={per_query}&sort=new"
        try:
            r = request(s, "GET", f"{GOOGLE_URL}?url={quote(inner, safe='')}&exp=", timeout=30)
            if r.status_code in (429, 503) or "json" not in r.headers.get("content-type", ""):
                log("  Google Patents: доступ заблокирован Google (503) — пропускаю")
                return docs
            clusters = (r.json().get("results") or {}).get("cluster") or []
            found = 0
            for c in clusters:
                for res in c.get("result", []):
                    p = res.get("patent") or {}
                    pn = (p.get("publication_number") or "").upper()
                    if not pn or not p.get("title"):
                        continue
                    docs.append(_doc(
                        source="Google Patents",
                        source_id=pn,
                        url=f"https://patents.google.com/patent/{pn}",
                        title=re.sub(r"<[^>]+>", "", p["title"]),
                        summary=re.sub(r"<[^>]+>", "", p.get("snippet") or "")[:1200],
                        date=_iso(p.get("publication_date") or p.get("priority_date")),
                        country_code=pn[:2],
                        number=pn,
                        applicants=[re.sub(r"<[^>]+>", "", p.get("assignee") or "")] if p.get("assignee") else [],
                        inventors=[re.sub(r"<[^>]+>", "", p.get("inventor") or "")] if p.get("inventor") else [],
                        query_topic=topic,
                    ))
                    found += 1
            log(f"  Google [{topic}] «{q}»: {found}")
        except Exception as e:
            log(f"  Google [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
        time.sleep(2)
    return docs
