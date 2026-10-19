"""Убрать ложный досбор «дронопортов» (обычные дроны) и пересобрать сайт."""
import json
import re
from pathlib import Path

from tm.topics import Topics
from collect import classify, SITE_DATA, DATA_FILE

STRICT = re.compile(r"дронопорт|дронпорт|droneport", re.I)
BATCH = "2026-10-19T10:22"  # first_seen досбора collect_droneport.py


def blob(d: dict) -> str:
    return " ".join([
        d.get("title") or "", d.get("title_ru") or "",
        d.get("summary") or "", d.get("summary_ru") or "",
        " ".join(d.get("keywords") or []),
    ])


def main():
    store = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    topics = Topics(Path("config/topics.yaml"))
    before = len(store["docs"])
    kept, removed = [], 0
    for d in store["docs"]:
        fs = d.get("first_seen") or ""
        if fs.startswith(BATCH) and not STRICT.search(blob(d)):
            removed += 1
            continue
        d["topics"], d["keywords"] = classify(topics, d)
        # ключ «дрон-порт» больше не используем — вычищаем хвосты
        d["keywords"] = [k for k in (d.get("keywords") or []) if k.lower() not in {"дрон-порт", "drone port", "drone hangar", "uav hangar", "порт для бпла"}]
        if not d["topics"]:
            removed += 1
            continue
        kept.append(d)
    store["docs"] = kept
    store["meta"]["total"] = len(kept)
    store["meta"]["added"] = 0
    DATA_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {
        "meta": store["meta"],
        "topics": [{"id": t["id"], "name": t["name"]} for t in topics.items],
        "docs": kept,
    }
    SITE_DATA.write_text("window.TM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    strict_n = sum(1 for d in kept if STRICT.search(blob(d)))
    print(f"Было {before}, удалено {removed}, осталось {len(kept)}, настоящих дронопортов: {strict_n}")


if __name__ == "__main__":
    main()
