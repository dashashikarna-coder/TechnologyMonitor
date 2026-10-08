@echo off
rem Обновление данных: темы из Google-таблицы + сбор тендеров и патентов. Запускается Планировщиком раз в 3 дня.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONWARNINGS=ignore
echo ==== %date% %time% ==== >> data\update.log
".venv\Scripts\python.exe" import_topics.py >> data\update.log 2>&1
".venv\Scripts\python.exe" collect.py >> data\update.log 2>&1
