"""Enterprise SSO — SAML/OIDC configuration per tenant.

Each CA firm can configure their own identity provider for
enterprise single sign-on. Domain verification ensures only
verified domains can use SSO.

Traceability: C21.6 (Enterprise SSO — 30%→60%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SSOProviderType(str, Enum):
    SAML = "saml"
    OIDC = "oidc"


class SSOStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True)
class DomainVerification:
    """Domain ownership verification record. Value object."""

    domain: str
    verification_token: str
    verified_at: str = ""
    verified: bool = False

    def verify(self, token: str) -> DomainVerification:
        """Verify domain ownership. Returns new instance with updated state."""
        if token == self.verification_token:
            return DomainVerification(
                domain=self.domain,
                verification_token=self.verification_token,
                verified_at=datetime.now(timezone.utc).isoformat(),
                verified=True,
            )
        return self

    @staticmethod
    def create(domain: str) -> DomainVerification:
        import secrets
        return DomainVerification(
            domain=domain,
            verification_token=f"taxstox-verify-{secrets.token_hex(16)}",
        )


@dataclass(frozen=True)
class SAMLConfig:
    """SAML 2.0 identity provider configuration."""

    entity_id: str = ""                         # IdP entity ID
    sso_url: str = ""                           # Single sign-on URL
    slo_url: str = ""                           # Single logout URL (optional)
    x509_certificate: str = ""                  # IdP signing certificate
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    request_signing: bool = True
    want_assertions_signed: bool = True

    @property
    def is_configured(self) -> bool:
        return bool(self.entity_id and self.sso_url)


@dataclass(frozen=True)
class OIDCConfig:
    """OpenID Connect identity provider configuration."""

    issuer_url: str = ""                        # IdP issuer URL
    client_id: str = ""
    client_secret: str = ""                     # Stored encrypted
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    jwks_uri: str = ""
    scopes: str = "openid profile email"

    @property
    def is_configured(self) -> bool:
        return bool(self.issuer_url and self.client_id)


@dataclass
class SSOConfig:
    """SSO configuration for a tenant. Entity within Tenant aggregate.

    One tenant can have one SSO configuration (SAML or OIDC).
    """

    config_id: UUID
    tenant_id: UUID
    provider_type: SSOProviderType
    status: SSOStatus = SSOStatus.PENDING_VERIFICATION
    saml: SAMLConfig | None = None
    oidc: OIDCConfig | None = None
    domains: list[DomainVerification] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @staticmethod
    def create_saml(tenant_id: UUID, saml: SAMLConfig) -> SSOConfig:
        return SSOConfig(
            config_id=uuid4(), tenant_id=tenant_id,
            provider_type=SSOProviderType.SAML, saml=saml,
        )

    @staticmethod
    def create_oidc(tenant_id: UUID, oidc: OIDCConfig) -> SSOConfig:
        return SSOConfig(
            config_id=uuid4(), tenant_id=tenant_id,
            provider_type=SSOProviderType.OIDC, oidc=oidc,
        )

    def add_domain(self, domain: str) -> DomainVerification:
        """Register a domain for SSO. Returns verification record."""
        verification = DomainVerification.create(domain)
        self.domains.append(verification)
        self._touch()
        return verification

    def verify_domain(self, domain: str, token: str) -> bool:
        """Verify a registered domain."""
        for i, dv in enumerate(self.domains):
            if dv.domain == domain and not dv.verified:
                self.domains[i] = dv.verify(token)
                if self.domains[i].verified:
                    self.status = SSOStatus.ACTIVE
                    self._touch()
                    return True
        return False

    @property
    def verified_domains(self) -> list[str]:
        return [dv.domain for dv in self.domains if dv.verified]

    @property
    def is_active(self) -> bool:
        return (self.status == SSOStatus.ACTIVE
                and (self.saml.is_configured if self.saml else False
                     or self.oidc.is_configured if self.oidc else False))

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
