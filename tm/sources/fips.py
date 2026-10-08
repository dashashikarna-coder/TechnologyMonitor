"""ФИПС (www1.fips.ru) — открытая информационно-поисковая система Роспатента, без ключей и регистрации.

Ищет по российским изобретениям, заявкам и полезным моделям (в том числе от иностранных заявителей),
затем для каждого документа берёт карточку из открытого реестра: реферат, заявители, МПК, статус.
"""
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from bs4 import BeautifulSoup

from ..http import request, session

BASE = "https://www1.fips.ru"
VIEW_RE = r'name="javax\.faces\.ViewState"[^>]*value="([^"]+)"'
# библиотека в выдаче -> база открытого реестра
REGISTRY_DB = {"РИ": "RUPAT", "НИЗ": "RUPAT", "ЗИЗ": "RUPATAP", "ФПМ": "RUPM", "НПМ": "RUPM"}
KIND = {"RUPAT": "Патент на изобретение", "RUPATAP": "Заявка на изобретение", "RUPM": "Полезная модель"}
COUNTRY_RE = re.compile(r"\(([A-Z]{2})\)")


def _view(html: str, form: str) -> str:
    return re.search(VIEW_RE, html[html.find(f'id="{form}"'):]).group(1)


class Fips:
    def __init__(self):
        self.s = session()
        self._open_search()

    def _open_search(self):
        """Выбор баз «Патентные документы РФ (рус.)» и переход к форме поиска (JSF, как в браузере)."""
        h = request(self.s, "GET", BASE + "/iiss/").text
        action = re.search(r'<form id="db-selection-form"[^>]*action="([^"]+)"', h).group(1)
        boxes = [f"db-selection-form:dbsGrid1:{i}:dbsGrid1checkbox" for i in range(5)]
        data = {"db-selection-form": "db-selection-form", "javax.faces.ViewState": _view(h, "db-selection-form"),
                **{b: "on" for b in boxes}}
        r = request(self.s, "POST", BASE + action, headers={"Faces-Request": "partial/ajax"}, data={
            **data, "javax.faces.partial.ajax": "true", "javax.faces.source": boxes[0],
            "javax.faces.partial.execute": boxes[0], "javax.faces.partial.render": "db-selection-form:button-set1",
            "javax.faces.behavior.event": "change"})
        data["javax.faces.ViewState"] = re.search(r'ViewState:0"><!\[CDATA\[([^\]]+)\]\]>', r.text).group(1)
        data["db-selection-form:j_idt90"] = "перейти к поиску"
        request(self.s, "POST", BASE + action, data=data)

    def search(self, query: str, since: date) -> tuple[int, list[dict]]:
        """Первая страница выдачи (до 50 документов), опубликованных после даты since."""
        h = request(self.s, "GET", BASE + "/iiss/search.xhtml").text
        fields = {"searchForm": "searchForm", "j_idt89": query, "j_idt92": "Поиск",
                  "javax.faces.ViewState": _view(h, "searchForm")}
        for name in re.findall(r'name="(fields:\d+:j_idt109)"', h):
            fields[name] = ""
        fields["fields:2:j_idt109"] = ">" + since.strftime("%Y%m%d")
        r = request(self.s, "POST", BASE + "/iiss/search.xhtml", data=fields)
        soup = BeautifulSoup(r.text, "lxml")
        total = re.search(r"Всего найдено:\s*(\d+)", soup.get_text(" ", strip=True))
        rows = []
        for a in soup.select("a.tr[data-index]"):
            td = [c.get_text(" ", strip=True) for c in a.select("div.td")]
            if len(td) < 6:
                continue
            rows.append({"number": td[1], "date": td[2].strip("()"), "title": td[4], "lib": td[5], "href": a.get("href")})
        return (int(total.group(1)) if total else 0), rows

    def card(self, db: str, number: str, href: str) -> dict:
        """Карточка документа. Открытый реестр пускает не чаще раза в 3 с, поэтому текст берём из ИПС
        (ссылка действует только в этой сессии), а пользователю даём постоянную ссылку на реестр."""
        url = f"{BASE}/registers-doc-view/fips_servlet?DB={db}&DocNumber={number}&TypeFile=html"
        r = request(self.s, "GET", f"{BASE}/iiss/{href}")
        text = BeautifulSoup(r.text, "lxml").get_text("\n", strip=True)

        def section(label, stop=r"\n\(\d{2}\)|\nАдрес для переписки|\nСтатус"):
            m = re.search(re.escape(label) + r"[^\n]*\n(.*?)(?=" + stop + "|$)", text, re.S)
            return m.group(1).strip() if m else ""

        abstract = section("(57) Реферат:", stop=r"\nФормула|\nИзобретение относится к[^\n]*\n\n|\n\(\d{2}\)")
        end = re.search(r"\d+\s*ил\.", abstract)  # после «N ил.» начинается описание
        if end:
            abstract = abstract[:end.end()]
        holders = section("(73) Патентообладатель(и):") or section("(71) Заявитель(и):")
        names = [n.strip() for n in re.split(r"\n|,\s*(?=[А-ЯA-Z«\"])", holders) if n.strip()]
        ipc = re.findall(r"\b([A-H]\d{2}[A-Z]\s+\d+/\d+)", section("(51) МПК", stop=r"\n\(\d{2}\)|\nСтатус"))
        status = re.search(r"Статус:\s*\n?([^\n(]+)", text)
        return {
            "url": url,
            "summary": re.sub(r"\s+", " ", abstract)[:1500],
            "applicants": names[:5],
            "country_code": (COUNTRY_RE.findall(holders) or ["RU"])[0],
            "ipc": [re.sub(r"\s+", " ", c) for c in dict.fromkeys(ipc)][:6],
            "status": status.group(1).strip() if status else ("заявка" if db == "RUPATAP" else ""),
        }


