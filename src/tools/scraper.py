import httpx
from langchain_community.document_loaders import WebBaseLoader


class WebScraper:
    """Optional webpage scraper for deeper content extraction."""

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    def scrape_url(self, url: str) -> str:
        """Scrape a URL and return its text content."""
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            if docs:
                return docs[0].page_content[:10000]
            return ""
        except Exception:
            return self._fallback_scrape(url)

    def _fallback_scrape(self, url: str) -> str:
        try:
            resp = httpx.get(url, timeout=self._timeout, follow_redirects=True)
            resp.raise_for_status()
            return resp.text[:10000]
        except Exception:
            return ""

    def scrape_multiple(self, urls: list[str]) -> dict[str, str]:
        return {url: self.scrape_url(url) for url in urls}
