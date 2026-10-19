"""Целевой сбор по дронопортам + нормализация стран по всей базе.

    python collect_droneport.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from tm import countries
from tm.sources import canada, eis, epo_ld, fips, kz, sam, ted, worldbank
from tm.topics import Topics
from tm.translate import is_russian, translate
from collect import classify, doc_key, SITE_DATA, DATA_FILE

RU = [("robotics", "дронопорт"), ("robotics", "дронпорт"), ("robotics", "порт для БПЛА")]
EN = [("robotics", "droneport"), ("robotics", "drone port"), ("robotics", "UAV hangar"), ("robotics", "drone hangar")]
PAT_RU = [("robotics", ["дронопорт", "дронпорт", "дрон-порт", "порт для БПЛА"])]
PAT_EN = [("robotics", ["droneport", "drone port", "UAV hangar", "drone hangar", "drone nest"])]


def main():
    topics = Topics(Path(__file__).parent / "config" / "topics.yaml")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    store = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    known = {doc_key(d): d for d in store["docs"]}
    raw = []
    for name, fn, args in [
        ("ЕИС", eis.collect, (RU,)),
        ("Казахстан", kz.collect, (RU,)),
        ("TED", ted.collect, (EN,)),
        ("Всемирный банк", worldbank.collect, (EN,)),
        ("CanadaBuys", canada.collect, (EN,)),
        ("SAM.gov", sam.collect, (EN,)),
        ("ФИПС", fips.collect, (PAT_RU, set(known))),
        ("EPO", epo_ld.collect, (PAT_EN,)),
    ]:
        print(f"\n▶ {name}", flush=True)
        try:
            part = fn(*args)
        except Exception as e:
            print(f"  ОШИБКА {type(e).__name__}: {e}", flush=True)
            part = []
        print(f"  {len(part)}", flush=True)
        raw.extend(part)

    fresh = [d for d in raw if doc_key(d) not in known]
    print(f"\nНовых сырых: {len(fresh)}. Перевод…", flush=True)
    titles = translate([d["title"] for d in fresh])
    summaries = translate([d["summary"][:600] if not is_russian(d.get("summary") or "") else "" for d in fresh])
    added = 0
    for d, t_ru, s_ru in zip(fresh, titles, summaries):
        d["title_ru"] = t_ru
        d["summary_ru"] = s_ru or (d.get("summary") or "")[:600]
        d["topics"], d["keywords"] = classify(topics, d)
        if not d["topics"]:
            continue
        src = d.get("country_code") or d.get("country")
        d["country_code"], d["country"] = countries.code(src), countries.name(src)
        d["first_seen"] = now
        d.pop("query_topic", None)
        store["docs"].append(d)
        known[doc_key(d)] = d
        added += 1

    kept = []
    for d in store["docs"]:
        if d["type"] == "paper":
            continue
        d["topics"], d["keywords"] = classify(topics, d)
        if not d["topics"]:
            continue
        src = d.get("country_code") or d.get("country")
        d["country_code"], d["country"] = countries.code(src), countries.name(src)
        kept.append(d)
    store["docs"] = kept
    store["docs"].sort(key=lambda d: d.get("date") or (d.get("first_seen") or "")[:10], reverse=True)
    store["meta"] = {
        "updated": now, "prev_updated": store["meta"].get("updated"), "added": added,
        "total": len(store["docs"]),
        "sources": {**(store["meta"].get("sources") or {}), "дронопорт (досбор)": added},
    }
    DATA_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {
        "meta": store["meta"],
        "topics": [{"id": t["id"], "name": t["name"]} for t in topics.items],
        "docs": store["docs"],
    }
    SITE_DATA.write_text("window.TM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    def is_droneport(d):
        blob = " ".join([
            d.get("title") or "", d.get("title_ru") or "",
            " ".join(d.get("keywords") or []),
        ]).lower()
        return any(x in blob for x in ("дронопорт", "дронпорт", "droneport", "drone port", "uav hangar", "drone hangar"))

    hit = sum(1 for d in store["docs"] if is_droneport(d))
    print(f"\nДобавлено: {added}. В базе: {len(store['docs'])}. С дронопортом в тексте/ключах: {hit}", flush=True)


if __name__ == "__main__":
    main()
