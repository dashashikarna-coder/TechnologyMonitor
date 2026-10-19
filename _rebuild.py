import json
from pathlib import Path

from tm.topics import Topics

ROOT = Path(__file__).parent
store = json.loads((ROOT / "data" / "documents.json").read_text(encoding="utf-8"))
topics = Topics(ROOT / "config" / "topics.yaml")
docs = []
for d in store["docs"]:
    title = f"{d.get('title') or ''} {d.get('title_ru') or ''}"
    body = f"{(d.get('summary') or '')[:1500]} {d.get('summary_ru') or ''}"
    d["topics"], d["keywords"] = topics.classify(title, body, kind=d["type"])
    if d["topics"]:
        docs.append(d)
store["docs"] = docs
store["meta"]["total"] = len(docs)
(ROOT / "data" / "documents.json").write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
payload = {"meta": store["meta"], "topics": [{"id": t["id"], "name": t["name"]} for t in topics.items], "docs": docs}
(ROOT / "site" / "data.js").write_text("window.TM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
exo = [d for d in docs if "exoskeletons" in d["topics"]]
print("docs", len(docs), "exo", len(exo),
      "с экзопротез", sum("экзопротез" in (d.get("title_ru") or d.get("title") or "").lower() for d in exo))
