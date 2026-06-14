"""
Integration exceptions for mock enterprise providers.

These exceptions represent the error conditions that real enterprise
adapters will raise in production. Building mock providers that raise
these same exceptions ensures that upstream error handling — in the
supervisor, orchestration layer, and governance engine — is exercised
against these mocks and will work correctly when real adapters replace them.

Exception hierarchy:
    MockIntegrationError (base)
    ├── MockNotFoundError      — 404: resource not in system or adjuster portfolio
    ├── MockUnauthorizedError  — 401: authentication token missing or invalid
    ├── MockForbiddenError     — 403: authenticated but insufficient permissions
    ├── MockRateLimitError     — 429: API rate limit exceeded (retryable)
    ├── MockTimeoutError       — 408/504: upstream timeout (retryable)
    ├── MockUnavailableError   — 503: upstream unavailable (retryable)
    └── MockWriteDisabledError — write operation blocked by Phase 2B gate
"""

from __future__ import annotations


class MockIntegrationError(Exception):
    """
    Base class for all mock integration exceptions.

    In production, real adapter exceptions will extend a parallel
    IntegrationError hierarchy. The supervisor and orchestration layer
    must catch MockIntegrationError (or a future IntegrationError base)
    rather than specific subclasses where the same handling applies.
    """

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.message = message

    def __str__(self) -> str:
        retry_hint = " [retryable]" if self.retryable else ""
        return f"{self.__class__.__name__}{retry_hint}: {self.message}"


class MockNotFoundError(MockIntegrationError):
    """
    Resource not found — HTTP 404 equivalent.

    Raised when:
      - A claim ID is not in the adjuster's ClaimCenter portfolio
      - A policy number is not associated with the claim
      - A document ID does not exist or is not linked to the claim

    NOT retryable — the resource does not exist; retrying will not help.
    """

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, retryable=False)


class MockUnauthorizedError(MockIntegrationError):
    """
    Authentication failure — HTTP 401 equivalent.

    Raised when:
      - The session token has expired
      - OBO token exchange failed
      - Service account credentials are invalid

    Retryable after re-authentication.
    """

    def __init__(self, message: str = "Authentication token missing or invalid.") -> None:
        super().__init__(message, retryable=False)


class MockForbiddenError(MockIntegrationError):
    """
    Permission denied — HTTP 403 equivalent.

    Raised when:
      - Adjuster does not have read permission for this claim type
      - SIU data access requires a higher role than the adjuster holds
      - Write access is attempted without an approved write-gate identity

    NOT retryable — permissions must be granted before retrying.
    """

    def __init__(self, message: str = "Insufficient permissions for this resource.") -> None:
        super().__init__(message, retryable=False)


class MockRateLimitError(MockIntegrationError):
    """
    Rate limit exceeded — HTTP 429 equivalent.

    Raised when:
      - ClaimCenter API quota is exhausted for the current time window
      - Azure Cognitive Search throttles the query rate
      - Model gateway token-per-minute limit is reached

    Retryable after a backoff period (production: follow Retry-After header).
    """

    def __init__(
        self,
        message: str = "API rate limit exceeded — retry after backoff.",
        retry_after_seconds: int = 60,
    ) -> None:
        super().__init__(message, retryable=True)
        self.retry_after_seconds = retry_after_seconds

    def __str__(self) -> str:
        return (
            f"MockRateLimitError [retryable after {self.retry_after_seconds}s]: "
            f"{self.message}"
        )


class MockTimeoutError(MockIntegrationError):
    """
    Upstream timeout — HTTP 408/504 equivalent.

    Raised when:
      - ClaimCenter does not respond within the configured timeout
      - A complex EDW query exceeds the query timeout limit
      - The fraud scoring engine is slow to respond

    Retryable — the upstream system may be temporarily slow.
    """

    def __init__(self, message: str = "Upstream system did not respond within the timeout window.") -> None:
        super().__init__(message, retryable=True)


class MockUnavailableError(MockIntegrationError):
    """
    Service unavailable — HTTP 503 equivalent.

    Raised when:
      - ClaimCenter is in a maintenance window
      - Azure Cognitive Search index is being rebuilt
      - The fraud system is offline

    Retryable — the upstream system should recover.
    """

    def __init__(self, message: str = "Upstream system is temporarily unavailable.") -> None:
        super().__init__(message, retryable=True)


class MockWriteDisabledError(MockIntegrationError):
    """
    Write operation blocked by the Phase 2B write-framework gate (ADR-002).

    Raised by ALL write provider methods until all Phase 2B gate conditions
    are satisfied. This is not a transient error — it is a deliberate
    architectural control. Do not catch and retry; surface to the caller.

    Write gate conditions (ADR-002):
      1. Identity strategy confirmed: OBO or approved fallback (ADR-003)
      2. Idempotency key mechanism implemented and tested
      3. Read-back reconciliation after write implemented
      4. Human approval record verified present before write
      5. ClaimCenter write contract validated in lower environment
      6. Security review of write path completed
      7. Compliance sign-off on write audit trail
      8. IAM approval of ClaimCenter write endpoint access
      9. Write rollback procedure documented and tested
    """

    def __init__(
        self,
        message: str = (
            "Write operations are disabled until Phase 2B identity, idempotency, "
            "human approval, and audit reconciliation gates are approved."
        ),
    ) -> None:
        super().__init__(message, retryable=False)
