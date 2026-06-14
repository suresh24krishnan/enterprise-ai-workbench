# backend/app/integration/providers
#
# Real provider implementations (enterprise adapters).
# Populated in Sprint 2+ — one adapter per real enterprise system.
#
# No real providers exist yet. REAL mode raises IntegrationConfigError
# until a real provider is registered for the requested name.
#
# ProviderName constants are defined here for convenient import:
#   from backend.app.integration.providers import ProviderName


class ProviderName:
    """
    Canonical provider name constants for use with the ProviderRegistry.

    Use these constants everywhere instead of inline string literals:
      registry.resolve(ProviderName.CLAIMCENTER)   # not "claimcenter"
      registry.register_mock(ProviderName.EDW, ...) # not "edw"

    All 6 constants map to the enterprise systems documented in the ADRs:
      CLAIMCENTER   — Guidewire ClaimCenter (ADR-001, ADR-004)
      POLICYCENTER  — Guidewire PolicyCenter (ADR-004)
      EDW           — Enterprise Data Warehouse (ADR-004)
      DOCUMENTS     — Document management / ECM system (ADR-004, ADR-006)
      FRAUD         — Fraud detection / SIU scoring system (ADR-004)
      EMAIL         — Email correspondence system (ADR-004)
    """

    CLAIMCENTER: str = "claimcenter"
    POLICYCENTER: str = "policycenter"
    EDW: str = "edw"
    DOCUMENTS: str = "documents"
    FRAUD: str = "fraud"
    EMAIL: str = "email"

    ALL: tuple[str, ...] = (
        "claimcenter",
        "policycenter",
        "edw",
        "documents",
        "fraud",
        "email",
    )
