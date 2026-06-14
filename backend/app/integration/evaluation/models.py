"""Evaluation framework data models — pure Pydantic, no provider logic."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────


class EvalStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class RegressionType(str, Enum):
    MISSING_PROVIDER      = "missing_provider"
    UNEXPECTED_PROVIDER   = "unexpected_provider"
    PROVIDER_FAILURE      = "provider_failure"
    WRITE_ENABLED         = "write_enabled"
    REAL_PROVIDER_ENABLED = "real_provider_enabled"
    LATENCY_EXCEEDED      = "latency_exceeded"
    WRONG_EXECUTION_ORDER = "wrong_execution_order"
    WRONG_PROVIDER_COUNT  = "wrong_provider_count"
    WRONG_SUCCESS_COUNT   = "wrong_success_count"


# ── Golden dataset models ─────────────────────────────────────────────────


class GoldenExpectation(BaseModel):
    """What a correct supervisor execution must produce for a scenario."""

    expected_providers:       list[str]
    expected_provider_count:  int
    expected_success_count:   int
    writes_expected:          bool = False
    real_providers_expected:  bool = False
    max_latency_ms:           float = 500.0
    execution_order_strict:   bool = True


class GoldenScenario(BaseModel):
    """A single deterministic evaluation scenario."""

    scenario_id:   str
    name:          str
    description:   str
    claim_id:      str
    intent:        str
    expectation:   GoldenExpectation
    version:       str = "1.0"
    tags:          list[str] = Field(default_factory=list)


# ── Scoring models ────────────────────────────────────────────────────────


class EvaluationMetric(BaseModel):
    """A single scored dimension."""

    name:        str
    score:       float          # 0.0 – 1.0
    weight:      float          # relative weight (0–100)
    weighted:    float          # score * weight
    passed:      bool
    reason:      str


class EvaluationScore(BaseModel):
    """Aggregated score across all dimensions."""

    provider_selection:  EvaluationMetric
    execution_success:   EvaluationMetric
    governance:          EvaluationMetric
    write_safety:        EvaluationMetric
    latency:             EvaluationMetric
    determinism:         EvaluationMetric
    overall_score:       float          # 0–100
    overall_passed:      bool
    pass_threshold:      float = 80.0


# ── Regression models ─────────────────────────────────────────────────────


class RegressionResult(BaseModel):
    """A detected deviation from the golden expectation."""

    regression_type: RegressionType
    severity:        str           # "critical" | "warning"
    detail:          str
    expected:        Any | None = None
    actual:          Any | None = None


# ── Run models ────────────────────────────────────────────────────────────


class EvaluationRequest(BaseModel):
    """Input to a single evaluation run."""

    scenario_id: str
    label:       str | None = None


class EvaluationResult(BaseModel):
    """Outcome of running one golden scenario through the supervisor."""

    run_id:       str
    scenario_id:  str
    scenario_name: str
    claim_id:     str
    intent:       str

    # What we expected
    expectation:  GoldenExpectation

    # What the supervisor produced
    actual_providers:     list[str]
    actual_provider_count: int
    actual_success_count:  int
    actual_latency_ms:    float
    actual_status:        str
    actual_writes_enabled: bool
    actual_provider_mode: str

    # Scoring
    score:       EvaluationScore
    regressions: list[RegressionResult]

    # Outcome
    status:       EvalStatus
    passed:       bool
    reason:       str
    recorded_at:  str
    version:      str = "1.0"


# ── Summary models ────────────────────────────────────────────────────────


class EvaluationRun(BaseModel):
    """Lightweight record stored in the evaluation store."""

    run_id:         str
    scenario_id:    str
    scenario_name:  str
    claim_id:       str
    intent:         str
    overall_score:  float
    passed:         bool
    regression_count: int
    latency_ms:     float
    recorded_at:    str


class EvaluationSummary(BaseModel):
    """Aggregate health across all evaluation runs in the store."""

    total_runs:       int
    pass_count:       int
    fail_count:       int
    pass_rate:        float          # 0.0–1.0
    average_score:    float
    regression_count: int
    last_run_at:      str | None
    last_run_id:      str | None
    store_used:       int
    store_capacity:   int
    writes_enabled:   bool = False
    lab_safe:         bool = True
