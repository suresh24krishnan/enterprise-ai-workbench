"""
Integration layer configuration.

All provider modes default to MOCK. No provider can be set to REAL
without explicit environment variable configuration. REAL mode with no
registered real adapter raises IntegrationConfigError at registry
resolution time — the application does not start.

Environment variable: INTEGRATION_MODE
  Controls the global default. Per-provider overrides take precedence.
  Default: "mock"
  Allowed: "mock" | "hybrid" | "real"

Per-provider environment variables (all default to "mock"):
  PROVIDER_CLAIMCENTER   — ClaimCenter read/write provider
  PROVIDER_POLICYCENTER  — PolicyCenter provider
  PROVIDER_EDW           — Enterprise Data Warehouse provider
  PROVIDER_DOCUMENTS     — Document store provider
  PROVIDER_FRAUD         — Fraud detection provider
  PROVIDER_EMAIL         — Email/notification provider

Example: enable hybrid mode with one live provider
  INTEGRATION_MODE=hybrid
  PROVIDER_CLAIMCENTER=real

Example: full mock (default — no configuration needed)
  # No environment variables required

Example: REAL mode protection
  PROVIDER_CLAIMCENTER=real
  # IntegrationConfigError raised at startup if no real ClaimCenter
  # adapter is registered — application does not start.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.integration.modes import ProviderMode


class IntegrationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Global default — individual provider settings take precedence
    integration_mode: ProviderMode = ProviderMode.MOCK

    # Per-provider modes — all default MOCK
    provider_claimcenter: ProviderMode = ProviderMode.MOCK
    provider_policycenter: ProviderMode = ProviderMode.MOCK
    provider_edw: ProviderMode = ProviderMode.MOCK
    provider_documents: ProviderMode = ProviderMode.MOCK
    provider_fraud: ProviderMode = ProviderMode.MOCK
    provider_email: ProviderMode = ProviderMode.MOCK

    @field_validator(
        "provider_claimcenter",
        "provider_policycenter",
        "provider_edw",
        "provider_documents",
        "provider_fraud",
        "provider_email",
        mode="before",
    )
    @classmethod
    def reject_real_without_explicit_intent(cls, v: str) -> str:
        # Validation only — registry enforces the adapter-exists check.
        # This validator ensures the value is a recognised mode string.
        allowed = {m.value for m in ProviderMode}
        if isinstance(v, str) and v.lower() not in allowed:
            raise ValueError(
                f"Invalid provider mode '{v}'. "
                f"Allowed values: {sorted(allowed)}"
            )
        return v

    def effective_mode(self, provider_name: str) -> ProviderMode:
        """
        Return the effective mode for a named provider.

        Per-provider setting takes precedence over the global
        integration_mode default.
        """
        per_provider = getattr(self, f"provider_{provider_name}", None)
        if per_provider is not None:
            return per_provider
        return self.integration_mode


@lru_cache
def get_integration_config() -> IntegrationConfig:
    return IntegrationConfig()
