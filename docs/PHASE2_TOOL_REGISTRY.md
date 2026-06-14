# Phase 2 Tool Registry

**Sprint 3 — Tool Registry Wiring**
**Branch:** `phase-2-enterprise-integration-foundation`
**Status:** Phase 2A complete — all 6 providers wired to mock implementations

---

## What the registry does

The `ProviderRegistry` (`backend/app/integration/registry.py`) is the
wiring point between:

- **Contracts** — Protocol interfaces defined in Sprint 1 (`contracts/`)
- **Implementations** — Mock providers (Sprint 2, `mocks/`) or real
  adapters (future sprints, `providers/`)
- **Configuration** — Per-provider mode settings from environment variables

The registry decouples *what* a provider does (the contract) from *which
implementation* satisfies it (mock vs. real). The AI supervisor, tool
layer, and status endpoint all interact with providers through the registry
— they never import a concrete provider class directly.

### Core operations

```python
registry = get_registry()                        # singleton
provider = registry.resolve(ProviderName.CLAIMCENTER)  # returns MockClaimCenterProvider
mode     = registry.effective_mode("claimcenter")      # returns ProviderMode.MOCK
info     = registry.registered_providers()             # {"claimcenter": {"mock": True, "real": False}, ...}
```

---

## Why MOCK is the default

Every provider defaults to `ProviderMode.MOCK`. This is not a temporary
shortcut — it is the permanent safe default, enforced at three levels:

1. **Config default** (`config.py`): every `PROVIDER_*` setting defaults
   to `"mock"`. No environment variable → mock mode.

2. **Registry resolution** (`registry.py`): if no mode is specified and no
   real factory is registered, mock is returned without error.

3. **Bootstrap** (`bootstrap.py`): `get_registry()` registers all 6 mock
   provider factories at application startup. The mock is always available.

The consequence: **switching from mock to real requires two explicit
actions** — setting an environment variable to `"real"` AND registering
a real adapter factory. Neither alone is sufficient. This prevents
accidental enterprise connectivity from a configuration typo.

---

## How HYBRID supports gradual migration

`HYBRID` mode allows individual providers to be at different stages of
migration simultaneously.

Example: ClaimCenter goes live while PolicyCenter remains on mock.

```ini
INTEGRATION_MODE=hybrid
PROVIDER_CLAIMCENTER=real
# PROVIDER_POLICYCENTER defaults to mock
```

In this configuration:
- `registry.resolve("claimcenter")` → real adapter (if registered)
- `registry.resolve("policycenter")` → mock provider
- `registry.resolve("edw")` → mock provider

HYBRID resolution rule (per provider):
1. Read `PROVIDER_<NAME>` environment variable.
2. If `real` → require a registered real factory (fail fast if missing).
3. If `mock` or unset → return mock provider.

This means HYBRID with all providers on mock works today — it is
equivalent to full MOCK mode with an explicit hybrid config.

---

## Why REAL fails fast without implementation

If a provider is set to `REAL` but no real adapter is registered, the
registry raises `IntegrationConfigError` **at startup**, before any
request is served.

This is intentional. The alternatives are worse:

| Alternative | Problem |
|---|---|
| Silent fallback to MOCK | Operator believes they are running live data; they are not. Incorrect production decisions result. |
| Return `None` | Every caller must null-check; one missing check causes an `AttributeError` in production. |
| Log a warning and continue | Warning is ignored; same outcome as silent fallback. |
| Fail at first use | Partial traffic reaches mock; partial traffic reaches real. Split-brain state. |

Failing fast at startup means: **if the application starts, the providers
are correctly configured.** No partial states.

Error message format:

```
IntegrationConfigError: Provider 'claimcenter' is configured for REAL mode
but no real adapter is registered. Real provider adapters are not
implemented in Phase 2A. Production enterprise integration requires
explicit adapter registration and governance approval (see ADR-002,
ADR-004). To use mock mode: set PROVIDER_CLAIMCENTER=mock (or remove the
variable — MOCK is the default).
```

---

## How future Guidewire adapters will register

When a real ClaimCenter adapter is ready (Phase 2B+):

