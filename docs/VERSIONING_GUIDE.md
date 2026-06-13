# Versioning Guide — Enterprise AI Workbench

## Tag Naming Strategy

Tags use [Semantic Versioning](https://semver.org/) with an optional phase suffix for major milestones.

```
v{MAJOR}.{MINOR}.{PATCH}[-{label}]
```

| Segment | When to increment |
|---------|-------------------|
| `MAJOR` | Breaking architecture change, new platform generation |
| `MINOR` | New phase capability, new adapter integration, new business domain |
| `PATCH` | Bug fix, documentation update, minor UI change within a phase |
| `-label` | Optional human-readable phase identifier on milestone tags |

### Current Tag History

| Tag | SHA | Description |
|-----|-----|-------------|
| `v1.0.0-phase1` | `d2c6989` | Phase 1 MVP Freeze — Reference Implementation |

### Planned Tags

| Tag | Milestone |
|-----|-----------|
| `v1.1.0-phase2` | Sandbox Integration complete |
| `v1.2.0` | Azure OpenAI + RAG integration |
| `v2.0.0` | Enterprise Platform — multi-domain |

---

## Release Naming Strategy

GitHub Release titles follow this pattern:

```
Phase {N}: {Short Name} — v{X.Y.Z}
```

Examples:
- `Phase 1: Reference Implementation — v1.0.0`
- `Phase 2: Sandbox Integration — v1.1.0`
- `Phase 3: Enterprise Platform — v2.0.0`

Patch releases use a shorter title:
```
v1.0.1 — Bug fix: {one-line description}
```

---

## When to Create Tags

Create a tag when:
- A phase is complete and the HF Space is live and verified
- A significant integration milestone is reached (first real adapter wired)
- A stakeholder demo is being prepared and a stable reference point is needed
- A GitHub Release is being created (a release must point to a tag)

Do NOT create a tag for:
- Work-in-progress commits
- Documentation-only changes (unless they mark a phase boundary)
- Minor fixes mid-phase

---

## When to Create GitHub Releases

Create a GitHub Release when:
- A new version tag is created at a phase boundary
- Stakeholders need a formal change record with release notes
- A public-facing milestone is being communicated to leadership

One release per minor/major version tag. Patch releases are optional — create a release only if the patch fixes something stakeholder-visible.

---

## Recommended Commands

### View existing tags

```bash
git tag --list
git tag --list --sort=-version:refname   # sorted newest first
```

### Create an annotated tag

```bash
git tag -a v1.1.0-phase2 -m "Phase 2: Sandbox Integration"
```

Always use annotated tags (`-a`), not lightweight tags. Annotated tags include the tagger name, date, and message — required for GitHub Releases.

### Push a tag to GitHub

```bash
git push origin v1.1.0-phase2
```

### Push a tag to Hugging Face

```bash
git push hf v1.1.0-phase2
```

### Push all local tags

```bash
git push origin --tags
```

### List tags with their commit SHAs

```bash
git tag -l --format='%(refname:short) %(objectname:short) %(contents:subject)'
```

### Delete a local tag (if created in error)

```bash
git tag -d v1.1.0-phase2
```

### Delete a remote tag (use with caution)

```bash
git push origin --delete v1.1.0-phase2
```

---

## Full Phase Boundary Workflow

Use this sequence when completing a phase and tagging a release.

```bash
# 1. Confirm working tree is clean
git status

# 2. Confirm all phase work is merged to main
git log --oneline -10

# 3. Verify Docker build
docker-compose up --build

# 4. Push to GitHub
git push origin main

# 5. Push to Hugging Face (triggers Space rebuild)
git push hf main:main

# 6. Confirm HF Space is live at the expected URL
# https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench

# 7. Create annotated tag
git tag -a v1.1.0-phase2 -m "Phase 2: Sandbox Integration — real identity, ClaimCenter sandbox, PostgreSQL"

# 8. Push tag to GitHub
git push origin v1.1.0-phase2

# 9. Create GitHub Release via gh CLI
gh release create v1.1.0-phase2 \
  --title "Phase 2: Sandbox Integration — v1.1.0" \
  --notes-file docs/RELEASE_NOTES_v1.1.md

# 10. Confirm release is visible on GitHub
gh release view v1.1.0-phase2
```

---

## Branch and Remote Reference

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | `https://github.com/suresh24krishnan/enterprise-ai-workbench.git` | Source of truth, GitHub Releases, CI |
| `hf` | `https://huggingface.co/spaces/sureshkrishnan/enterprise-ai-workbench` | Live deployment — push triggers Docker build |

Both remotes always point to the same commit on `main`. After any push to `hf`, push to `origin` immediately to keep them aligned.
