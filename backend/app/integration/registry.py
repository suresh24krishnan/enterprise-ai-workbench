"""
Provider registry for the integration layer.

Responsibilities:
  - Register provider factories by name and mode
  - Resolve the correct provider instance for a given name
  - Report the effective mode for any provider
  - Fail fast if REAL is requested and no real factory is registered
  - Prevent silent fallback from REAL to MOCK

No business logic. No orchestration. No API calls. No enterprise
connectivity. This is purely structural — a wiring point for Sprint 1
contracts and Sprint 2 mock providers.

Usage (Sprint 2+, after mock providers exist):

    registry = ProviderRegistry(config=get_integration_config())
    registry.register_mock("claimcenter", lambda: MockClaimCenterProvider())
    provider = registry.resolve("claimcenter")

Usage (current Sprint 0.5 — no providers registered yet):

    registry = ProviderRegistry(config=get_integration_config())
    # resolve("claimcenter") → IntegrationConfigError
    # (no mock registered yet; will be populated in Sprint 2)
"""

from __future__ import annotations

from typing import Any, Callable

from backend.app.integration.config import IntegrationConfig, get_integration_config
from backend.app.integration.modes import ProviderMode


class IntegrationConfigError(Exception):
    """
    Raised when the registry cannot satisfy a provider resolution request.

    Causes:
      - REAL mode requested, no real factory registered
      - MOCK mode requested, no mock factory registered
      - Provider name unknown to the registry
    """


ProviderFactory = Callable[[], Any]


class ProviderRegistry:
    """
    Lightweight provider registry.

    Register factories with register_mock() and register_real().
    Resolve providers with resolve().

    Thread safety: not thread-safe. Registrations must happen at
    application startup before the first resolve() call.
    """

    def __init__(self, config: IntegrationConfig | None = None) -> None:
        self._config = config or get_integration_config()
        self._mock_factories: dict[str, ProviderFactory] = {}
        self._real_factories: dict[str, ProviderFactory] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_mock(self, name: str, factory: ProviderFactory) -> None:
        """Register a mock provider factory for the given provider name."""
        self._mock_factories[name] = factory

    def register_real(self, name: str, factory: ProviderFactory) -> None:
        """Register a real (enterprise) provider factory."""
        self._real_factories[name] = factory

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, name: str) -> Any:
        """
        Resolve and return a provider instance for the given name.

        The effective mode is determined by IntegrationConfig:
          - Per-provider setting (PROVIDER_<NAME>) takes precedence
          - Falls back to global INTEGRATION_MODE
          - Global default is MOCK

        Raises IntegrationConfigError if:
          - Effective mode is REAL and no real factory is registered
          - Effective mode is MOCK and no mock factory is registered
          - Provider name is not registered in any factory
        """
        mode = self.effective_mode(name)

        if mode == ProviderMode.REAL:
            return self._resolve_real(name)

        # MOCK or HYBRID — resolve mock unless a real factory exists and
        # HYBRID explicitly targets this provider at REAL.
        if mode == ProviderMode.HYBRID:
            # In HYBRID, per-provider config determines which mode applies.
            # The effective_mode() already resolved the per-provider setting.
            # A per-provider REAL in HYBRID mode still requires a real factory.
            per_provider = getattr(
                self._config, f"provider_{name}", ProviderMode.MOCK
            )
            if per_provider == ProviderMode.REAL:
                return self._resolve_real(name)

        return self._resolve_mock(name)

    def effective_mode(self, name: str) -> ProviderMode:
        """Return the effective ProviderMode for a named provider."""
        return self._config.effective_mode(name)

    def registered_providers(self) -> dict[str, dict[str, bool]]:
        """
        Return a summary of all registered factories.

        Returns:
            {
                "claimcenter": {"mock": True, "real": False},
                ...
            }
        """
        names = set(self._mock_factories) | set(self._real_factories)
        return {
            n: {
                "mock": n in self._mock_factories,
                "real": n in self._real_factories,
            }
            for n in sorted(names)
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_real(self, name: str) -> Any:
        if name not in self._real_factories:
            raise IntegrationConfigError(
                f"Provider '{name}' is configured for REAL mode but no real "
                f"adapter is registered. "
                f"Register a real factory with registry.register_real('{name}', ...) "
                f"or change PROVIDER_{name.upper()} to 'mock'."
            )
        return self._real_factories[name]()

    def _resolve_mock(self, name: str) -> Any:
        if name not in self._mock_factories:
            raise IntegrationConfigError(
                f"Provider '{name}' has no registered mock factory. "
                f"Mock providers will be registered in Sprint 2. "
                f"Register a mock factory with registry.register_mock('{name}', ...)."
            )
        return self._mock_factories[name]()