### 1. Implement the adapter

```python
# backend/app/integration/providers/claimcenter.py

from backend.app.integration.contracts.claimcenter import (
    IClaimCenterReadProvider,
    IClaimCenterWriteProvider,
)

class RealClaimCenterAdapter:
    """
    Guidewire ClaimCenter REST API v10 adapter.
    Implements IClaimCenterReadProvider.
    Write methods require Phase 2B gate (ADR-002).
    """
    def get_claim(self, claim_id: str, context: ToolExecutionContext) -> GetClaimResult:
        # Map from Guidewire field names to platform models
        ...
```

### 2. Register the factory

In `bootstrap.py`, add below the mock registrations:

```python
from backend.app.integration.providers.claimcenter import RealClaimCenterAdapter
registry.register_real(ProviderName.CLAIMCENTER, lambda: RealClaimCenterAdapter())
```

### 3. Enable via environment variable

```ini
PROVIDER_CLAIMCENTER=real
# or
INTEGRATION_MODE=hybrid
PROVIDER_CLAIMCENTER=real
```

### 4. No other changes required

The AI supervisor, tool layer, and status endpoint resolve the provider
through the registry. They see the same contract interface regardless
of whether the mock or real adapter is active. **No UX redesign, no tool
rewrites, no prompt changes.**

---

## Why this design supports adapter substitution without UX redesign

The registry enforces the **Ports and Adapters** pattern (ADR-001,
ADR-004):

- **Port**: the contract Protocol (`IClaimCenterReadProvider`)
- **Adapter**: the implementation (mock or real)
- **Registry**: the wiring between them

The AI supervisor invokes deterministic tool functions. Those tool
functions call `get_registry().resolve(name)` to get a provider. The
provider satisfies the contract. Whether it is mock or real is invisible
to the supervisor.

This means:
- The adjuster UI does not change when a real adapter goes live.
- The AI prompt templates do not change.
- The claim summary format does not change.
- The only change is in `bootstrap.py` (register real factory) and
  environment config (set `PROVIDER_X=real`).

---

## Provider name constants

All provider names are defined as class attributes in `providers.py`:

```python
ProviderName.CLAIMCENTER  = "claimcenter"
ProviderName.POLICYCENTER = "policycenter"
ProviderName.EDW          = "edw"
ProviderName.DOCUMENTS    = "documents"
ProviderName.FRAUD        = "fraud"
ProviderName.EMAIL        = "email"
ProviderName.ALL          = (all six, in order)
```

Use these constants everywhere instead of string literals.

---

## Status endpoint

`GET /api/integration/status` returns safe operational metadata:

```json
{
  "global_mode": "mock",
  "providers": [
    {
      "name": "claimcenter",
      "mode": "mock",
      "mock_registered": true,
      "real_registered": false,
      "real_provider_available": false,
      "writes_enabled": false
    }
  ],
  "writes_enabled": false,
  "lab_safe": true,
  "phase": "Phase 2A — Mock providers (Sprint 2/3)",
  "note": "All providers are running against specification-backed mock data..."
}
```

Does not expose: API keys, tokens, connection strings, environment variable
values, internal hostnames, or write gate override capability.

---

## Files in this sprint

| File | Role |
|---|---|
| `backend/app/integration/providers.py` | `ProviderName` constants |
| `backend/app/integration/bootstrap.py` | Registry construction + mock registration |
| `backend/app/integration/registry.py` | Registry (updated: stronger REAL error message) |
| `backend/app/api/routes_integration.py` | `GET /api/integration/status` |
| `backend/main.py` | Wired integration router + registry warmup at startup |
| `docs/PHASE2_TOOL_REGISTRY.md` | This document |

---

## Write gate status

Writes remain disabled. `MockWriteDisabledError` is raised by
`create_claim_note` and `create_activity` on `MockClaimCenterProvider`.
`send_email` does not exist on `MockEmailProvider`. `draft_email` returns
advisory text only — no email is sent.

The 9-condition write gate (ADR-002) has not been satisfied. This will
be revisited in Phase 2B.
