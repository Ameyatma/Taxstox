"""Income Tax Department provider — scrapes incometaxindia.gov.in for notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from src.providers import BaseProvider, RawUpdate, register_provider

logger = logging.getLogger(__name__)

# Income Tax Department — "What's New" and notifications pages
ITD_WHATS_NEW = "https://incometaxindia.gov.in/Pages/whats-new.aspx"
ITD_NOTIFICATIONS = "https://incometaxindia.gov.in/Pages/communications/notifications.aspx"
ITD_PRESS_RELEASES = "https://incometaxindia.gov.in/Pages/communications/press-releases.aspx"


@register_provider
class IncomeTaxProvider(BaseProvider):
    """Fetches notifications from incometaxindia.gov.in."""

    name = "incometax"
    label = "Income Tax Department"
    base_url = "https://incometaxindia.gov.in"

    async def fetch(self) -> list[RawUpdate]:
        """Scrape What's New and Notifications pages for recent updates."""
        updates: list[RawUpdate] = []
        pages = [
            ("What's New", ITD_WHATS_NEW),
            ("Notifications", ITD_NOTIFICATIONS),
        ]

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for page_name, url in pages:
                try:
                    page_updates = await self._scrape_page(client, url, page_name)
                    updates.extend(page_updates)
                    logger.info("ITD %s: fetched %d items", page_name, len(page_updates))
                except Exception as e:
                    logger.warning("ITD %s: fetch failed — %s", page_name, e)

        return updates

    async def _scrape_page(self, client: httpx.AsyncClient, url: str, page_name: str) -> list[RawUpdate]:
        """Scrape a single ITD page."""
        updates: list[RawUpdate] = []

        response = await client.get(url, headers={
            "User-Agent": "TaxStox/0.1 (tax compliance tool; contact@taxstox.com)",
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # ITD site typically has updates in tables or list elements
        # Try common patterns
        items = []
        # Pattern 1: Table rows with links
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

        # Pattern 2: List items in a "whats-new" section
        if not items:
            for li in soup.select("ul li a, .whats-new a, .notification-list a"):
                title = li.get_text(strip=True)
                href = li.get("href", "")
                if title and href:
                    if not href.startswith("http"):
                        href = self.base_url + href if href.startswith("/") else f"{self.base_url}/{href}"
                    items.append((title, "", href))

        for title, date_text, href in items:
            if not title:
                continue
            published_date = self._parse_date(date_text)
            if not self._is_recent(published_date, days=90):
                continue

            # Try to fetch the detail page for raw content
            raw_content = title
            try:
                detail_resp = await client.get(href, headers={
                    "User-Agent": "TaxStox/0.1 (tax compliance tool)",
                })
                if detail_resp.status_code == 200:
                    detail_soup = BeautifulSoup(detail_resp.text, "lxml")
                    # Remove scripts and styles
                    for tag in detail_soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    body = detail_soup.select_one("body")
                    raw_content = body.get_text(separator="\n", strip=True)[:4000] if body else title
            except Exception:
                pass  # Use title-only fallback

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
        """Parse various Indian date formats."""
        if not date_str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
            "%d %B %Y", "%d %b %Y", "%B %d, %Y",
            "%d.%m.%Y", "%d-%m-%y",
        ]
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
