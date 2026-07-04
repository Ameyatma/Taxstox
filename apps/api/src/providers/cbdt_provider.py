"""CBDT (Central Board of Direct Taxes) provider — circulars and notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from src.providers import BaseProvider, RawUpdate, register_provider

logger = logging.getLogger(__name__)

CBDT_CIRCULARS = "https://incometaxindia.gov.in/Pages/communications/circulars.aspx"
CBDT_NOTIFICATIONS = "https://incometaxindia.gov.in/Pages/communications/notifications.aspx"


@register_provider
class CBDTProvider(BaseProvider):
    """Fetches CBDT circulars and notifications from incometaxindia.gov.in."""

    name = "cbdt"
    label = "Central Board of Direct Taxes"
    base_url = "https://incometaxindia.gov.in"

    async def fetch(self) -> list[RawUpdate]:
        """Scrape CBDT circulars and notifications."""
        updates: list[RawUpdate] = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for label, url in [("Circulars", CBDT_CIRCULARS), ("Notifications", CBDT_NOTIFICATIONS)]:
                try:
                    items = await self._scrape_page(client, url)
                    updates.extend(items)
                    logger.info("CBDT %s: fetched %d items", label, len(items))
                except Exception as e:
                    logger.warning("CBDT %s: fetch failed — %s", label, e)

        return updates

    async def _scrape_page(self, client: httpx.AsyncClient, url: str) -> list[RawUpdate]:
        """Scrape a CBDT listing page."""
        updates: list[RawUpdate] = []

        response = await client.get(url, headers={
            "User-Agent": "TaxStox/0.1 (tax compliance tool; contact@taxstox.com)",
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        items = []

        # CBDT pages typically use tables
        for row in soup.select("table tr"):
            link = row.select_one("a")
            if link and link.get("href"):
                cells = row.select("td")
                title = link.get_text(strip=True)
                date_text = cells[-1].get_text(strip=True) if len(cells) > 1 else ""
                href = link["href"]
                if not href.startswith("http"):
                    href = self.base_url + href if href.startswith("/") else f"{self.base_url}/{href}"
                items.append((title, date_text, href))

        # Fallback: list items
        if not items:
            for link in soup.select("a[href*='circular'], a[href*='notification'], ul li a"):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if title and href and len(title) > 20:  # meaningful titles only
                    if not href.startswith("http"):
                        href = self.base_url + href if href.startswith("/") else f"{self.base_url}/{href}"
                    items.append((title, "", href))

        for title, date_text, href in items[:20]:  # Cap at 20 per page
            published_date = self._parse_date(date_text)
            if not self._is_recent(published_date, days=90):
                continue

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
