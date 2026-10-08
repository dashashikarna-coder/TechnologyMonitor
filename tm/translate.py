"""Перевод на русский через публичный Google Translate (без ключа). Русский текст не трогает."""
import re
from concurrent.futures import ThreadPoolExecutor

import requests

URL = "https://translate.googleapis.com/translate_a/single"
LETTER_RE = re.compile(r"[^\W\d_]")
CYR_RE = re.compile(r"[а-яё]", re.I)


def is_russian(text: str) -> bool:
    if re.search(r"[іїєґІЇЄҐўЎ]", text or ""):  # украинский / белорусский
        return False
    letters = LETTER_RE.findall(text or "")
    return bool(letters) and sum(bool(CYR_RE.match(c)) for c in letters) / len(letters) > 0.5


def _batch(texts: list[str]) -> list[str]:
    r = requests.get(URL, params={"client": "gtx", "sl": "auto", "tl": "ru", "dt": "t", "q": "\n".join(texts)}, timeout=30)
    r.raise_for_status()
    out = "".join(seg[0] for seg in r.json()[0] if seg and seg[0]).split("\n")
    if len(out) != len(texts):
        raise ValueError("batch split mismatch")
    return [o.strip() for o in out]


def translate(texts: list[str], workers: int = 4) -> list[str]:
    texts = [re.sub(r"\s+", " ", t or "").strip() for t in texts]
    result = list(texts)
    todo = [i for i, t in enumerate(texts) if t and not is_russian(t)]
    batches, cur, size = [], [], 0
    for i in todo:
        if cur and size + len(texts[i]) > 3500:
            batches.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += len(texts[i]) + 1
    if cur:
        batches.append(cur)

    def run(batch):
        try:
            return batch, _batch([texts[i] for i in batch])
        except Exception:
            out = []
            for i in batch:
                try:
                    out.append(_batch([texts[i]])[0])
                except Exception:
                    out.append(texts[i])
            return batch, out

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for batch, tr in pool.map(run, batches):
            for i, t in zip(batch, tr):
                result[i] = t
    return result
