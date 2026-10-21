# DOC-004 — ORION Master Roadmap v1.0

## Status
DRAFT — Pending Owner Acceptance.

## 1. Purpose
Define the remaining ORION v1.0 development modules,
their dependencies, deliverables, validation gates,
and final system acceptance criteria.

## 2. Reference Architecture
- DOC-000 Project Index v1.0
- DOC-001 ORION Foundation v1.1
- DOC-003 Software Architecture v1.1
- DOC-010 Repository Bootstrap v1.0
- Approved specifications and designs MOD-001 through MOD-008

## 3. Completed Baseline
MOD-001 through MOD-008 are integrated in main.

Baseline merge commit: c258c1c
Baseline automated tests: 290 passed.

## 4. Remaining Modules

### MOD-009 — Trend Engine
Purpose: Deterministic trend and market regime analysis.
Outputs: Trend direction, strength, regime and supporting context.
Excludes: Trading decisions, position sizing and execution.

### MOD-010 — Alpha / Opportunity Engine
Purpose: Identify and evaluate trading opportunities.
Outputs: Opportunity candidates, scores and supporting evidence.
Excludes: Final trading authorization and execution.

### MOD-011 — Decision Engine / Alpha Core
Purpose: Convert validated inputs into preliminary decisions.
Outputs: BUY, SELL or NO_TRADE with reasons and traceability.
Excludes: Risk bypass, order placement and broker operations.

### MOD-012 — Execution Engine
Purpose: Safely process risk-authorized trading instructions.
Outputs: Order lifecycle events, execution records and reconciliation.
Excludes: Independent trading decisions and autonomous risk overrides.

### MOD-013 — Performance & Validation
Purpose: Measure, reproduce and validate trading performance.
Outputs: Backtests, KPI reports, drawdown and validation results.
Excludes: Modification of historical evidence and unauthorized execution.

### MOD-014 — Adaptive Learning & Controlled Upgrade
Purpose: Evaluate candidate improvements in isolated experiments.
Outputs: Versioned proposals, experiment results and rollback plans.
Excludes: Unapproved production modifications.

## 5. Architectural Invariants

1. All modules must preserve deterministic behavior where specified.
2. Market Memory shall not depend on Decision Engine.
3. Evidence Engine shall not generate trading decisions.
4. Risk Manager cannot be bypassed by Decision or Execution.
5. Invalid or missing safety-critical inputs must fail closed.
6. Production changes require explicit Owner Acceptance.
7. Existing public contracts remain stable unless changes are approved.

## 5A. Module Dependency Matrix

Dependencies are architectural proposals.
Exact interfaces require Specification and Design approval.

| Module | Upstream dependencies | Primary output |
|---|---|---|
| MOD-009 Trend Engine | MOD-003 Market Data; MOD-004 Market Structure | Trend and market regime |
| MOD-010 Alpha / Opportunity | MOD-009 Trend; MOD-008 Liquidity; MOD-006 Evidence; MOD-007 Market Memory | Evaluated opportunities |
| MOD-011 Decision Engine | MOD-010 Alpha; MOD-006 Evidence; MOD-007 Market Memory | Preliminary BUY / SELL / NO_TRADE |
| MOD-012 Execution Engine | MOD-011 Decision; MOD-005 Risk Manager | Authorized order lifecycle |
| MOD-013 Performance & Validation | Historical data; decisions; simulated executions | Backtests, KPIs and validation |
| MOD-014 Adaptive Learning | MOD-013 Performance; MOD-006 Evidence; MOD-007 Market Memory | Versioned improvement proposals |

### Dependency Constraints

1. MOD-009 shall not depend on MOD-010 through MOD-014.
2. MOD-010 shall not issue final trading decisions or orders.
3. MOD-011 shall produce preliminary decisions only.
4. MOD-012 shall require valid risk authorization before execution.
5. MOD-013 shall preserve historical evidence and evaluation results.
6. MOD-014 shall not autonomously modify production code or configuration.
7. Circular dependencies are prohibited.

## 6. Development Lifecycle
Specification -> Design -> Implementation (TDD) ->
Testing -> Validation -> Owner Acceptance -> Merge -> Publish.

## 6A. Module Acceptance Criteria

All modules require approved Specification and Design,
automated tests, documented validation results,
and explicit Owner Acceptance before merge.

### MOD-009 - Trend Engine
- Deterministic results for identical inputs and configuration.
- Correct handling of bullish, bearish and neutral regimes.
- Explicit handling of conflicting timeframes.
- No lookahead or future-data leakage.
- Safe behavior for insufficient or invalid data.

### MOD-010 - Alpha / Opportunity Engine
- Reproducible opportunity scoring and ranking.
- Traceable inputs and supporting evidence.
- Defined filtering and rejection behavior.
- No final trading decisions or order submission.
- Safe handling of incomplete market information.

### MOD-011 - Decision Engine
- Deterministic BUY / SELL / NO_TRADE decisions.
- Documented decision rationale and evidence references.
- Explicit conflict-resolution rules.
- NO_TRADE on unresolved safety-critical conditions.
- No bypass of the Risk Manager.

### MOD-012 - Execution Engine
- Paper-trading execution supported.
- Valid risk authorization required before order submission.
- Duplicate order prevention and idempotency.
- Complete order-state tracking and reconciliation.
- Safe handling of rejection, timeout and disconnection.
- No automatic live-trading authorization.

### MOD-013 - Performance & Validation
- Reproducible backtesting with versioned inputs.
- Explicit fees, spread and slippage assumptions.
- Out-of-sample and walk-forward evaluation.
- P&L, drawdown and risk-adjusted KPI reporting.
- No lookahead, survivorship or data leakage.
- Traceable results and documented limitations.

### MOD-014 - Adaptive Learning & Controlled Upgrade
- Versioned improvement proposals.
- Isolated experiments with reproducible results.
- Comparison against an approved baseline.
- Detection of performance degradation.
- Documented rollback and recovery procedures.
- No autonomous promotion to production.
- Explicit Owner Acceptance for upgrades.

## 7. Release Gate — ORION v1.0
The final release requires:
- All approved automated tests passing.
- End-to-end integration validation.
- No unresolved critical safety defects.
- Reproducible backtesting with realistic trading costs.
- Out-of-sample and walk-forward evaluation.
- Stress and failure-recovery testing.
- Validated paper trading and order reconciliation.
- Documented security and operational controls.
- Rollback procedures.
- Explicit final Owner Acceptance.

## 8. Performance Objective
Target: evaluate whether the system can support a
net annualized return of at least 25%.

This is a research and validation objective,
not a guaranteed return or automatic release criterion.

## 9. Repository Governance
DOC-010 remains authoritative until a branching-policy
amendment is explicitly approved.

The established module workflow is documented as a
proposed convention; it does not silently supersede DOC-010.

## 9A. Architecture and Branching Compatibility

### Architecture Identifiers
Approved module-level specifications and designs define
the implementation identifiers and software contracts.

Legacy or generic identifiers in DOC-003 must be
reconciled through an explicitly approved documentation
revision or Architecture Decision Record (ADR).

No existing approved contract may be silently renamed.

### Git Branching Governance
DOC-010 remains the authoritative branching policy.

The module-specific branch workflow used during previous
development is recorded as an operational precedent,
not as an automatic amendment to DOC-010.

Any permanent branching-policy change requires
explicit approval and traceable documentation.

No merge into main is permitted without Owner Acceptance.

## 10. Release Status
ORION v1.0 remains IN DEVELOPMENT.

Completion of MOD-014 alone does not authorize live trading.
Live activation requires a separate approval decision.
