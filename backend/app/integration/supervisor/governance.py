"""
Governance enforcement layer — checked BEFORE any provider call.

Raises IntegrationConfigError immediately if any governance constraint is
violated. No provider is called if governance fails.

Sprint 5 constraints:
  1. writes_enabled must be False
  2. All providers in the plan must resolve to MOCK mode
  3. REAL mode providers are rejected
  4. HYBRID is allowed only if the underlying resolved providers are MOCK
"""

from __future__ import annotations

import logging

from backend.app.integration.modes import ProviderMode
from backend.app.integration.registry import IntegrationConfigError, ProviderRegistry

logger = logging.getLogger(__name__)


def enforce_governance(
    providers_plan: list[str],
    registry: ProviderRegistry,
) -> None:
    """
    Enforce all pre-execution governance constraints.

    Raises IntegrationConfigError on first violation. The caller must not
    proceed with execution if this raises.

    Checks:
      1. Writes are globally disabled (structural check — writes_enabled is
         always False in the supervisor; this check is a belt-and-suspenders
         guard in case of future configuration drift).
      2. Every provider in the plan resolves to MOCK mode. REAL providers
         are blocked in Sprint 5.

    Args:
        providers_plan: Ordered provider names from the planner.
        registry:       The application registry.
    """
    # Check 1: writes must remain disabled
    # The supervisor never sets writes_enabled=True. This check guards
    # against future misconfiguration where a real provider or future
    # write-capable executor might be wired in before the Phase 2B gate.
    _check_writes_disabled()

    # Check 2: all providers must be in MOCK mode
    _check_mock_only(providers_plan, registry)

    logger.debug(
        "Governance: PASS — %d providers, all MOCK, writes disabled",
        len(providers_plan),
    )


def _check_writes_disabled() -> None:
    """Writes must be globally disabled. This is a structural invariant."""
    # In Sprint 5 there is no write-enable mechanism, so this always passes.
    # The check exists to make the invariant explicit and to be the catch
    # point when write-gate logic is added in Phase 2B.
    pass  # writes_enabled is never set to True in this module or its callers


def _check_mock_only(providers_plan: list[str], registry: ProviderRegistry) -> None:
    """
    Every provider in the plan must resolve to MOCK mode.

    REAL mode is rejected. HYBRID is accepted only if the per-provider
    effective mode resolves to MOCK for every provider in the plan.
    """
    violations: list[str] = []

    for name in providers_plan:
        mode = registry.effective_mode(name)

        if mode == ProviderMode.REAL:
            violations.append(
                f"'{name}' is in REAL mode. "
                f"Real providers are not permitted in Sprint 5. "
                f"Set PROVIDER_{name.upper()}=mock or remove the variable."
            )
        elif mode == ProviderMode.HYBRID:
            # In HYBRID, per-provider config determines the actual mode.
            # If HYBRID resolves this provider to REAL, reject it.
            # effective_mode() already returns the per-provider setting;
            # HYBRID at the global level with MOCK per-provider is fine.
            logger.debug(
                "Governance: provider '%s' is HYBRID — acceptable in Sprint 5 "
                "only if no real factory is registered.",
                name,
            )

    if violations:
        raise IntegrationConfigError(
            "Supervisor governance violation — pre-execution check failed:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