def _iso(d: str) -> str | None:
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", d or "")
    return f"{m[3]}-{m[2]}-{m[1]}" if m else None


def _query(keywords: list[str]) -> str:
    return " OR ".join(f'"{k}"' if " " in k else k for k in keywords)


def collect(queries, known: set[str] = frozenset(), days: int = 1825, per_query: int = 50, log=print) -> list[dict]:
    """queries: [(topic, [ключевые слова]), ...] — слова одной группы объединяются через OR.
    known — ключи уже сохранённых документов («patent:RU…»): их карточки повторно не скачиваются."""
    try:
        f = Fips()
    except Exception as e:
        log(f"  ФИПС: недоступен — {type(e).__name__}: {e}")
        return []
    since = date.today() - timedelta(days=days)
    docs, seen = [], set()
    for topic, words in queries:
        q = _query(words)
        try:
            total, rows = f.search(q, since)
        except Exception as e:
            log(f"  ФИПС [{topic}] {q[:60]}: ОШИБКА {type(e).__name__}: {e}")
            continue
        todo = []
        for row in rows[:per_query]:
            db = REGISTRY_DB.get(row["lib"], "RUPAT")
            if (db, row["number"]) not in seen and f"patent:RU{row['number']}" not in known:
                seen.add((db, row["number"]))
                todo.append((db, row))

        def fetch(item):
            db, row = item
            try:
                return f.card(db, row["number"], row["href"])
            except Exception:
                return {"url": f"{BASE}/registers-doc-view/fips_servlet?DB={db}&DocNumber={row['number']}&TypeFile=html",
                        "summary": "", "applicants": [], "country_code": "RU", "ipc": [], "status": ""}

        with ThreadPoolExecutor(max_workers=4) as pool:
            cards = list(pool.map(fetch, todo))
        new = 0
        for (db, row), card in zip(todo, cards):
            docs.append({
                "type": "patent", "source": "ФИПС (Роспатент)", "source_id": f"{db}:{row['number']}",
                "number": f"RU{row['number']}", "kind": KIND[db], "title": row["title"].capitalize() if row["title"].isupper() else row["title"],
                "date": _iso(row["date"]), "inventors": [], "query_topic": topic, **card,
            })
            new += 1
        log(f"  ФИПС [{topic}] {q[:70]}…: найдено {total}, взято {new}")
    return docs
