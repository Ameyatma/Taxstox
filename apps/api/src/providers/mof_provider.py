"""Ministry of Finance provider — Budget and Finance Act updates."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from src.providers import BaseProvider, RawUpdate, register_provider

logger = logging.getLogger(__name__)

MOF_WHATSNEW = "https://finmin.gov.in/whats-new"
MOF_PRESS = "https://finmin.gov.in/press-releases"
MOF_BUDGET = "https://www.indiabudget.gov.in"


@register_provider
class MoFProvider(BaseProvider):
    """Fetches Ministry of Finance announcements relevant to tax."""

    name = "mof"
    label = "Ministry of Finance"
    base_url = "https://finmin.gov.in"

    # Keywords to filter for direct/indirect tax relevance
    TAX_KEYWORDS = [
        "income tax", "direct tax", "indirect tax", "gst", "customs",
        "cbdt", "cbec", "finance bill", "taxation", "budget",
        "finance act", "appropriation", "revenue",
    ]

    async def fetch(self) -> list[RawUpdate]:
        """Scrape MoF for recent tax-related announcements."""
        updates: list[RawUpdate] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for label, url in [("What's New", MOF_WHATSNEW), ("Press Releases", MOF_PRESS)]:
                try:
                    items = await self._scrape_page(client, url)
                    # Filter for tax relevance
                    tax_items = [
                        item for item in items
                        if any(kw in (item.title + " " + item.raw_content).lower()
                               for kw in self.TAX_KEYWORDS)
                    ]
                    updates.extend(tax_items)
                    logger.info("MoF %s: fetched %d tax-relevant items (from %d total)", label, len(tax_items), len(items))
                except Exception as e:
                    logger.warning("MoF %s: fetch failed — %s", label, e)

        return updates

    async def _scrape_page(self, client: httpx.AsyncClient, url: str) -> list[RawUpdate]:
        """Scrape an MoF listing page."""
        updates: list[RawUpdate] = []

        try:
            response = await client.get(url, headers={
                "User-Agent": "TaxStox/0.1 (tax compliance tool; contact@taxstox.com)",
            })
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("MoF: could not reach %s", url)
            return updates

        soup = BeautifulSoup(response.text, "lxml")
        items = []

        # MoF site typically uses lists or tables
        for row in soup.select("table tr, ul li, .news-item, .press-release"):
            link = row.select_one("a")
            if link and link.get("href"):
                title = link.get_text(strip=True)
                href = link["href"]
                if not href.startswith("http"):
                    href = self.base_url + href if href.startswith("/") else f"{self.base_url}/{href}"

                # Try to find date
                date_el = row.select_one("time, .date, .published-date, span.date")
                date_text = date_el.get_text(strip=True) if date_el else ""
                published_date = self._parse_date(date_text)

                if title and self._is_recent(published_date, days=90):
                    items.append((title, published_date, href))

        for title, published_date, href in items[:15]:
            raw_content = title
            try:
                detail_resp = await client.get(href, headers={
                    "User-Agent": "TaxStox/0.1 (tax compliance tool)",
                })
                if detail_resp.status_code == 200:
                    detail_soup = BeautifulSoup(detail_resp.text, "lxml")
                    for tag in detail_soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    body = detail_soup.select_one("body")
                    raw_content = body.get_text(separator="\n", strip=True)[:4000] if body else title
            except Exception:
                pass

            updates.append(RawUpdate(
                title=title,
                raw_content=raw_content[:4000],
                url=href,
                published_date=published_date,
                source=self.name,
            ))

        return updates

    @staticmethod
    def _parse_date(date_str: str) -> str:
        if not date_str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _is_recent(date_str: str, days: int = 90) -> bool:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - d).days <= days
        except ValueError:
            return True
