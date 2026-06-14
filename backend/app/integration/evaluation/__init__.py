"""
Evaluation Harness — Phase 2 Sprint 7

Deterministic quality gate for the Enterprise AI Workbench supervisor.
Measures AI orchestration quality against governed golden datasets.

This package is isolated — nothing imports it automatically.
Entrypoints: runner.py (programmatic), routes_evaluation.py (HTTP API).

NOT agentic. NOT autonomous. Does NOT execute provider calls directly.
Delegates to the existing supervisor and collects structured responses.
"""
