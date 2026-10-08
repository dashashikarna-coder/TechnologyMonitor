"""Темы и ключевые слова из Google-таблицы -> config/topics.yaml.

    python import_topics.py            # скачать таблицу заново и пересобрать темы
    python import_topics.py --local    # взять уже скачанный config/topics_source.xlsx

Каждый лист таблицы — тема; строка «Ключевые слова» и строки под ней — слова на русском, английском, китайском.
"""
import re
import sys
from pathlib import Path

import openpyxl
import requests
import yaml

SHEET_ID = "1-2tD4AuwHF0prfgz4Lj0ocp2E2s0GmL8HWpCyxR0HN8"
ROOT = Path(__file__).parent
SRC = ROOT / "config" / "topics_source.xlsx"
OUT = ROOT / "config" / "topics.yaml"

IDS = {
    "Робототехника": ("robotics", "Робототехника"),
    "Биотехнология": ("biotech", "Биотехнологии"),
    "Радио и спутниковая связь": ("radio", "Радио- и спутниковая связь в охране"),
    "Материалы и микроэлектроника": ("materials", "Материалы и микроэлектроника"),
    "Экзоскелеты": ("exoskeletons", "Экзоскелеты"),
    "Квантовые вычисления": ("quantum", "Квантовые вычисления"),
    "Кибербезопасность": ("cyber", "Кибербезопасность"),
}
# поисковые фразы-«вопросы» и слишком общие слова дают мусор в закупках и патентах
JUNK = re.compile(r"что такое|это$|what is|definition|fundamentals|основы ", re.I)
TOO_GENERIC = {"радио", "радиосвязь", "robots", "роботы", "радиостанция", "безопасность", "security"}
CJK = re.compile(r"[\u4e00-\u9fff]")
CYR = re.compile(r"[а-яё]", re.I)

N_TENDER_QUERIES = 10  # запросов на тему в ЕИС, TED и др.
N_PATENT_WORDS = 40    # слов на тему для ФИПС (группами по 8 через OR)


def download():
    r = requests.get(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx", timeout=60)
    r.raise_for_status()
    SRC.write_bytes(r.content)
    print(f"Скачано {len(r.content) // 1024} КБ")


def sheet_keywords(ws) -> list[str]:
    rows = [[str(c).strip() if c is not None else "" for c in row] for row in ws.iter_rows(values_only=True)]
    cells, collecting = [], False
    for row in rows:
        label = row[0] if row else ""
        if label.lower().startswith("ключевые слова"):
            collecting = True
            cells += [c for c in row[1:] if c]
        elif collecting:
            if label:  # следующая подписанная строка («Источники», «География»…)
                break
            cells += [c for c in row[1:] if c]
    words = []
    for cell in cells:
        words += [w.strip(" .\u3000") for w in re.split(r"[;,，；、\n]", cell)]
    return [w for w in dict.fromkeys(words) if len(w) > 2 and not JUNK.search(w)]


def main():
    if "--local" not in sys.argv:
        download()
    wb = openpyxl.load_workbook(SRC, read_only=True)
    topics = {}
    for ws in wb.worksheets:
        key = next((k for k in IDS if ws.title.strip().startswith(k[:20])), None)
        tid, name = IDS[key] if key else (re.sub(r"\W+", "_", ws.title.lower()).strip("_"), ws.title.strip())
        kws = sheet_keywords(ws)
        if not kws:
            print(f"  лист «{ws.title}»: ключевых слов не найдено — пропущен")
            continue
        ru = [w for w in kws if CYR.search(w)]
        en = [w for w in kws if not CYR.search(w) and not CJK.search(w)]
        zh = [w for w in kws if CJK.search(w)]
        def pick(lst, n):
            out = []
            for w in lst:
                sig = tuple(x[:6].lower() for x in w.split())
                if w.lower() not in TOO_GENERIC and sig not in {tuple(x[:6].lower() for x in o.split()) for o in out}:
                    out.append(w)
            return out[:n]
        topics[tid] = {
            "name": name,
            "queries": {"ru": pick(ru, N_TENDER_QUERIES), "en": pick(en, N_TENDER_QUERIES)},
            "patent_words": pick(ru, N_PATENT_WORDS),
            "patent_words_en": pick(en, N_PATENT_WORDS),
            "keywords": kws,
        }
        print(f"  {name}: слов RU {len(ru)}, EN {len(en)}, ZH {len(zh)}")
    OUT.write_text("# Сгенерировано import_topics.py из Google-таблицы — правьте таблицу, а не этот файл\n"
                   + yaml.safe_dump(topics, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    print(f"Тем: {len(topics)} -> {OUT}")


if __name__ == "__main__":
    main()
