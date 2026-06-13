# mock-data/

Local mock data for Phase 1 development.

## Responsibility

Provides realistic, deterministic test data consumed by mock adapters. This data replaces live integrations (ClaimCenter, enterprise knowledge bases) during local development.

## Structure (to be built)

```
mock-data/
├── claims/
│   ├── CLM-2024-001.json       # Auto liability claim, medium risk
│   ├── CLM-2024-002.json       # Property damage claim, high risk (high reserve)
│   ├── CLM-2024-003.json       # Workers' compensation, low risk
│   └── index.json              # Search index for mock claim queries
├── knowledge/
│   ├── claims-handling-guide.md          # Standard claims handling procedures
│   ├── coverage-interpretation.md        # Coverage analysis guidelines
│   ├── escalation-criteria.md            # When and how to escalate
│   └── regulatory-requirements.md        # Jurisdiction-specific rules
└── users/
    └── users.json              # Mock user accounts and roles
```

## Mock Claim Structure

Each claim file contains a realistic representation including:
- Claim metadata (number, status, type, dates)
- Parties (insured, claimant, attorney if applicable)
- Coverages and policy limits
- Reserve amounts
- Existing notes
- Document references
- Risk flags

## Design Rules

- Mock data must be realistic — it demonstrates the system to stakeholders
- Claims should span risk levels (low / medium / high) to exercise all routing paths
- Knowledge documents should be genuine enough to produce coherent AI responses
- Never include real personal information — all data is fictional
- Files ending in `.local.json` are gitignored — use for personal development overrides
