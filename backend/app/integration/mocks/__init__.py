# backend/app/integration/mocks
#
# Specification-backed mock providers — Sprint 2.
# Each mock implements its corresponding contract protocol (IXxxReadProvider,
# IXxxWriteProvider) using Phase 1 claim data for CLM-2026-100245.
#
# Mocks simulate real system behaviour: same field names, HTTP status codes,
# error shapes, and pagination as the real system (ADR-004).
# An integration test that passes against a mock must pass against the
# real provider without code changes.
#
# Write methods always raise MockWriteDisabledError (ADR-002 Phase 2B).

from backend.app.integration.mocks.claimcenter import MockClaimCenterProvider
from backend.app.integration.mocks.documents import MockDocumentProvider
from backend.app.integration.mocks.edw import MockEDWProvider
from backend.app.integration.mocks.email import MockEmailProvider
from backend.app.integration.mocks.errors import (
    MockForbiddenError,
    MockIntegrationError,
    MockNotFoundError,
    MockRateLimitError,
    MockTimeoutError,
    MockUnauthorizedError,
    MockUnavailableError,
    MockWriteDisabledError,
)
from backend.app.integration.mocks.fraud import MockFraudProvider
from backend.app.integration.mocks.policycenter import MockPolicyCenterProvider
from backend.app.integration.mocks.simulation import (
    DEFAULT_SIM,
    FailureMode,
    SimulationConfig,
    apply_simulation,
    paginate,
)

__all__ = [
    # Providers
    "MockClaimCenterProvider",
    "MockPolicyCenterProvider",
    "MockEDWProvider",
    "MockDocumentProvider",
    "MockFraudProvider",
    "MockEmailProvider",
    # Errors
    "MockIntegrationError",
    "MockNotFoundError",
    "MockUnauthorizedError",
    "MockForbiddenError",
    "MockRateLimitError",
    "MockTimeoutError",
    "MockUnavailableError",
    "MockWriteDisabledError",
    # Simulation
    "FailureMode",
    "SimulationConfig",
    "DEFAULT_SIM",
    "apply_simulation",
    "paginate",
]
