"""
Integration bootstrap — wires Sprint 2 mock providers into the registry.

This module is the single point of truth for all provider registrations.
It is called once at application startup (from backend/main.py) and
returns the singleton ProviderRegistry.

MOCK providers registered here (Sprint 2):
  claimcenter  → MockClaimCenterProvider
  policycenter → MockPolicyCenterProvider
  edw          → MockEDWProvider
  documents    → MockDocumentProvider
  fraud        → MockFraudProvider
  email        → MockEmailProvider

REAL providers:
  None registered. Requesting REAL mode raises IntegrationConfigError
  immediately. No silent fallback to MOCK.

Write gate (ADR-002):
  All providers are registered in read-only mode. Write methods on
  MockClaimCenterProvider raise MockWriteDisabledError unconditionally.
  Writes remain disabled until Phase 2B identity, idempotency, human
  approval, and audit reconciliation gates are satisfied.

How to add a real provider (future Sprint):
  1. Obtain the enterprise system's API specification.
  2. Implement an adapter class that satisfies the relevant contract
     protocol (IClaimCenterReadProvider, etc.) in
     backend/app/integration/providers/.
  3. Obtain governance approval (ADR-002 write gate if writes are needed).
  4. Call registry.register_real("claimcenter", lambda: RealClaimCenterAdapter())
     in this function, below the mock registrations.
  5. Set PROVIDER_CLAIMCENTER=real (or INTEGRATION_MODE=hybrid) in the
     environment where the real adapter should be active.

No imports from this file should trigger enterprise connectivity. All
mock provider factories are lightweight lambdas — no network I/O at
registration time.
"""

from __future__ import annotations

from functools import lru_cache

from backend.app.integration.config import get_integration_config
from backend.app.integration.mocks.claimcenter import MockClaimCenterProvider
from backend.app.integration.mocks.documents import MockDocumentProvider
from backend.app.integration.mocks.edw import MockEDWProvider
from backend.app.integration.mocks.email import MockEmailProvider
from backend.app.integration.mocks.fraud import MockFraudProvider
from backend.app.integration.mocks.policycenter import MockPolicyCenterProvider
from backend.app.integration.providers import ProviderName  # providers/__init__.py
from backend.app.integration.registry import ProviderRegistry


def _build_registry() -> ProviderRegistry:
    """
    Construct and populate the provider registry.

    Registers all 6 mock providers. No real providers are registered.
    Each factory is a zero-argument callable that returns a fresh
    provider instance — the registry calls the factory on every resolve().

    If provider-level caching / request-scoped singletons are needed in a
    later sprint, wrap the factory in an appropriate scope here.
    """
    config = get_integration_config()
    registry = ProviderRegistry(config=config)

    # Sprint 2 mock providers — all read-only
    registry.register_mock(ProviderName.CLAIMCENTER, lambda: MockClaimCenterProvider())
    registry.register_mock(ProviderName.POLICYCENTER, lambda: MockPolicyCenterProvider())
    registry.register_mock(ProviderName.EDW, lambda: MockEDWProvider())
    registry.register_mock(ProviderName.DOCUMENTS, lambda: MockDocumentProvider())
    registry.register_mock(ProviderName.FRAUD, lambda: MockFraudProvider())
    registry.register_mock(ProviderName.EMAIL, lambda: MockEmailProvider())

    # --- Real providers: none registered in Phase 2A ---
    # Future sprint example:
    #   from backend.app.integration.providers.claimcenter import RealClaimCenterAdapter
    #   registry.register_real(ProviderName.CLAIMCENTER, lambda: RealClaimCenterAdapter())

    return registry


@lru_cache(maxsize=1)
def get_registry() -> ProviderRegistry:
    """
    Return the application-scoped provider registry singleton.

    The registry is built once and cached for the lifetime of the process.
    Call get_registry().resolve(ProviderName.CLAIMCENTER) to obtain a
    provider instance.

    lru_cache ensures this is safe to call from anywhere — FastAPI
    dependency injection, tools, background tasks — without re-building
    the registry on every call.
    """
    return _build_registry()
