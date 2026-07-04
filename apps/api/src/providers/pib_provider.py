"""PIB (Press Information Bureau) provider — fetches Ministry of Finance releases via RSS."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from xml.etree import ElementTree

import httpx

from src.providers import BaseProvider, RawUpdate, register_provider

logger = logging.getLogger(__name__)

PIB_RSS_URL = "https://pib.gov.in/RssSource.aspx"
PIB_FINANCE_FEED = "https://www.pib.gov.in/PressReleseArchive.aspx?MinistryID=8"  # MoF releases

# Finance-related keywords to filter relevant items
FINANCE_KEYWORDS = [
    "income tax", "itr", "tds", "tcs", "gst", "customs", "cbdt",
    "finance act", "budget", "taxpayer", "filing", "pan", "aadhaar",
    "direct tax", "indirect tax", "advance tax", "deduction",
    "exemption", "section 80", "capital gain", "return filing",
    "central board of direct taxes", "ministry of finance",
    "tax regime", "assessment year", "form 16", "ais", "26as",
    "refund", "e-verification", "e-filing", "compliance",
]


@register_provider
class PIBProvider(BaseProvider):
    """Fetches tax-related press releases from the Press Information Bureau."""

    name = "pib"
    label = "Press Information Bureau"
    base_url = "https://pib.gov.in"

    async def fetch(self) -> list[RawUpdate]:
        """Fetch and filter MoF/tax-related items from PIB RSS feed."""
        updates: list[RawUpdate] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(PIB_RSS_URL)
                response.raise_for_status()

            root = ElementTree.fromstring(response.text)
            # PIB RSS has items in channel/item
            items = root.findall(".//item")

            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                pubdate_el = item.find("pubDate")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                pub_date_str = pubdate_el.text.strip() if pubdate_el is not None and pubdate_el.text else ""

                if not title or not link:
                    continue

                # Check if finance/tax related
                combined = f"{title.lower()} {description.lower()}"
                if not any(kw in combined for kw in FINANCE_KEYWORDS):
                    continue

                # Parse date
                published_date = self._parse_date(pub_date_str)

                # Only include items from last 60 days
                if not self._is_recent(published_date, days=60):
                    continue

                updates.append(RawUpdate(
                    title=title,
                    raw_content=f"{title}\n\n{description}",
                    url=link,
                    published_date=published_date,
                    source=self.name,
                ))

            logger.info("PIB: fetched %d relevant items (filtered from %d total)", len(updates), len(items))
        except Exception as e:
            logger.warning("PIB: fetch failed — %s", e)

        return updates

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Parse various date formats to ISO YYYY-MM-DD."""
        if not date_str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d %B %Y",
            "%B %d, %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Fallback: return today
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _is_recent(date_str: str, days: int = 60) -> bool:
        """Check if a date string is within the given number of days from today."""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - d).days <= days
        except ValueError:
            return True  # Include if we can't parse the date
