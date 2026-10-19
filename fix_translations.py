"""Доперевод названий/описаний, которые остались на исходном языке (болгарский и др.).

    python fix_translations.py
"""
import json
from pathlib import Path

from tm.translate import is_russian, translate

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "documents.json"
SITE = ROOT / "site" / "data.js"


def needs(text: str, ru: str) -> bool:
    t = (text or "").strip()
    if not t or is_russian(t):
        return False
    r = (ru or "").strip()
    return (not r) or r == t or not is_russian(r)


def main():
    store = json.loads(DATA.read_text(encoding="utf-8"))
    docs = store["docs"]
    titles = [d for d in docs if needs(d.get("title"), d.get("title_ru"))]
    sums = [d for d in docs if needs(d.get("summary"), d.get("summary_ru"))]
    print(f"К переводу: названий {len(titles)}, описаний {len(sums)}")
    if titles:
        for d, tr in zip(titles, translate([d["title"] for d in titles])):
            d["title_ru"] = tr
            print(" ", (d.get("country") or "")[:12], "→", tr[:70])
    if sums:
        for d, tr in zip(sums, translate([(d.get("summary") or "")[:600] for d in sums])):
            d["summary_ru"] = tr
    topics = json.loads(SITE.read_text(encoding="utf-8").removeprefix("window.TM_DATA = ").rstrip(";\n"))["topics"]
    # переразметка тем подтянется в collect --only none; здесь только перевод + запись
    DATA.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    payload = {"meta": store["meta"], "topics": topics, "docs": docs}
    SITE.write_text("window.TM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("Готово.")


if __name__ == "__main__":
    main()
