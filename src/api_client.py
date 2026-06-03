"""Generic REST API client with retries, rate limiting, pagination."""
import time
import json
import logging
from typing import Generator, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, calls_per_second: int):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
        self.last_call = 0.0

    def wait(self):
        now = time.monotonic()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.monotonic()

class ApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        backoff: float = 5.0,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff = backoff
        self.rate_limiter = rate_limiter or RateLimiter(calls_per_second=10)
        self.session_headers = {
            "User-Agent": "DataSync/1.0",
            "Accept": "application/json",
        }
        if api_key:
            self.session_headers["Authorization"] = f"Bearer {api_key}"

    def _request(self, method: str, path: str, params: Optional[dict] = None, body: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            q = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{q}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self.session_headers, method=method)
        for attempt in range(self.max_retries):
            try:
                self.rate_limiter.wait()
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After", str(int(self.backoff)))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(int(retry_after))
                elif e.code >= 500 and attempt < self.max_retries - 1:
                    wait = self.backoff * (2 ** attempt)
                    logger.warning(f"Server error {e.code}, retry in {wait}s")
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait = self.backoff * (2 ** attempt)
                    logger.warning(f"Request failed: {e}, retry in {wait}s")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("Max retries exceeded")

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        return self._request("GET", path, params=params)

    def paginate(self, path: str, params: Optional[dict] = None, page_size: int = 100) -> Generator[list, None, None]:
        params = dict(params or {})
        params["limit"] = page_size
        offset = 0
        while True:
            params["offset"] = offset
            result = self.get(path, params=params)
            items = result.get("data", result.get("results", result.get("items", [])))
            if not items:
                break
            yield items
            total = result.get("total", result.get("count", len(items)))
            offset += len(items)
            if offset >= total:
                break

def create_client(base_url: str, api_key: str, rate_limit: int = 10) -> ApiClient:
    return ApiClient(base_url, api_key, rate_limiter=RateLimiter(calls_per_second=rate_limit))