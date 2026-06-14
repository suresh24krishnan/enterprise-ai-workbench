"""Sprint 5 validation — run with: .venv/Scripts/python backend/tests/sprint5_validation.py"""

import json
import subprocess
import sys

errors = []
ok_count = 0


def ok(msg):
    global ok_count
    ok_count += 1
    print(f"PASS: {msg}")


def fail(msg):
    errors.append(msg)
    print(f"FAIL: {msg}")


# ---- 1. Supervisor imports ----
try:
    from backend.app.integration.supervisor.models import (
        ClaimIntent,
        GovernanceFlags,
        SupervisorRequest,
        SupervisorResponse,
        SupervisorStatus,
    )
    from backend.app.integration.supervisor.planner import build_plan, classify_intent
    from backend.app.integration.supervisor.governance import enforce_governance
    from backend.app.integration.supervisor.supervisor import run_supervisor
    ok("supervisor imports clean")
except Exception as exc:
    fail(f"supervisor import error: {exc}")
    sys.exit(1)

# ---- 2. Intent classification ----
cases = [
    ("claim_summary", ClaimIntent.CLAIM_SUMMARY),
    ("fraud_check", ClaimIntent.FRAUD_CHECK),
    ("coverage_analysis", ClaimIntent.COVERAGE_ANALYSIS),
    ("document_review", ClaimIntent.DOCUMENT_REVIEW),
    ("policy_lookup", ClaimIntent.POLICY_LOOKUP),
    ("fraud", ClaimIntent.FRAUD_CHECK),
    ("documents", ClaimIntent.DOCUMENT_REVIEW),
    ("coverage", ClaimIntent.COVERAGE_ANALYSIS),
    ("policy", ClaimIntent.POLICY_LOOKUP),
    ("summary", ClaimIntent.CLAIM_SUMMARY),
    ("UNKNOWN_GIBBERISH", ClaimIntent.CLAIM_SUMMARY),
]
for raw, expected in cases:
    got = classify_intent(raw)
    if got == expected:
        ok(f"classify_intent({raw!r}) -> {got.value}")
    else:
        fail(f"classify_intent({raw!r}) expected {expected.value} got {got.value}")

# ---- 3. Provider plans ----
plan_checks = {
    ClaimIntent.CLAIM_SUMMARY: ["claimcenter", "policycenter", "edw", "fraud", "email"],
    ClaimIntent.COVERAGE_ANALYSIS: ["claimcenter", "policycenter"],
    ClaimIntent.FRAUD_CHECK: ["claimcenter", "fraud"],
    ClaimIntent.DOCUMENT_REVIEW: ["documents"],
    ClaimIntent.POLICY_LOOKUP: ["policycenter", "edw"],
}
for intent, expected in plan_checks.items():
    plan = build_plan(intent)
    if plan == expected:
        ok(f"plan({intent.value}) = {plan}")
    else:
        fail(f"plan({intent.value}) expected {expected} got {plan}")

# ---- 4. Governance: MOCK mode passes ----
from backend.app.integration.bootstrap import _build_registry

reg = _build_registry()
try:
    enforce_governance(["claimcenter", "policycenter", "edw"], reg)
    ok("governance: MOCK providers pass")
except Exception as exc:
    fail(f"governance MOCK should pass: {exc}")

# ---- 5. Supervisor claim_summary ----
req = SupervisorRequest(claim_id="CLM-2026-100245", intent="claim_summary")
resp = run_supervisor(req, reg)
if resp.status == SupervisorStatus.SUCCESS:
    ok(f"supervisor claim_summary: status={resp.status.value}")
else:
    fail(f"supervisor claim_summary: status={resp.status.value}")
if resp.provider_count == 5:
    ok("supervisor claim_summary: 5 providers selected")
else:
    fail(f"supervisor claim_summary: expected 5 providers, got {resp.provider_count}")
if resp.succeeded_count == 5 and resp.failed_count == 0:
    ok(f"supervisor claim_summary: {resp.succeeded_count}/5 succeeded")
else:
    fail(f"supervisor claim_summary: succeeded={resp.succeeded_count} failed={resp.failed_count}")

# ---- 6. Execution trace ----
trace_providers = [t.provider for t in resp.execution_trace]
if trace_providers == ["claimcenter", "policycenter", "edw", "fraud", "email"]:
    ok(f"execution trace order: {trace_providers}")
else:
    fail(f"execution trace order wrong: {trace_providers}")
for t in resp.execution_trace:
    if t.status == "success" and t.latency_ms >= 0:
        ok(f"trace: {t.provider}.{t.method} -> {t.status} ({t.latency_ms}ms)")
    else:
        fail(f"trace: {t.provider}.{t.method} unexpected status={t.status}")

# ---- 7. Governance flags ----
gf = resp.governance_flags
assert gf.writes_enabled is False
assert gf.real_providers_rejected is True
assert gf.all_operations_read_only is True
assert gf.phase_2b_gate_open is False
ok(f"governance_flags: writes_enabled={gf.writes_enabled} real_rejected={gf.real_providers_rejected}")

# ---- 8. Aggregated result ----
ar = resp.aggregated_result
assert ar["intent"] == "claim_summary"
assert "providers" in ar
for pname in ["claimcenter", "policycenter", "edw", "fraud", "email"]:
    p = ar["providers"].get(pname)
    if p and p.get("status") == "success":
        ok(f"aggregated_result: {pname} status=success")
    else:
        fail(f"aggregated_result: {pname} missing or failed: {p}")

