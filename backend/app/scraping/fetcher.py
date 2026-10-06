"""Polite HTTP fetching for the scraping prototype.

Rules (same for every source):
  - an identified User-Agent with a contact address;
  - at least DELAY seconds between two requests to the same host;
  - retries with exponential back-off on network errors, 429 and 5xx;
  - a timeout on every request;
  - a hard cap on pages fetched per run, and a separate cap on PDFs.
The clock and sleep are injectable so the limits can be tested without waiting.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests

USER_AGENT = "LegalEase-FYP/0.1 (+research prototype; contact: i228795@nu.edu.pk)"
DELAY = 2.0
TIMEOUT = 30
RETRIES = 3
BACKOFF = 2.0  # seconds; doubled on each retry


class LimitReachedError(Exception):
    """The per-run page or PDF cap was hit; the run stops fetching."""


class DisallowedError(Exception):
    """robots.txt doesn't allow our User-Agent to fetch this URL."""


@dataclass
class FetchResult:
    url: str
    status: int
    content: bytes
    content_type: str


@dataclass
class Fetcher:
    max_pages: int = 50
    max_pdfs: int = 10
    delay: float = DELAY
    timeout: float = TIMEOUT
    retries: int = RETRIES
    backoff: float = BACKOFF
    session: requests.Session | None = None
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    pages: int = 0
    pdfs: int = 0
    requests_made: int = 0
    _last: dict[str, float] = field(default_factory=dict)
    _robots: dict[str, object] = field(default_factory=dict)
    host_delay: dict[str, float] = field(default_factory=dict)
    obey_robots: bool = True

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def _wait_for(self, host: str) -> None:
        delay = max(self.delay, self.host_delay.get(host, 0.0))
        last = self._last.get(host)
        if last is not None:
            gap = self.clock() - last
            if gap < delay:
                self.sleep(delay - gap)
        self._last[host] = self.clock()

    def allowed(self, url: str) -> bool:
        """robots.txt check, cached per host (RFC 9309): a 4xx robots.txt
        means everything is allowed; 5xx or no answer means stay off. A
        Crawl-delay longer than our own delay is honoured."""
        import urllib.robotparser
        parts = urlparse(url)
        host = parts.netloc
        rp = self._robots.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            self._wait_for(host)
            self.requests_made += 1
            try:
                r = self.session.get(f"{parts.scheme}://{host}/robots.txt", timeout=self.timeout)
                if r.status_code >= 500:
                    rp.disallow_all = True
                elif r.status_code >= 400 or "html" in r.headers.get("content-type", ""):
                    rp.parse([])
                else:
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp.disallow_all = True
            cd = rp.crawl_delay(USER_AGENT)
            if cd:
                self.host_delay[host] = float(cd)
            self._robots[host] = rp
        return rp.can_fetch(USER_AGENT, url)

    def get(self, url: str, *, pdf: bool = False) -> FetchResult:
        """One page (or PDF). Raises LimitReachedError before going over a cap, and
        requests.RequestException once the retries are used up."""
        if self.obey_robots and not self.allowed(url):
            raise DisallowedError(f"robots.txt disallows {url}")
        if pdf and self.pdfs >= self.max_pdfs:
            raise LimitReachedError(f"PDF cap of {self.max_pdfs} reached")
        if self.pages >= self.max_pages:
            raise LimitReachedError(f"page cap of {self.max_pages} reached")
        self.pages += 1
        if pdf:
            self.pdfs += 1
        host = urlparse(url).netloc
        wait = self.backoff
        for attempt in range(self.retries + 1):
            self._wait_for(host)
            self.requests_made += 1
            try:
                r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
                return FetchResult(url=r.url, status=r.status_code, content=r.content,
                                   content_type=r.headers.get("content-type", ""))
            except requests.RequestException:
                if attempt == self.retries:
                    raise
                self.sleep(wait)
                wait *= 2
        raise AssertionError("unreachable")
