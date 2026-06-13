# adapters/identity/

Identity adapter — authentication and authorization.

## Responsibility

Implements `IIdentityProvider` against the configured identity system. In Phase 1 this is a mock that accepts any valid-looking credentials. In Phase 2+ it integrates with Azure AD or Okta.

## Interface Implemented

```python
class IIdentityProvider(Protocol):
    def authenticate(self, credentials: Credentials) -> AuthResult: ...
    def validate_token(self, token: str) -> TokenClaims | None: ...
    def get_user(self, user_id: str) -> User | None: ...
    def get_user_permissions(self, user_id: str) -> list[Permission]: ...
```

## Implementations

| File | Environment Value | Description |
|------|------------------|-------------|
| `mock_identity_provider.py` | `IDENTITY_PROVIDER=mock` | Fixed test users with predefined roles |
| `azure_ad_adapter.py` | `IDENTITY_PROVIDER=azure_ad` | Azure AD OAuth2 / OIDC |
| `okta_adapter.py` | `IDENTITY_PROVIDER=okta` | Okta OAuth2 / OIDC |

## Mock Users

The mock provider includes realistic test users across roles:

| User | Role | Permissions |
|------|------|-------------|
| `adjuster@mock.local` | Claims Adjuster | Read claims, view AI output, approve notes |
| `supervisor@mock.local` | Supervisor | All adjuster permissions + override escalations |
| `auditor@mock.local` | Auditor | Read-only access to claims and full audit log |

## Roles and Permissions

| Permission | Adjuster | Supervisor | Auditor |
|------------|----------|------------|---------|
| `claims:read` | ✓ | ✓ | ✓ |
| `ai:generate` | ✓ | ✓ | — |
| `notes:approve` | ✓ | ✓ | — |
| `escalation:override` | — | ✓ | — |
| `audit:read` | — | ✓ | ✓ |
