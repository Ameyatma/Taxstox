"""Enterprise Branding — White-label configuration per tenant.

Each tenant (CA firm) can configure their logo, colors, custom domain,
and CSS to provide a branded experience for their clients.

Traceability: C21.7 (White-Label/Branding — 0%→50%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class BrandingConfig:
    """White-label branding configuration for a tenant.

    Value object — immutable configuration. Stored as part of the Tenant aggregate.
    """

    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#1a56db"        # Default blue
    accent_color: str = "#16a34a"          # Default green
    custom_domain: str = ""                # e.g., "tax.firmname.com"
    custom_css_url: str = ""
    company_name_display: str = ""         # Override tenant name in UI
    support_email: str = ""
    support_phone: str = ""
    powered_by_visible: bool = True        # Show "Powered by TaxStox"

    @property
    def has_custom_domain(self) -> bool:
        return bool(self.custom_domain)

    @property
    def has_branding(self) -> bool:
        """True if any branding has been configured beyond defaults."""
        return bool(
            self.logo_url or self.custom_domain or self.custom_css_url
            or self.company_name_display
        )

    @staticmethod
    def default() -> BrandingConfig:
        return BrandingConfig()

    def with_logo(self, url: str) -> BrandingConfig:
        return BrandingConfig(
            logo_url=url, favicon_url=self.favicon_url,
            primary_color=self.primary_color, accent_color=self.accent_color,
            custom_domain=self.custom_domain, custom_css_url=self.custom_css_url,
            company_name_display=self.company_name_display,
            support_email=self.support_email, support_phone=self.support_phone,
            powered_by_visible=self.powered_by_visible,
        )

    def with_colors(self, primary: str, accent: str) -> BrandingConfig:
        return BrandingConfig(
            logo_url=self.logo_url, favicon_url=self.favicon_url,
            primary_color=primary, accent_color=accent,
            custom_domain=self.custom_domain, custom_css_url=self.custom_css_url,
            company_name_display=self.company_name_display,
            support_email=self.support_email, support_phone=self.support_phone,
            powered_by_visible=self.powered_by_visible,
        )

    def validate(self) -> list[str]:
        """Validate branding configuration. Returns list of errors."""
        errors: list[str] = []

        if self.primary_color and not self._is_valid_hex(self.primary_color):
            errors.append(f"Invalid primary color: {self.primary_color}")
        if self.accent_color and not self._is_valid_hex(self.accent_color):
            errors.append(f"Invalid accent color: {self.accent_color}")
        if self.custom_domain and not self._is_valid_domain(self.custom_domain):
            errors.append(f"Invalid custom domain: {self.custom_domain}")
        if self.support_email and "@" not in self.support_email:
            errors.append(f"Invalid support email: {self.support_email}")

        return errors

    @staticmethod
    def _is_valid_hex(color: str) -> bool:
        return color.startswith("#") and len(color) in (4, 7) and all(
            c in "0123456789abcdefABCDEF" for c in color[1:]
        )

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        return "." in domain and len(domain) > 3
