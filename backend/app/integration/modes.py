"""
Runtime provider modes for the integration layer.

Three modes are supported:

MOCK    — All providers are specification-backed mocks. No enterprise
          connectivity. Safe for local development, CI, and the current
          Phase 2 Sprint 0.5 state where no real adapters exist.
          This is the permanent default.

HYBRID  — Individual providers may be set to MOCK or REAL independently.
          Allows incremental migration: one provider goes live while others
          remain on mock. The ProviderRegistry resolves each provider's
          effective mode independently.

REAL    — Reserved for fully-integrated enterprise environments.
          A provider set to REAL with no registered real adapter raises
          IntegrationConfigError immediately at startup. There is no silent
          fallback from REAL to MOCK — that would hide misconfiguration.

Safety rules enforced by the registry (registry.py):

  1. Default mode is MOCK. The integration.config default for every
     provider is ProviderMode.MOCK.

  2. REAL never activates accidentally. Switching a provider to REAL
     requires explicit environment variable configuration AND a registered
     real adapter factory. Both conditions must be true.

  3. No silent fallback. If REAL is configured but no real adapter exists,
     IntegrationConfigError is raised. The application does not start.

  4. MOCK is always safe. Switching from REAL back to MOCK requires only
     a configuration change — no code change.
"""

from enum import Enum


class ProviderMode(str, Enum):
    MOCK = "mock"
    HYBRID = "hybrid"
    REAL = "real"
