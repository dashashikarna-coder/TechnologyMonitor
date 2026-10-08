"""Сбор тендеров и патентов по темам из config/topics.yaml (темы — из Google-таблицы, см. import_topics.py).

    python collect.py                    # всё
    python collect.py --only patents     # tenders | patents | foreign (можно через запятую)
    python collect.py --quick            # по одному запросу на тему — быстрая проверка
    python collect.py --only none        # без сбора: только переразметить базу и пересобрать сайт
"""
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from tm import countries
from tm.sources import canada, eis, epo_ld, fips, kz, patents, sam, ted, worldbank
from tm.topics import Topics
from tm.translate import is_russian, translate

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "documents.json"
SITE_DATA = ROOT / "site" / "data.js"
MIN_DATE = "2021-01-01"  # более старые документы не показываем


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def doc_key(d: dict) -> str:
    if d["type"] == "patent" and d.get("number"):
        return f"patent:{d['number']}"
    return f"{d['type']}:{d['source']}:{d['source_id']}"


def classify(topics: Topics, d: dict):
    title = f"{d.get('title') or ''} {d.get('title_ru') or ''}"
    body = f"{(d.get('summary') or '')[:1500]} {d.get('summary_ru') or ''}"
    return topics.classify(title, body, kind=d["type"])


def too_old(d: dict) -> bool:
    return bool(d.get("date")) and d["date"] < MIN_DATE


def fix_url(d: dict):
    """Ссылки, собранные старыми версиями источников."""
    if d["source"].startswith("EPO") and ("register.epo.org" in d.get("url", "") or d.get("url", "").endswith("NWB8.html")):
        m = re.fullmatch(r"EP(\d+)([A-Z]\d?)", d.get("number") or "")
        if m:
            d["url"] = epo_ld.doc_url(f"EP {m[1]} {m[2]}")
    if d["source"].startswith("CanadaBuys") and d.get("url", "").endswith("/tender-opportunities"):
        d["url"] = f"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/{d['source_id']}"


def first_per_topic(queries):
    seen, out = set(), []
    for topic, q in queries:
        if topic not in seen:
            seen.add(topic)
            out.append((topic, q))
    return out


def gather(topics: Topics, only: set[str], quick: bool, known: set[str]) -> tuple[list[dict], dict]:
    ru, en = topics.queries("ru"), topics.queries("en")
    pat, pat_en = topics.patent_queries("ru"), topics.patent_queries("en")
    if quick:
        ru, en, pat, pat_en = (first_per_topic(x) for x in (ru, en, pat, pat_en))
    raw, stats = [], {}

    def run(name, fn, *args):
        print(f"\n▶ {name}")
        docs = fn(*args)
        stats[name] = len(docs)
        raw.extend(docs)

    if "foreign" in only:  # только зарубежные источники — быстрое дообновление
        run("TED (Евросоюз)", ted.collect, en)
        run("Всемирный банк", worldbank.collect, en)
        run("CanadaBuys (Канада)", canada.collect, en)
        run("SAM.gov (США)", sam.collect, en)
        run("EPO Linked Data (европейские патенты)", epo_ld.collect, pat_en)
    if "us" in only:
        run("SAM.gov (США)", sam.collect, en)
    if "tenders" in only:
        run("ЕИС (Россия)", eis.collect, ru)
        run("Госзакупки Казахстана", kz.collect, ru)
        run("TED (Евросоюз)", ted.collect, en)
        run("Всемирный банк", worldbank.collect, en)
        run("CanadaBuys (Канада)", canada.collect, en)
        run("SAM.gov (США)", sam.collect, en)
    if "patents" in only:
        run("ФИПС (Роспатент)", fips.collect, pat, known)
        run("EPO Linked Data (европейские патенты)", epo_ld.collect, pat_en)
        # необязательный источник: работает, только если в .env есть ключ EPO OPS
        run("EPO OPS (весь мир)", patents.epo, en)
    return raw, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="tenders,patents")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    load_env()
    topics = Topics(ROOT / "config" / "topics.yaml")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    store = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {"meta": {}, "docs": []}
    # темы и правила отбора могли поменяться — переразмечаем уже сохранённое
    kept = []
    for d in store["docs"]:
        if d["type"] == "paper" or too_old(d):
            continue
        fix_url(d)
        d["topics"], d["keywords"] = classify(topics, d)
        if d["topics"]:
            kept.append(d)
    print(f"Переразметка базы: оставлено {len(kept)} из {len(store['docs'])}")
    store["docs"] = kept
    known = {doc_key(d): d for d in store["docs"]}

    raw, stats = gather(topics, set(args.only.split(",")), args.quick, set(known))

    fresh = {}
    for d in raw:
        k = doc_key(d)
        if k not in known and k not in fresh:
            fresh[k] = d
    fresh = list(fresh.values())
    print(f"\nНайдено {len(raw)}, новых (ещё не было в базе) {len(fresh)}. Перевожу на русский…")

    titles = translate([d["title"] for d in fresh])
    summaries = translate([d["summary"][:600] if not is_russian(d["summary"]) else "" for d in fresh])
    added = 0
    for d, t_ru, s_ru in zip(fresh, titles, summaries):
        d["title_ru"] = t_ru
        d["summary_ru"] = s_ru or d["summary"][:600]
        d["topics"], d["keywords"] = classify(topics, d)
        if not d["topics"] or too_old(d):
            continue
        raw_country = d.get("country_code")
        d["country_code"], d["country"] = countries.code(raw_country), countries.name(raw_country)
        d["first_seen"] = now
        d.pop("query_topic", None)
        store["docs"].append(d)
        added += 1

    store["docs"].sort(key=lambda d: d.get("date") or d["first_seen"][:10], reverse=True)
    if not stats:  # пересборка без сбора — дата обновления данных прежняя
        now = store["meta"].get("updated") or now
    store["meta"] = {"updated": now, "prev_updated": store["meta"].get("prev_updated" if not stats else "updated"), "added": added,
                     "total": len(store["docs"]), "sources": stats or store["meta"].get("sources", {})}

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {"meta": store["meta"], "topics": [{"id": t["id"], "name": t["name"]} for t in topics.items], "docs": store["docs"]}
    SITE_DATA.parent.mkdir(exist_ok=True)
    SITE_DATA.write_text("window.TM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    by_type = {t: sum(d["type"] == t for d in store["docs"]) for t in ("tender", "patent")}
    print(f"\nДобавлено по темам: {added}. В базе: тендеров {by_type['tender']}, патентов {by_type['patent']}.")
    print(f"Откройте {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
