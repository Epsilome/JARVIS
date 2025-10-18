# assistant_app/adapters/persistence/robots.py
from urllib.parse import urlparse
from urllib import robotparser
from functools import lru_cache

DEFAULT_UA = "JarvisPriceChecker/1.0 (+contact@example.com)"

@lru_cache(maxsize=64)
def _get_rp(base: str) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    rp.set_url(base.rstrip("/") + "/robots.txt")
    try:
        rp.read()
    except Exception:
        pass
    return rp

def robots_allows(url: str, user_agent: str = DEFAULT_UA) -> bool:
    o = urlparse(url)
    base = f"{o.scheme}://{o.netloc}"
    return _get_rp(base).can_fetch(user_agent, url)
