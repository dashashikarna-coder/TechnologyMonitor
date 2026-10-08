"""Темы из config/topics.yaml и отнесение документов к темам по ключевым словам."""
import re
from pathlib import Path

import yaml

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CYR_RE = re.compile(r"[а-яё]", re.I)
CYR_ENDING_RE = re.compile(r"[аеёиийоуыьэюя]{1,2}$", re.I)


def _word(word: str) -> str:
    if sum(ch.isupper() for ch in word) >= 2:  # аббревиатуры (БПЛА, UAV, СКУД) — строго с учётом регистра
        return rf"(?-i:{re.escape(word)})s?(?!\w)"
    if CYR_RE.search(word):
        stem = CYR_ENDING_RE.sub("", word)
        if len(word) >= 6 and len(stem) >= 5:
            return re.escape(stem) + r"\w*"
        return re.escape(word) + r"\w{0,3}"
    return re.escape(word) + r"(?:s|es|ed|ing)?"


def _pattern(kw: str) -> str:
    if CJK_RE.search(kw):
        return re.escape(kw)
    body = r"[\s\-]+".join(_word(w) for w in re.split(r"[\s\-]+", kw.strip()) if w)
    return rf"(?<!\w){body}"


class Matcher:
    def __init__(self, keywords: list[str]):
        self.keywords = [k for k in dict.fromkeys(str(k).strip() for k in keywords or []) if k]
        parts = [f"(?P<k{i}>{_pattern(k)})" for i, k in enumerate(self.keywords)]
        self.regex = re.compile("|".join(parts), re.I) if parts else None

    def find(self, text: str) -> list[str]:
        if not self.regex or not text:
            return []
        return list(dict.fromkeys(self.keywords[int(m.lastgroup[1:])] for m in self.regex.finditer(text)))


class Topics:
    def __init__(self, path: Path):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        flt_path = path.parent / "filters.yaml"
        flt = yaml.safe_load(flt_path.read_text(encoding="utf-8")) if flt_path.exists() else {}
        ignore = {str(k).lower() for k in flt.get("ignore_keywords") or []}
        self.tender_exclude = re.compile("|".join(flt.get("tender_exclude") or ["(?!x)x"]), re.I)
        self.items = [{"id": tid, **cfg} for tid, cfg in raw.items()]
        self._kw = {t["id"]: Matcher([k for k in t.get("keywords") or [] if str(k).lower() not in ignore])
                    for t in self.items}
        self._ex = {t["id"]: Matcher(t.get("exclude")) for t in self.items}

    def queries(self, lang: str) -> list[tuple[str, str]]:
        return [(t["id"], q) for t in self.items for q in (t.get("queries") or {}).get(lang, [])]

    def patent_queries(self, lang: str = "ru", group: int = 8) -> list[tuple[str, list[str]]]:
        out = []
        for t in self.items:
            key = "patent_words" if lang == "ru" else f"patent_words_{lang}"
            words = t.get(key) or (t.get("queries") or {}).get(lang, [])
            out += [(t["id"], words[i:i + group]) for i in range(0, len(words), group)]
        return out

    def classify(self, title: str, body: str = "", kind: str = "tender") -> tuple[list[str], list[str]]:
        """Строгий отбор: тендер — слово темы в названии; патент — в названии или ≥2 разных слова в реферате."""
        if kind == "tender" and self.tender_exclude.search(title):
            return [], []
        topics, keywords = [], []
        for t in self.items:
            m = self._kw[t["id"]]
            hits = m.find(title)
            if not hits and kind == "patent":
                body_hits = m.find(body)
                hits = body_hits if len(body_hits) >= 2 else []
            if hits and not self._ex[t["id"]].find(f"{title} {body}"):
                topics.append(t["id"])
                keywords += hits
        return topics, list(dict.fromkeys(keywords))
