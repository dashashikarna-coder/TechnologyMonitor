"""Закупки Евросоюза: официальный API TED (ted.europa.eu), без ключа."""
from datetime import date, timedelta

from ..http import request, session

URL = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = [
    "publication-number", "notice-title", "notice-type", "buyer-name", "buyer-country", "publication-date",
    "deadline-receipt-tender-date-lot", "total-value", "total-value-cur", "classification-cpv",
]
NOTICE_TYPES = {
    "cn": "Объявление о закупке", "can": "Итоги закупки", "pin": "Предварительное уведомление",
    "veat": "Намерение заключить контракт", "pmc": "Изменение", "corr": "Исправление",
}
LANG_PREF = ["eng", "fra", "deu"]


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _lang_text(value) -> str:
    if isinstance(value, dict):
        for lang in LANG_PREF:
            if value.get(lang):
                return str(_first(value[lang]))
        return str(_first(next(iter(value.values()), ""))) if value else ""
    return str(_first(value) or "")


def _price(value) -> float | None:
    try:
        price = float(_first(value))
    except (TypeError, ValueError):
        return None
    return price if price > 1 else None  # в итогах TED часто ставят 1 € вместо реальной суммы


def _notice_type(code: str) -> str:
    code = (code or "").lower()
    for prefix, name in NOTICE_TYPES.items():
        if code.startswith(prefix):
            return name
    return code


def collect(queries: list[tuple[str, str]], days: int = 1825, limit: int = 100, log=print) -> list[dict]:
    s = session(Accept="application/json")
    since = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
    docs = []
    for topic, q in queries:
        payload = {
            "query": f'FT~"{q}" AND publication-date>={since} SORT BY publication-date DESC',
            "fields": FIELDS, "limit": limit, "page": 1,
            "paginationMode": "PAGE_NUMBER", "checkQuerySyntax": False,
        }
        try:
            r = request(s, "POST", URL, json=payload, timeout=60)
            r.raise_for_status()
            notices = r.json().get("notices") or []
            for n in notices:
                number = n.get("publication-number")
                title = _lang_text(n.get("notice-title"))
                if not number or not title:
                    continue
                # «Румыния – Сонары – <предмет>»: оставляем предмет закупки
                subject = title.split(" – ", 2)[-1] if title.count(" – ") >= 2 else title
                docs.append({
                    "type": "tender",
                    "source": "TED (Евросоюз)",
                    "source_id": number,
                    "url": f"https://ted.europa.eu/en/notice/-/detail/{number}",
                    "title": subject,
                    "summary": title,
                    "date": (n.get("publication-date") or "")[:10] or None,
                    "country_code": _first(n.get("buyer-country")),
                    "customer": _lang_text(n.get("buyer-name")),
                    "price": _price(n.get("total-value")),
                    "currency": _first(n.get("total-value-cur")) or "EUR",
                    "deadline": (_first(n.get("deadline-receipt-tender-date-lot")) or "")[:10] or None,
                    "status": _notice_type(n.get("notice-type")),
                    "law": "TED",
                    "procedure": "",
                    "cpv": list(dict.fromkeys(n.get("classification-cpv") or []))[:5],
                    "query_topic": topic,
                })
            log(f"  TED   [{topic}] «{q}»: {len(notices)}")
        except Exception as e:
            log(f"  TED   [{topic}] «{q}»: ОШИБКА {type(e).__name__}: {e}")
    return docs
