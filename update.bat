@echo off
rem Обновление данных: темы из Google-таблицы + сбор тендеров и патентов. Запускается Планировщиком раз в 3 дня.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONWARNINGS=ignore
echo ==== %date% %time% ==== >> data\update.log
".venv\Scripts\python.exe" import_topics.py >> data\update.log 2>&1
".venv\Scripts\python.exe" collect.py >> data\update.log 2>&1
rem Отправка свежих данных на GitHub: сайт на GitHub Pages обновляется сам. Git ходит через прокси VPN-клиента.
set "PATH=%PATH%;C:\Program Files\Git\cmd"
set HTTPS_PROXY=http://127.0.0.1:10809
git add -A >> data\update.log 2>&1
git commit -q -m "Обновление данных" >> data\update.log 2>&1
git push -q >> data\update.log 2>&1
