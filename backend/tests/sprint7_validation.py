"""Sprint 7 validation — run with: PYTHONPATH=. .venv/Scripts/python backend/tests/sprint7_validation.py"""

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


# ── 1. Package imports ─────────────────────────────────────────────────────
try:
    from backend.app.integration.evaluation.models import (
        GoldenScenario, GoldenExpectation,
        EvaluationResult, EvaluationScore, EvaluationMetric,
        EvaluationRequest, EvaluationRun, EvaluationSummary,
        RegressionResult, RegressionType, EvalStatus,
    )
    ok("evaluation models import clean")
except Exception as exc:
    fail(f"models import: {exc}")
    sys.exit(1)

try:
    from backend.app.integration.evaluation.golden_dataset import (
        list_scenarios, get_scenario, scenario_count,
    )
    ok("golden_dataset import clean")
except Exception as exc:
    fail(f"golden_dataset import: {exc}")
    sys.exit(1)

try:
    from backend.app.integration.evaluation.scoring import score_execution, PASS_THRESHOLD
    ok("scoring import clean")
except Exception as exc:
    fail(f"scoring import: {exc}")
    sys.exit(1)

try:
    from backend.app.integration.evaluation.metrics import detect_regressions
    ok("metrics import clean")
except Exception as exc:
    fail(f"metrics import: {exc}")
    sys.exit(1)

try:
    from backend.app.integration.evaluation import runner as eval_runner
    ok("runner import clean")
except Exception as exc:
    fail(f"runner import: {exc}")
    sys.exit(1)

try:
    from backend.app.api.routes_evaluation import router
    ok("routes_evaluation import clean")
except Exception as exc:
    fail(f"routes_evaluation import: {exc}")
    sys.exit(1)


# ── 2. Golden dataset ──────────────────────────────────────────────────────
scenarios = list_scenarios()
if len(scenarios) == 10:
    ok(f"10 golden scenarios loaded")
else:
    fail(f"expected 10 scenarios, got {len(scenarios)}")

# Spot-check each scenario has required fields
for s in scenarios:
    assert s.scenario_id, f"missing scenario_id: {s}"
    assert s.claim_id, f"missing claim_id: {s.scenario_id}"
    assert s.intent, f"missing intent: {s.scenario_id}"
    assert s.expectation.expected_providers, f"empty providers: {s.scenario_id}"
    assert not s.expectation.writes_expected, f"writes_expected=True: {s.scenario_id}"
    assert not s.expectation.real_providers_expected, f"real_expected=True: {s.scenario_id}"
ok("all 10 scenarios have valid fields (no writes, no real providers)")

# Lookup
gs1 = get_scenario("GS-001")
assert gs1 is not None and gs1.scenario_id == "GS-001"
assert get_scenario("NONEXISTENT") is None
ok("scenario lookup: found GS-001, missing returns None")

# Intent coverage
intents = {s.intent for s in scenarios}
assert "claim_summary" in intents
assert "coverage_analysis" in intents
assert "fraud_check" in intents
assert "document_review" in intents
assert "policy_lookup" in intents
ok(f"intent coverage: {sorted(intents)}")


# ── 3. Scoring engine — deterministic ─────────────────────────────────────
exp = gs1.expectation

