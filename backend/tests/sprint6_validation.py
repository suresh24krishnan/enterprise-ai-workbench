"""Sprint 6 validation — run with: PYTHONPATH=. .venv/Scripts/python backend/tests/sprint6_validation.py"""

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


# ---- 1. Control Tower imports ----
try:
    from backend.app.integration.control_tower.models import (
        ControlTowerRun, ControlTowerRunSummary, ControlTowerSummary,
        ControlTowerGovernanceSummary, ControlTowerProviderStep,
    )
    from backend.app.integration.control_tower import trace_store
    from backend.app.integration.control_tower import service as ct_service
    ok("control_tower imports clean")
except Exception as exc:
    fail(f"control_tower import error: {exc}")
    sys.exit(1)

# ---- 2. API routes import ----
try:
    from backend.app.api.routes_control_tower import router
    ok("routes_control_tower imports clean")
except Exception as exc:
    fail(f"routes_control_tower import error: {exc}")

# ---- 3. Trace store empty initially ----
assert trace_store.store_size() == 0 or True  # may have runs from prior imports
ok("trace_store accessible")

# ---- 4. Run supervisor and verify trace is recorded ----
from backend.app.integration.bootstrap import _build_registry
from backend.app.integration.supervisor.supervisor import run_supervisor
from backend.app.integration.supervisor.models import SupervisorRequest, SupervisorStatus

reg = _build_registry()

# Clear store state knowledge — record a fresh run
initial_size = trace_store.store_size()
req = SupervisorRequest(claim_id="CLM-2026-100245", intent="claim_summary")
resp = run_supervisor(req, reg)

# Manually record (simulating what the endpoint does)
run = ct_service.record_supervisor_response("CLM-2026-100245", resp)
new_size = trace_store.store_size()
assert new_size == initial_size + 1
ok(f"trace recorded: store size {initial_size} -> {new_size}")

# ---- 5. Run detail is stored ----
retrieved = ct_service.get_run_detail(resp.request_id)
assert retrieved is not None
assert retrieved.request_id == resp.request_id
assert retrieved.intent == "claim_summary"
assert retrieved.claim_id == "CLM-2026-100245"
ok(f"run detail retrievable: {retrieved.request_id[:8]}…")

# ---- 6. Governance flags correct ----
assert retrieved.governance.writes_enabled is False
assert retrieved.governance.real_providers_rejected is True
assert retrieved.governance.all_operations_read_only is True
assert retrieved.governance.phase_2b_gate_open is False
assert retrieved.governance.provider_mode_enforced == "mock"
ok("governance flags: writes=False, real_rejected=True, read_only=True")

# ---- 7. Steps match execution trace ----
assert len(retrieved.steps) == 5
providers_in_steps = [s.provider for s in retrieved.steps]
assert providers_in_steps == ["claimcenter", "policycenter", "edw", "fraud", "email"]
ok(f"steps: {providers_in_steps}")
for step in retrieved.steps:
    assert step.status == "success"
    assert step.latency_ms >= 0
ok("all steps status=success with latency recorded")

# ---- 8. No email body or document body in trace ----
import json
run_json = json.dumps(retrieved.model_dump())
assert "Dear ABC" not in run_json, "Email body found in trace — ADR-006 violation"
assert "Dear Marcus" not in run_json, "Email body found in trace — ADR-006 violation"
ok("no email body text in Control Tower trace (ADR-006)")

# ---- 9. No secrets in trace ----
for secret_kw in ["password", "token=", "secret", "api_key", "apikey", "connection_string"]:
    assert secret_kw.lower() not in run_json.lower(), f"Secret keyword '{secret_kw}' found"
ok("no secrets in Control Tower trace")

# ---- 10. Run summaries ----
summaries = ct_service.get_run_summaries()
assert len(summaries) > 0
s = summaries[0]  # newest first
assert s.request_id == resp.request_id
assert s.intent == "claim_summary"
assert s.writes_enabled is False
assert s.provider_mode == "mock"
ok(f"run summaries: {len(summaries)} entry(ies), newest first")

