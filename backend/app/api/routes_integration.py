"""
Integration status endpoint.

GET /api/integration/status

Returns provider mode metadata for operational visibility. Exposes only
safe configuration metadata — no secrets, no environment variable values,
no internal system addresses.

This endpoint is intentionally read-only and additive. It does not alter
any existing API, route, or application behavior.

SECURITY:
  - Does not expose API keys, tokens, connection strings, or env vars.
  - Does not expose internal hostnames or URLs.
  - Does not expose write gate override capability.
  - Returns only mode/status strings safe for operational dashboards.

Usage: curl http://localhost:8000/api/integration/status
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.integration.bootstrap import get_registry
from backend.app.integration.config import get_integration_config
from backend.app.integration.providers import ProviderName

router = APIRouter(prefix="/api/integration", tags=["integration"])


class ProviderStatusEntry(BaseModel):
    name: str
    mode: str
    mock_registered: bool
    real_registered: bool
    real_provider_available: bool
    writes_enabled: bool


class IntegrationStatusResponse(BaseModel):
    global_mode: str
    providers: list[ProviderStatusEntry]
    writes_enabled: bool
    lab_safe: bool
    phase: str
    note: str


@router.get("/status", response_model=IntegrationStatusResponse)
def integration_status() -> IntegrationStatusResponse:
    """
    Return integration registry status.

    Safe metadata only. No secrets. No environment values.

    Fields:
      global_mode         — effective integration mode (always "mock" in Phase 2A)
      providers           — per-provider mode and registration status
      writes_enabled      — always false; Phase 2B write gate not yet open
      lab_safe            — always true in mock mode; no enterprise connectivity
      phase               — current phase label
      note                — human-readable status note
    """
    config = get_integration_config()
    registry = get_registry()
    registered = registry.registered_providers()

    provider_entries = []
    for name in ProviderName.ALL:
        info = registered.get(name, {"mock": False, "real": False})
        mode = registry.effective_mode(name).value
        provider_entries.append(
            ProviderStatusEntry(
                name=name,
                mode=mode,
                mock_registered=info["mock"],
                real_registered=info["real"],
                real_provider_available=info["real"],
                writes_enabled=False,  # Phase 2B gate not open
            )
        )

    return IntegrationStatusResponse(
        global_mode=config.integration_mode.value,
        providers=provider_entries,
        writes_enabled=False,
        lab_safe=True,
        phase="Phase 2A — Mock providers (Sprint 2/3)",
        note=(
            "All providers are running against specification-backed mock data. "
            "No enterprise connectivity. "
            "Writes are disabled until Phase 2B identity, idempotency, "
            "human approval, and audit reconciliation gates are satisfied."
        ),
    )
