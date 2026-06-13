# Release Strategy — Enterprise AI Workbench

## Summary

One repository. One Hugging Face Space. Versioned evolution through Git tags and GitHub Releases. The architecture is built once; adapters are swapped between phases.

---

## Repository Strategy

**Single repository for all phases.**

There is no `phase-2` branch, no separate repo, no fork. The `main` branch always reflects the latest deployable state. Each phase is a set of commits on top of the previous — not a rewrite.

```
main
 │
 ├── d2c6989  Phase 1 MVP Freeze                    ← tag: v1.0.0-phase1
 ├── 89d23f5  Phase 1.1 Dockerization
 ├── 2c406db  HF Space deployment                   ← current HEAD
 │
 │   (future)
 ├── xxxxxxx  Phase 2: identity provider integration
 ├── xxxxxxx  Phase 2: ClaimCenter sandbox adapter
 ├── xxxxxxx  Phase 2: PostgreSQL repository         ← tag: v1.1.0-phase2
 │
 ├── xxxxxxx  Azure OpenAI model provider
 ├── xxxxxxx  Azure Cognitive Search RAG adapter     ← tag: v1.2.0
 │
 └── xxxxxxx  Multi-domain, production platform      ← tag: v2.0.0
```

**Why one repo:**
- Architecture decisions accumulate as commits — full history preserved
- No merge conflicts between phase branches
- No "which branch is production" ambiguity
- Reviewers can always `git log` to understand what changed and why
- Tags mark stable milestones without disrupting the development flow

---

## Hugging Face Space Strategy

**One Space. Always points to `main`.**

`https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench`

The Space is a deployment target, not a branch. When Phase 2 adapters are wired and tested, they are merged to `main` and pushed to the HF remote. The Space rebuilds automatically.

There is no `enterprise-ai-workbench-phase2` Space. The Space URL is stable and shareable at every phase.

**Deployment model:**
```
git push hf main:main
       │
       └──▶ HF Spaces detects push
              └──▶ docker build . (multi-stage)
                     └──▶ Space rebuilds and redeploys
```

---

## Version Path

| Tag | Name | Milestone | Status |
|-----|------|-----------|--------|
| `v1.0.0-phase1` | Reference Implementation | Full governed workflow, all mock adapters, immutable audit trail, 9-screen UI | **Released** |
| `v1.1.0-phase2` | Sandbox Integration | Real identity provider, ClaimCenter sandbox API, PostgreSQL, enterprise RAG pipeline | Planned |
| `v1.2.0` | AI Layer | Azure OpenAI model provider, real model routing, live policy engine, immutable audit ledger | Planned |
| `v2.0.0` | Enterprise Platform | Multi-domain support, production ClaimCenter, compliance reporting, SLA monitoring, role-based access | Planned |

---

## What Changes Between Phases

The business logic, UI, API contracts, and governance interfaces do not change between phases. Only adapters are swapped.

| Component | Phase 1 | Phase 2 | Phase 3 |
|-----------|---------|---------|---------|
| `IClaimRepository` | `MockClaimRepository` | `ClaimCenterSandboxRepository` | `ClaimCenterProductionRepository` |
| `IIdentityProvider` | `MockIdentityProvider` | `SSOIdentityProvider` | `SSOIdentityProvider` |
| `IModelProvider` | `MockModelProvider` | `AzureOpenAIProvider` | `AzureOpenAIProvider` |
| `IKnowledgeProvider` | `MockKnowledgeProvider` | `AzureCognitiveSearchProvider` | `AzureCognitiveSearchProvider` |
| `IAuditStore` | `InMemoryAuditStore` | `PostgreSQLAuditStore` | `ImmutableLedgerAuditStore` |
| `IGovernanceEngine` | `MockGovernanceEngine` | `RuleBasedGovernanceEngine` | `PolicyEngineGovernanceEngine` |

The only file that imports concrete implementations is `backend/app/dependencies.py`. This is intentional. Every other file depends on interfaces.

---

## GitHub Releases

A GitHub Release is created at each major version tag. Each release includes:

- Tag: `vX.Y.Z-name`
- Release title: human-readable phase name
- Release notes: see `docs/RELEASE_NOTES_*.md`
- Attached artifacts: none (Docker image is built on HF Spaces, not distributed as a binary)

GitHub Releases serve as the **change log** and **stakeholder communication record** for the project.

---

## Branching Rules

| Action | Approach |
|--------|----------|
| New feature | Develop on `main` or a short-lived feature branch, merge to `main` |
| Phase boundary | Merge all phase work to `main`, tag, create GitHub Release |
| Hotfix | Apply directly to `main`, push to both remotes |
| Rollback | `git revert` on `main`, push — never force-push to a shared remote |
| Phase 2 exploration | Feature branch `phase2/identity-provider` → PR → merge to `main` |

---

## Deployment Checklist (Per Phase)

Before tagging a new version:

- [ ] All phase work merged to `main`
- [ ] `docker-compose up --build` runs clean locally
- [ ] All application screens load and behave correctly
- [ ] `git push origin main` — GitHub up to date
- [ ] `git push hf main:main` — HF Space rebuilt and live
- [ ] HF Space URL confirmed accessible
- [ ] Tag created: `git tag -a vX.Y.Z -m "Phase name"`
- [ ] Tag pushed: `git push origin vX.Y.Z`
- [ ] GitHub Release created with release notes
- [ ] `docs/RELEASE_NOTES_vX.Y.md` committed

See [`docs/VERSIONING_GUIDE.md`](VERSIONING_GUIDE.md) for exact commands.
