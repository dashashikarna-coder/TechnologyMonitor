from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
_pool = ThreadPoolExecutor(max_workers=4)


def session(**headers) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8", **headers})
    # 429 не повторяем: сервер может попросить ждать часами (Retry-After), источник просто пропускается
    retry = Retry(total=2, backoff_factor=1.5, status_forcelist=[500, 502, 504], allowed_methods=None,
                  respect_retry_after_header=False)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def _do(s, method, url, kw):
    try:
        return s.request(method, url, **kw)
    except requests.exceptions.SSLError:
        # в локальной сети часть сайтов идёт через чужую цепочку сертификатов
        return s.request(method, url, verify=False, **kw)


def request(s: requests.Session, method: str, url: str, **kw) -> requests.Response:
    """Запрос с жёстким общим лимитом времени: медленно «капающее» соединение не повесит весь сбор."""
    t = kw.pop("timeout", 40)
    kw["timeout"] = (10, t)
    try:
        return _pool.submit(_do, s, method, url, kw).result(timeout=t * 3 + 20)
    except FutureTimeout:
        raise TimeoutError(f"нет ответа за {t * 3 + 20} с")
