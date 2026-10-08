"""Европейские патенты (EP) — открытый EPO Linked Data (data.epo.org), без ключа.

Заявители со всего мира: США, Китай, Япония, Корея, Европа… Поиск — полнотекстовый по названию изобретения.
"""
import re
import time
from datetime import date, timedelta

from ..http import request, session

URL = "https://data.epo.org/linked-data/query"
QUERY = """
PREFIX patent: <http://data.epo.org/linked-data/def/patent/>
PREFIX text: <http://jena.apache.org/text#>
PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?pub ?label ?date ?title ?lang ?name ?cc ?ipc WHERE {
  ?pub text:query (patent:titleOfInvention '%s' %d) .
  ?pub patent:publicationDate ?date . FILTER(?date >= '%s'^^<http://www.w3.org/2001/XMLSchema#date>)
  ?pub rdfs:label ?label ; patent:titleOfInvention ?title . BIND(lang(?title) AS ?lang)
  OPTIONAL { ?pub patent:applicantVC ?vc . ?vc vcard:fn ?name .
             OPTIONAL { ?vc vcard:hasAddress ?a . ?a patent:countryCode ?cc } }
  OPTIONAL { ?pub patent:classificationIPCInventive ?ipc }
}"""


def doc_url(label: str) -> str:
    """«EP 4718300 A1» → полный текст публикации на data.epo.org (Register требует номер заявки, а не публикации)."""
    parts = label.split()
    if len(parts) == 3:
        kind = "B1" if parts[2] == "B8" else parts[2]  # для исправлений (B8) полного текста нет — ведём на сам патент
        return f"https://data.epo.org/linked-data/representation/publication/EP/{parts[1]}/NW{kind}.html"
    return f"https://data.epo.org/linked-data/data/publication/EP/{parts[1] if len(parts) > 1 else label}"


def _lucene(words: list[str]) -> str:
    terms = [f'"{w}"' if " " in w else w for w in words]
    return " OR ".join(re.sub(r"['\\]", " ", t) for t in terms)


def collect(queries, days: int = 1825, hits: int = 400, log=print) -> list[dict]:
    """queries: [(topic, [английские ключевые слова]), ...]."""
    s = session(Accept="application/sparql-results+json")
    since = (date.today() - timedelta(days=days)).isoformat()
    docs = {}
    for topic, words in queries:
        q = QUERY % (_lucene(words), hits, since)
        rows, err = None, None
        for attempt in range(3):  # соединение с data.epo.org периодически обрывается
            try:
                r = request(s, "GET", URL, params={"query": q}, timeout=90)
                r.raise_for_status()
                rows = r.json()["results"]["bindings"]
                break
            except Exception as e:
                err = e
                time.sleep(5 * (attempt + 1))
        if rows is None:
            log(f"  EPO [{topic}] {' / '.join(words[:3])}…: ОШИБКА {type(err).__name__}")
            continue
        before = len(docs)
        for row in rows:
            v = {k: x["value"] for k, x in row.items()}
            label = v["label"]  # «EP 4200000 A1»
            d = docs.get(label)
            if not d:
                cc_num = label.replace(" ", "")
                d = docs[label] = {
                    "type": "patent", "source": "EPO (европейские патенты)", "source_id": cc_num,
                    "number": cc_num, "kind": "Европейская заявка" if label.endswith(("A1", "A2", "A3")) else "Европейский патент",
                    "url": doc_url(label),
                    "title": "", "summary": "", "date": v["date"][:10], "applicants": [], "inventors": [],
                    "ipc": [], "country_code": "", "status": "", "query_topic": topic, "_titles": {},
                }
            d["_titles"][v.get("lang", "")] = v["title"]
            name = " ".join((v.get("name") or "").split())
            if name and name not in d["applicants"]:
                d["applicants"].append(name)
                if not d["country_code"] and v.get("cc"):
                    d["country_code"] = v["cc"]
            if v.get("ipc"):
                code = v["ipc"].rsplit("/", 1)[-1].replace("-", "/")
                code = re.sub(r"^([A-H]\d{2}[A-Z])(\d+)/", r"\1 \2/", code)
                if code not in d["ipc"]:
                    d["ipc"].append(code)
        log(f"  EPO [{topic}] {' / '.join(words[:3])}…: {len(docs) - before}")
        time.sleep(1)
    out = []
    for d in docs.values():
        titles = d.pop("_titles")
        t = titles.get("en") or next(iter(titles.values()), "")
        d["title"] = t.capitalize() if t.isupper() else t
        d["ipc"] = d["ipc"][:6]
        d["applicants"] = d["applicants"][:5]
        out.append(d)
    return out
