@echo off
rem Обновление данных: темы из Google-таблицы + сбор тендеров и патентов. Запускается Планировщиком раз в 3 дня.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONWARNINGS=ignore
set "PATH=%PATH%;C:\Program Files\Git\cmd"

rem VPN-прокси (127.0.0.1:10809): если клиент не запущен — отключаем системный прокси,
rem иначе Python падает на Google Sheets / источниках, и дата на сайте не обновляется.
powershell -NoProfile -Command "try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',10809); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  set HTTP_PROXY=
  set HTTPS_PROXY=
  set ALL_PROXY=
  set NO_PROXY=*
  set PROXY_ON=0
) else (
  set HTTP_PROXY=http://127.0.0.1:10809
  set HTTPS_PROXY=http://127.0.0.1:10809
  set PROXY_ON=1
)

echo ==== %date% %time% proxy=%PROXY_ON% ==== >> data\update.log
".venv\Scripts\python.exe" import_topics.py >> data\update.log 2>&1
".venv\Scripts\python.exe" collect.py >> data\update.log 2>&1

rem На GitHub Pages push обычно нужен только при включённом VPN (GitHub с этого ПК без прокси недоступен).
if "%PROXY_ON%"=="1" (
  git add -A >> data\update.log 2>&1
  git commit -q -m "Обновление данных" >> data\update.log 2>&1
  git push -q >> data\update.log 2>&1
) else (
  echo git push пропущен: VPN/прокси выключен >> data\update.log
)