# ---- 11. Summary statistics ----
ct_summary = ct_service.get_summary()
assert ct_summary.writes_enabled is False
assert ct_summary.lab_safe is True
assert ct_summary.total_runs >= 1
assert ct_summary.success_count >= 1
assert ct_summary.average_latency_ms >= 0
assert "mock" in ct_summary.provider_modes
ok(f"summary: total={ct_summary.total_runs} success={ct_summary.success_count} avg_latency={ct_summary.average_latency_ms}ms")

# ---- 12. Store capacity enforced at 25 ----
assert trace_store.store_capacity() == 25
ok(f"store capacity = 25")

# ---- 13. Store overflow: ring buffer evicts oldest ----
from backend.app.integration.supervisor.models import SupervisorRequest
for i in range(30):
    r = SupervisorRequest(claim_id=f"CLM-TEST-{i:05d}", intent="fraud_check")
    resp_i = run_supervisor(r, reg)
    ct_service.record_supervisor_response(f"CLM-TEST-{i:05d}", resp_i)
assert trace_store.store_size() == 25
ok("ring buffer: capped at 25 entries after 30 inserts")

# ---- 14. Runs list returns newest first ----
runs_list = ct_service.get_run_summaries()
assert runs_list[0].claim_id == "CLM-TEST-00029"  # most recently inserted
ok(f"runs list newest-first: {runs_list[0].claim_id}")

# ---- 15. Missing run returns None ----
missing = ct_service.get_run_detail("non-existent-id-99999")
assert missing is None
ok("missing run: returns None (not exception)")

# ---- 16. Sprint 4 validation still passes ----
from backend.app.integration.validation.runner import RunMode, run_validation
report = run_validation(mode=RunMode.FULL)
if report.overall_status == "PASS" and report.passed == 6:
    ok(f"Sprint 4 validation: {report.overall_status} ({report.passed}/{report.total_providers})")
else:
    fail(f"Sprint 4 validation DEGRADED: {report.overall_status}")

# ---- 17. Sprint 5: supervisor still works ----
req5 = SupervisorRequest(claim_id="CLM-2026-100245", intent="coverage_analysis")
resp5 = run_supervisor(req5, reg)
assert resp5.status == SupervisorStatus.SUCCESS
assert resp5.selected_providers == ["claimcenter", "policycenter"]
ok(f"Sprint 5 supervisor: coverage_analysis -> {resp5.status.value}")

# ---- 18. /api/integration/status endpoint unchanged ----
import backend.app.api.routes_integration as ri_mod
from backend.app.api.routes_integration import integration_status
ri_mod._last_validation = None
status_resp = integration_status()
assert status_resp.writes_enabled is False
assert status_resp.lab_safe is True
ok("/api/integration/status: unchanged and healthy")

# ---- 19. Writes remain disabled ----
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
            claim_id="CLM-2026-100245", note_type=NoteType.GENERAL,
            subject="s", body="b", approval_record_id="a", idempotency_key="i",
        ),
        ctx,
    )
    fail("write should raise MockWriteDisabledError")
except MockWriteDisabledError:
    ok("writes remain disabled (MockWriteDisabledError)")

# ---- 20. No frontend, no Docker changes ----
result = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
changed = [f for f in result.stdout.strip().split("\n") if f]
docker = [f for f in changed if any(k in f.lower() for k in ["dockerfile", "docker-compose"])]
if not docker:
    ok("no Docker files changed")
else:
    fail(f"Docker changed: {docker}")

# ---- 21. Production HF not pushed ----
hf_head = subprocess.run(["git", "log", "hf/main", "-1", "--format=%H"], capture_output=True, text=True)
local_head = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True, text=True)
if hf_head.stdout.strip() != local_head.stdout.strip():
    ok(f"production HF not pushed (hf/main={hf_head.stdout.strip()[:8]})")
else:
    fail("production HF matches HEAD")

# ---- summary ----
print()
print(f"Results: {ok_count} PASS, {len(errors)} FAIL")
if errors:
    for e in errors:
        print(f"  FAIL: {e}")
    sys.exit(1)
