"""SSO Infrastructure Adapters — SAML and OIDC provider integrations.

Implements the SSO domain interfaces with provider-specific logic.
Framework-aware — uses HTTP clients for IdP communication.

For production: SAML via python3-saml, OIDC via authlib.
Current: Stub implementations with clear production migration paths.

Traceability: C21.6 (Enterprise SSO — 30%→60%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domain.enterprise.sso import (
    SSOConfig,
    SSOProviderType,
    SAMLConfig,
    OIDCConfig,
    DomainVerification,
)


@dataclass
class SSOTestResult:
    """Result of testing an SSO connection."""
    success: bool
    provider_type: SSOProviderType
    message: str = ""
    redirect_url: str = ""
    error_details: str = ""


class SAMLAdapter:
    """SAML 2.0 Service Provider adapter.

    Production: Replace with python3-saml (pysaml2) for full SP implementation.
    """

    @staticmethod
    def validate_config(config: SAMLConfig) -> list[str]:
        """Validate SAML configuration. Returns list of errors."""
        errors: list[str] = []
        if not config.entity_id:
            errors.append("IdP Entity ID is required")
        if not config.sso_url:
            errors.append("SSO URL is required")
        if not config.x509_certificate:
            errors.append("X.509 signing certificate is required")
        elif not config.x509_certificate.startswith("-----BEGIN CERTIFICATE-----"):
            errors.append("X.509 certificate must be in PEM format")
        return errors

    @staticmethod
    def generate_sp_metadata(tenant_slug: str, acs_url: str) -> str:
        """Generate SAML SP metadata XML for the tenant.

        Args:
            tenant_slug: Tenant's URL slug
            acs_url: Assertion Consumer Service URL

        Returns:
            SP metadata XML string
        """
        import uuid
        entity_id = f"https://taxstox.com/sp/{tenant_slug}"

        return f"""<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{entity_id}">
  <md:SPSSODescriptor AuthnRequestsSigned="true"
      WantAssertionsSigned="true"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{acs_url}" index="1"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""

    @staticmethod
    def test_connection(config: SAMLConfig) -> SSOTestResult:
        """Test SAML connection to IdP.

        Production: Perform actual SAML AuthnRequest and validate response.
        """
        errors = SAMLAdapter.validate_config(config)
        if errors:
            return SSOTestResult(
                success=False, provider_type=SSOProviderType.SAML,
                message="SAML configuration invalid",
                error_details="; ".join(errors),
            )
        return SSOTestResult(
            success=True, provider_type=SSOProviderType.SAML,
            message="SAML configuration valid — ready for connection testing",
            redirect_url=config.sso_url,
        )


class OIDCAdapter:
    """OpenID Connect Relying Party adapter.

    Production: Replace with authlib for full OIDC client implementation.
    """

    @staticmethod
    def validate_config(config: OIDCConfig) -> list[str]:
        """Validate OIDC configuration. Returns list of errors."""
        errors: list[str] = []
        if not config.issuer_url:
            errors.append("Issuer URL is required")
        if not config.client_id:
            errors.append("Client ID is required")
        if not config.client_secret:
            errors.append("Client secret is required")
        return errors

    @staticmethod
    def discover_provider(issuer_url: str) -> dict | None:
        """Discover OIDC provider metadata from .well-known endpoint.

        Production: Perform actual HTTP GET to {issuer}/.well-known/openid-configuration.

        Returns:
            Provider metadata dict or None if discovery fails
        """
        # Stub: In production, call {issuer_url}/.well-known/openid-configuration
        return {
            "issuer": issuer_url,
            "authorization_endpoint": f"{issuer_url}/authorize",
            "token_endpoint": f"{issuer_url}/token",
            "userinfo_endpoint": f"{issuer_url}/userinfo",
            "jwks_uri": f"{issuer_url}/jwks",
        }

    @staticmethod
    def test_connection(config: OIDCConfig) -> SSOTestResult:
        """Test OIDC connection to IdP.

        Production: Perform actual OIDC discovery and validate endpoints.
        """
        errors = OIDCAdapter.validate_config(config)
        if errors:
            return SSOTestResult(
                success=False, provider_type=SSOProviderType.OIDC,
                message="OIDC configuration invalid",
                error_details="; ".join(errors),
            )
        return SSOTestResult(
            success=True, provider_type=SSOProviderType.OIDC,
            message="OIDC configuration valid — ready for connection testing",
            redirect_url=config.authorization_endpoint or config.issuer_url,
        )


class SSOService:
    """Orchestrates SSO configuration and testing for tenants."""

    @staticmethod
    def configure_saml(tenant_id: UUID, saml_config: SAMLConfig) -> SSOConfig:
        """Create SAML SSO configuration for a tenant."""
        return SSOConfig.create_saml(tenant_id, saml_config)

    @staticmethod
    def configure_oidc(tenant_id: UUID, oidc_config: OIDCConfig) -> SSOConfig:
        """Create OIDC SSO configuration for a tenant."""
        return SSOConfig.create_oidc(tenant_id, oidc_config)

    @staticmethod
    def test(sso_config: SSOConfig) -> SSOTestResult:
        """Test SSO connection based on provider type."""
        if sso_config.provider_type == SSOProviderType.SAML and sso_config.saml:
            return SAMLAdapter.test_connection(sso_config.saml)
        elif sso_config.provider_type == SSOProviderType.OIDC and sso_config.oidc:
            return OIDCAdapter.test_connection(sso_config.oidc)
        return SSOTestResult(
            success=False, provider_type=sso_config.provider_type,
            message="No provider configuration found",
        )

    @staticmethod
    def add_domain(sso_config: SSOConfig, domain: str) -> DomainVerification:
        """Add a domain for SSO verification."""
        return sso_config.add_domain(domain)

    @staticmethod
    def verify_domain(sso_config: SSOConfig, domain: str, token: str) -> bool:
        """Verify domain ownership."""
        return sso_config.verify_domain(domain, token)
