"""Госзакупки РФ: поиск по ЕИС zakupki.gov.ru (44-ФЗ и 223-ФЗ)."""
import re
import time

from bs4 import BeautifulSoup

from ..http import request, session

URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"
BASE = "https://zakupki.gov.ru"


def _text(el) -> str:
    # без разделителя: ЕИС оборачивает найденные части слов в <span>, разделитель разрывал бы слова
    return " ".join(el.get_text().split()) if el else ""


def _date(value: str) -> str | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", value or "")
    return f"{m[3]}-{m[2]}-{m[1]}" if m else None


def _price(value: str) -> float | None:
    digits = re.sub(r"[^\d,]", "", value or "").replace(",", ".")
    try:
        price = float(digits)
    except ValueError:
        return None
    return price if price > 0 else None


def _parse(html: str, topic: str) -> list[dict]:
    docs = []
    for b in BeautifulSoup(html, "lxml").select("div.search-registry-entry-block"):
        num_el = b.select_one(".registry-entry__header-mid__number a")
        title = _text(b.select_one(".registry-entry__body-value"))
        if not num_el or not title:
            continue
        number = _text(num_el).replace("№", "").strip()
        header = _text(b.select_one(".registry-entry__header-top__title"))
        law, _, procedure = header.partition(" ")
        dates = {_text(t): _text(t.find_next_sibling(class_="data-block__value"))
                 for t in b.select(".data-block__title")}
        href = num_el.get("href", "")
        docs.append({
            "type": "tender",
            "source": "ЕИС (zakupki.gov.ru)",
            "source_id": number,
            "url": href if href.startswith("http") else BASE + href,
            "title": title,
            "summary": "",
            "date": _date(dates.get("Размещено", "")),
            "country_code": "RU",
            "customer": _text(b.select_one(".registry-entry__body-href")),
            "price": _price(_text(b.select_one(".price-block__value"))),
            "currency": "RUB",
            "deadline": _date(dates.get("Окончание подачи заявок", "")),
            "status": _text(b.select_one(".registry-entry__header-mid__title")),
            "law": law,
            "procedure": procedure,
            "query_topic": topic,
        })
    return docs


def collect(queries: list[tuple[str, str]], per_page: int = 50, pages: int = 2, log=print) -> list[dict]:
    s = session()
    docs = []
    for topic, q in queries:
        found = []
        for page in range(1, pages + 1):
            params = {
                "searchString": q, "morphology": "on", "pageNumber": page, "recordsPerPage": f"_{per_page}",
                "sortBy": "PUBLISH_DATE", "sortDirection": "false", "fz44": "on", "fz223": "on",
                "af": "on", "ca": "on", "pc": "on", "currencyIdGeneral": -1,
            }
            try:
                r = request(s, "GET", URL, params=params)
                r.raise_for_status()
                part = _parse(r.text, topic)
            except Exception as e:
                log(f"  ЕИС   [{topic}] «{q}» стр.{page}: ОШИБКА {type(e).__name__}: {e}")
                break
            found += part
            time.sleep(1.2)
            if len(part) < per_page - 5:
                break
        docs += found
        log(f"  ЕИС   [{topic}] «{q}»: {len(found)}")
    return docs
