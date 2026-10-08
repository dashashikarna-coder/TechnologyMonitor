"""Госзакупки Казахстана: поиск лотов на goszakup.gov.kz (на русском языке, без ключа)."""
import re
import time
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from ..http import request, session

BASE = "https://goszakup.gov.kz"
FIELD_RE = r'{label}</label>\s*<div[^>]*>\s*<input[^>]*value="([^"]*)"'


def _price(value: str) -> float | None:
    try:
        v = float(re.sub(r"[^\d.]", "", value or ""))
    except ValueError:
        return None
    return v if v > 1 else None


def _field(html: str, label: str) -> str:
    m = re.search(FIELD_RE.format(label=re.escape(label)), html)
    return m.group(1).strip() if m else ""


def _details(s, url: str) -> dict:
    """Даты и организатор есть только на странице объявления."""
    try:
        h = request(s, "GET", url, timeout=30).text
    except Exception:
        return {}
    org = re.search(r"Организатор</t[hd]>\s*<td[^>]*>([^<]+)", h)
    return {
        "date": _field(h, "Дата публикации объявления")[:10] or None,
        "deadline": _field(h, "Срок окончания приема заявок")[:10] or None,
        "customer": re.sub(r"^\d{12}\s*", "", org.group(1).strip()) if org else "",
    }


def collect(queries: list[tuple[str, str]], per_query: int = 25, log=print) -> list[dict]:
    s = session()
    docs, seen = [], set()
    for topic, q in queries:
        try:
            r = request(s, "GET", f"{BASE}/ru/search/lots", params={"filter[name]": q, "count_record": 50})
            rows = BeautifulSoup(r.text, "lxml").select("table#search-result tbody tr")
        except Exception as e:
            log(f"  Казахстан [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
            continue
        items = []
        for tr in rows:
            td = [c.get_text(" ", strip=True) for c in tr.select("td")]
            link = tr.select_one("a[href^='/ru/announce/index/']")
            if len(td) < 7 or not link or td[0] in seen:
                continue
            seen.add(td[0])
            lot = re.sub(r"\s*История$", "", td[2])
            announce = re.sub(r"^\d+-\d+\s*", "", td[1].split(" Заказчик:")[0])
            items.append({
                "type": "tender", "source": "Госзакупки Казахстана", "source_id": td[0],
                "url": BASE + link["href"], "title": lot, "summary": announce,
                "country_code": "KZ", "price": _price(td[4]), "currency": "KZT",
                "status": td[6], "procedure": td[5], "law": "",
                "customer": (td[1].split("Заказчик:")[1].strip() if "Заказчик:" in td[1] else ""),
                "query_topic": topic,
            })
            if len(items) >= per_query:
                break
        with ThreadPoolExecutor(max_workers=4) as pool:
            for item, extra in zip(items, pool.map(lambda d: _details(s, d["url"]), items)):
                item.update({k: v for k, v in extra.items() if v})
                item.setdefault("date", None)
                item.setdefault("deadline", None)
        docs += items
        log(f"  Казахстан [{topic}] «{q}»: {len(items)}")
        time.sleep(1)
    return docs
