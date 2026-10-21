"""예의 있는 수집 요청: robots.txt 확인 · 요청 간격 · 3회 재시도(지수 백오프)"""
import logging
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class CollectError(Exception):
    pass


class PoliteSession:
    def __init__(self, user_agent: str, interval_sec: float = 3.0, retries: int = 3, timeout: float = 10.0):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = user_agent
        self.ua, self.interval, self.retries, self.timeout = user_agent, interval_sec, retries, timeout
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last = 0.0

    def allowed(self, url: str) -> bool:
        p = urlparse(url)
        root = f"{p.scheme}://{p.netloc}"
        if root not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(f"{root}/robots.txt", timeout=self.timeout)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse(["User-agent: *", "Disallow: /"])  # robots.txt를 확인할 수 없으면 수집하지 않는다
            self._robots[root] = rp
        return self._robots[root].can_fetch(self.ua, url)

    def _wait(self) -> None:
        gap = self.interval - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()

    def fetch(self, url: str) -> BeautifulSoup:
        if not self.allowed(url):
            raise CollectError(f"robots.txt가 허용하지 않는 경로: {url}")
        for attempt in range(self.retries):
            self._wait()
            try:
                r = self.s.get(url, timeout=self.timeout)
                r.raise_for_status()
                return BeautifulSoup(r.text, "html.parser")
            except requests.RequestException as exc:
                log.warning("요청 실패(%s/%s) %s: %s", attempt + 1, self.retries, url, exc)
                time.sleep(3 * 2 ** attempt)
        raise CollectError(f"요청 실패: {url}")
