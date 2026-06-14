"""
Supervisor layer — deterministic tool orchestration for claim intelligence.

Orchestrates enterprise provider calls through the registry using a
fixed execution model: interpret intent → plan providers → execute
read-only calls → aggregate responses → return structured result.

NOT agentic. NOT autonomous. NOT LLM-driven planning.

The supervisor is deterministic: for a given intent, the same set of
providers is always selected and executed in the same order. There is
no randomness, no dynamic re-planning, and no self-modification.

Sprint 5 restriction: MOCK providers only.
Writes remain disabled (ADR-002 Phase 2B gate not satisfied).
"""