# Perfect run
score_a = score_execution(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
assert score_a.overall_score == 100.0, f"expected 100, got {score_a.overall_score}"
assert score_a.overall_passed is True
ok(f"perfect run score: {score_a.overall_score}/100 PASS")

# Same input → same score (determinism)
score_b = score_execution(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
assert score_a.overall_score == score_b.overall_score
ok("scoring deterministic: same input -> same score")

# Provider mismatch drops score
score_c = score_execution(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter"],  # missing edw, fraud, email
    actual_success_count=2,
    actual_provider_count=2,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
assert score_c.overall_score < 100.0
assert not score_c.overall_passed
ok(f"provider mismatch drops score: {score_c.overall_score}/100 FAIL")

# Write enabled drops to FAIL
score_d = score_execution(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=True,   # violation
    actual_provider_mode="mock",
)
assert not score_d.write_safety.passed
assert score_d.write_safety.score == 0.0
ok(f"write_enabled drops write_safety score to 0: overall={score_d.overall_score}")

# Weights sum to 100
weights_sum = (
    score_a.provider_selection.weight +
    score_a.execution_success.weight +
    score_a.governance.weight +
    score_a.write_safety.weight +
    score_a.latency.weight +
    score_a.determinism.weight
)
assert weights_sum == 100.0, f"weights sum {weights_sum} != 100"
ok(f"scoring weights sum to {weights_sum}")

assert PASS_THRESHOLD == 80.0
ok(f"pass threshold = {PASS_THRESHOLD}")


# ── 4. Regression engine ───────────────────────────────────────────────────
# No regressions on perfect run
regs = detect_regressions(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
assert regs == [], f"expected no regressions, got {regs}"
ok("perfect run: 0 regressions")

# Missing provider
regs_missing = detect_regressions(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter"],
    actual_success_count=2,
    actual_provider_count=2,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
types = {r.regression_type for r in regs_missing}
assert RegressionType.MISSING_PROVIDER in types
ok(f"missing provider detected: {[r.regression_type.value for r in regs_missing]}")

# Write enabled
regs_write = detect_regressions(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=True,
    actual_provider_mode="mock",
)
assert any(r.regression_type == RegressionType.WRITE_ENABLED for r in regs_write)
ok("write_enabled regression detected")

# Real provider
regs_real = detect_regressions(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=1.5,
    actual_writes_enabled=False,
    actual_provider_mode="hybrid",  # violation
)
assert any(r.regression_type == RegressionType.REAL_PROVIDER_ENABLED for r in regs_real)
ok("real_provider_enabled regression detected")

# Latency exceeded
regs_lat = detect_regressions(
    expectation=exp,
    actual_providers=["claimcenter", "policycenter", "edw", "fraud", "email"],
    actual_success_count=5,
    actual_provider_count=5,
    actual_latency_ms=999.0,  # over 500ms limit
    actual_writes_enabled=False,
    actual_provider_mode="mock",
)
assert any(r.regression_type == RegressionType.LATENCY_EXCEEDED for r in regs_lat)
ok("latency_exceeded regression detected")


# ── 5. Runner — end-to-end ─────────────────────────────────────────────────
from backend.app.integration.bootstrap import _build_registry

reg = _build_registry()
initial_size = eval_runner.store_size()

result = eval_runner.run_scenario("GS-001", reg)

assert eval_runner.store_size() == initial_size + 1
assert result.scenario_id == "GS-001"
assert result.passed is True
assert result.score.overall_score == 100.0
assert result.status == EvalStatus.PASS
assert result.actual_writes_enabled is False
assert result.actual_provider_mode == "mock"
ok(f"runner GS-001: score={result.score.overall_score} status={result.status.value}")

# Retrieve from store
retrieved = eval_runner.get_result(result.run_id)
assert retrieved is not None
assert retrieved.run_id == result.run_id
ok(f"get_result: retrieved run {result.run_id[:8]}...")

# Missing returns None
assert eval_runner.get_result("nonexistent-run-id") is None
ok("get_result: missing returns None")


# ── 6. Run all 10 scenarios ────────────────────────────────────────────────
all_results = eval_runner.run_all_scenarios(reg)
assert len(all_results) == 10, f"expected 10 results, got {len(all_results)}"
all_passed = all(r.passed for r in all_results)
assert all_passed, f"some scenarios failed: {[(r.scenario_id, r.reason) for r in all_results if not r.passed]}"
ok(f"all 10 golden scenarios PASS (scores: {[r.score.overall_score for r in all_results]})")


# ── 7. Summary API ────────────────────────────────────────────────────────
summary = eval_runner.get_summary()
assert summary.total_runs >= 11  # 1 from step 5 + 10 from step 6
assert summary.pass_count >= 11
assert summary.writes_enabled is False
assert summary.lab_safe is True
assert 0.0 <= summary.pass_rate <= 1.0
ok(f"summary: total={summary.total_runs} pass={summary.pass_count} rate={summary.pass_rate:.2f}")


# ── 8. Recent runs API ────────────────────────────────────────────────────
runs = eval_runner.get_recent_runs()
assert len(runs) > 0
r0 = runs[0]
assert r0.run_id
assert r0.scenario_id
assert r0.passed is True
ok(f"get_recent_runs: {len(runs)} runs, newest={r0.scenario_id}")


# ── 9. Recommendation ────────────────────────────────────────────────────
rec = eval_runner.get_recommendation(result.run_id)
assert rec is not None
assert "PROMOTE" in rec
ok(f"recommendation for passed run: '{rec[:60]}...'")


# ── 10. API router prefix ─────────────────────────────────────────────────
assert router.prefix == "/api/integration/evaluation"
ok(f"routes_evaluation prefix: {router.prefix}")


# ── 11. Regression baselines — Sprint 4/5/6 still pass ───────────────────
from backend.app.integration.validation.runner import RunMode, run_validation
report = run_validation(mode=RunMode.FULL)
if report.overall_status == "PASS" and report.passed == 6:
    ok(f"Sprint 4 validation: {report.overall_status} ({report.passed}/6)")
else:
    fail(f"Sprint 4 DEGRADED: {report.overall_status}")

from backend.app.integration.supervisor.models import SupervisorRequest, SupervisorStatus
from backend.app.integration.supervisor.supervisor import run_supervisor

resp5 = run_supervisor(SupervisorRequest(claim_id="CLM-SPRINT5-CHECK", intent="fraud_check"), reg)
assert resp5.status == SupervisorStatus.SUCCESS
assert resp5.selected_providers == ["claimcenter", "fraud"]
ok(f"Sprint 5 supervisor: fraud_check -> {resp5.status.value}")

from backend.app.integration.control_tower import trace_store
from backend.app.integration.control_tower import service as ct_service

ct_size_before = trace_store.store_size()
ct_req = SupervisorRequest(claim_id="CLM-CT-CHECK", intent="coverage_analysis")
ct_resp = run_supervisor(ct_req, reg)
ct_service.record_supervisor_response("CLM-CT-CHECK", ct_resp)
assert trace_store.store_size() == ct_size_before + 1
ok(f"Sprint 6 Control Tower: trace recorded, store size {trace_store.store_size()}")


# ── 12. Writes still disabled ─────────────────────────────────────────────
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
            claim_id="CLM-WRITE-CHECK", note_type=NoteType.GENERAL,
            subject="s", body="b", approval_record_id="a", idempotency_key="i",
        ),
        ctx,
    )
    fail("write should raise MockWriteDisabledError")
except MockWriteDisabledError:
    ok("writes remain disabled (MockWriteDisabledError)")


# ── 13. No Docker changes ─────────────────────────────────────────────────
result_git = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
changed = [f for f in result_git.stdout.strip().split("\n") if f]
docker = [f for f in changed if any(k in f.lower() for k in ["dockerfile", "docker-compose"])]
if not docker:
    ok("no Docker files changed")
else:
    fail(f"Docker changed: {docker}")

# ── 14. Production HF not pushed ─────────────────────────────────────────
hf_head   = subprocess.run(["git", "log", "hf/main", "-1", "--format=%H"], capture_output=True, text=True)
local_head = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True, text=True)
if hf_head.stdout.strip() != local_head.stdout.strip():
    ok(f"production HF not pushed (hf/main={hf_head.stdout.strip()[:8]})")
else:
    fail("production HF matches HEAD — not pushed check failed")


# ── Summary ───────────────────────────────────────────────────────────────
print()
print(f"Results: {ok_count} PASS, {len(errors)} FAIL")
if errors:
    for e in errors:
        print(f"  FAIL: {e}")
    sys.exit(1)
