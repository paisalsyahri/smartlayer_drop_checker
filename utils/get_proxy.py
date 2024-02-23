from random import choice

from better_proxy import Proxy

with open(file='data/proxies.txt',
          mode='r',
          encoding='utf-8-sig') as file:
    proxies: list[str] = [Proxy.from_str(proxy=row.strip().rstrip()).as_url for row in file if row.strip().rstrip()]


def get_proxy() -> str | None:
    return choice(proxies) if proxies else None