# ---- 9. Email body excluded (ADR-006) ----
agg_json = json.dumps(ar)
if "Dear ABC" not in agg_json:
    ok("email body text excluded from aggregated_result (ADR-006)")
else:
    fail("email body text in aggregated_result — ADR-006 violation")

# ---- 10. fraud_check intent ----
req2 = SupervisorRequest(claim_id="CLM-2026-100245", intent="fraud_check")
resp2 = run_supervisor(req2, reg)
assert resp2.status == SupervisorStatus.SUCCESS
assert resp2.selected_providers == ["claimcenter", "fraud"]
ok(f"fraud_check: {resp2.succeeded_count}/{resp2.provider_count} succeeded")

# ---- 11. document_review intent ----
req3 = SupervisorRequest(claim_id="CLM-2026-100245", intent="document_review")
resp3 = run_supervisor(req3, reg)
assert resp3.status == SupervisorStatus.SUCCESS
assert resp3.selected_providers == ["documents"]
doc_res = resp3.aggregated_result["providers"]["documents"]
assert doc_res["status"] == "success"
assert doc_res["document_count"] >= 5
ok(f"document_review: {doc_res['document_count']} documents aggregated")

# ---- 12. Unknown claim ID — no crash ----
req4 = SupervisorRequest(claim_id="CLM-UNKNOWN-99999", intent="claim_summary")
resp4 = run_supervisor(req4, reg)
assert resp4.status in [SupervisorStatus.PARTIAL, SupervisorStatus.SUCCESS, SupervisorStatus.FAILED]
ok(f"unknown claim_id: supervisor returns {resp4.status.value} (no crash)")

# ---- 13. Registry sole source ----
import inspect
from backend.app.integration.supervisor import executor as exec_mod

src = inspect.getsource(exec_mod)
direct = any(
    cls in src
    for cls in [
        "MockClaimCenterProvider()",
        "MockPolicyCenterProvider()",
        "MockEDWProvider()",
        "MockDocumentProvider()",
        "MockFraudProvider()",
        "MockEmailProvider()",
    ]
)
if not direct:
    ok("registry is sole provider source (no direct mock instantiation in executor)")
else:
    fail("executor instantiates providers directly — violates registry rule")

# ---- 14. Writes remain disabled ----
from backend.app.integration.mocks.errors import MockWriteDisabledError
from backend.app.integration.contracts.claimcenter import CreateClaimNoteRequest, NoteType
from backend.app.integration.contracts.common import ToolExecutionContext, ProviderMode

ctx = ToolExecutionContext(
    user_id="u", display_name="u", roles=[], permissions=[],
    correlation_id="c", trace_id="t", request_id="r",
    provider_mode=ProviderMode.MOCK, writes_enabled=False,
)
cc = reg.resolve("claimcenter")
try:
    cc.create_claim_note(
        CreateClaimNoteRequest(
            claim_id="CLM-2026-100245",
            note_type=NoteType.GENERAL,
            subject="s",
            body="b",
            approval_record_id="a",
            idempotency_key="i",
        ),
        ctx,
    )
    fail("write should have raised MockWriteDisabledError")
except MockWriteDisabledError:
    ok("writes remain disabled (MockWriteDisabledError)")

# ---- 15. Sprint 4 validation still passes ----
from backend.app.integration.validation.runner import RunMode, run_validation

report = run_validation(mode=RunMode.FULL)
if report.overall_status == "PASS" and report.passed == 6:
    ok(f"Sprint 4 validation: {report.overall_status} ({report.passed}/{report.total_providers})")
else:
    fail(f"Sprint 4 validation DEGRADED: {report.overall_status} ({report.passed}/{report.total_providers})")

# ---- 16. /api/integration/status unchanged ----
import backend.app.api.routes_integration as ri_mod
from backend.app.api.routes_integration import integration_status

ri_mod._last_validation = None
status_resp = integration_status()
assert status_resp.writes_enabled is False
assert status_resp.lab_safe is True
ok("/api/integration/status: unchanged and healthy")

# ---- 17. No frontend / Docker changes ----
result = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
changed = [f for f in result.stdout.strip().split("\n") if f]
frontend = [f for f in changed if "frontend" in f]
docker = [f for f in changed if any(k in f.lower() for k in ["dockerfile", "docker-compose"])]
if not frontend:
    ok("no frontend files changed")
else:
    fail(f"frontend changed: {frontend}")
if not docker:
    ok("no Docker files changed")
else:
    fail(f"Docker changed: {docker}")

# ---- 18. Production HF not pushed ----
hf_head = subprocess.run(
    ["git", "log", "hf/main", "-1", "--format=%H"], capture_output=True, text=True
)
local_head = subprocess.run(
    ["git", "log", "-1", "--format=%H"], capture_output=True, text=True
)
if hf_head.stdout.strip() != local_head.stdout.strip():
    ok(
        f"production HF not pushed "
        f"(hf/main={hf_head.stdout.strip()[:8]}, HEAD={local_head.stdout.strip()[:8]})"
    )
else:
    fail("production HF matches HEAD — push may have occurred")

# ---- 19. Latency ----
assert resp.latency_ms > 0
ok(f"latency recorded: {resp.latency_ms}ms total")

# ---- 20. Unique request IDs ----
resp_b = run_supervisor(SupervisorRequest(claim_id="CLM-2026-100245", intent="claim_summary"), reg)
assert resp.request_id != resp_b.request_id
ok("request_id is unique per call")

# ---- summary ----
print()
print(f"Results: {ok_count} PASS, {len(errors)} FAIL")
if errors:
    for e in errors:
        print(f"  FAIL: {e}")
    sys.exit(1)
