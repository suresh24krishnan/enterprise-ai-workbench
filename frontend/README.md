# Enterprise AI Workbench — Frontend

React 18 + Vite 5 + TypeScript + Tailwind CSS shell for the Claims AI Workbench.

## Prerequisites

- Node.js 20+
- Backend running on port 8000 (see `../backend/README.md`)

## Setup

```bash
cd frontend
npm install
```

## Run (development)

```bash
npm run dev
```

Opens at **http://localhost:5173**. The Vite dev server proxies `/api/*` and `/health` to the backend on `http://localhost:8000` — no CORS config needed.

## Type check

```bash
npx tsc --noEmit
```

## Build

```bash
npm run build
```

Output in `dist/`.

## Environment

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | *(empty)* | Override API base URL. Leave empty to use the Vite proxy. |

The empty default is correct for local dev. Set to `http://localhost:8000` only if running the built output outside Vite.

## Demo credentials (Phase 1 mock)

| Field | Value |
|---|---|
| Email | `john.smith@workbench.local` |
| Password | any value |
| Role | ADJUSTER |

## Pages

| Route | Description |
|---|---|
| `/login` | Mock SSO login |
| `/home` | Claims workbench dashboard |
| `/claims/:id/summary` | AI-generated claim summary with governance and evidence |
| `/claims/:id/audit` | Immutable audit trail |

## Architecture

- `src/lib/api.ts` — all API calls; types from `src/types/index.ts` (snake_case to match backend responses)
- `src/components/layout/` — AppLayout, Sidebar, ClaimContextBar
- `src/components/ui/` — GovernanceBadge, EvidenceSourceCard, AuditEventRow
- `src/pages/` — one file per route

## Design Constraints

- Calls only the Backend REST API — never calls AI models or adapters directly
- All AI interactions flow through the governed backend pipeline
- Governance decisions (ALLOW / DENY / ESCALATE) are displayed on every AI-generated surface
- Human approval is a first-class UI element

## Phase Evolution

No frontend code changes are required between phases — only environment variables change.

| Phase | Change |
|---|---|
| 1 | Mock auth, local API (current) |
| 2+ | SSO redirect, sandbox API URL |
| 3 | Production API URL (config only) |
