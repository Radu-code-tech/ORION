# MOD-001 — OR-CORE-001 Scheduler v1.0

## Purpose
Provide deterministic scheduling of internal ORION jobs without embedding market, risk, execution, or decision logic.

## Responsibilities
- Register jobs.
- Validate job definitions.
- Start and stop the scheduler.
- Execute jobs when due.
- Reschedule successful dispatches.
- Remain deterministic and testable through an injectable clock.

## Non-responsibilities
The Scheduler does not:
- generate BUY/SELL/NO TRADE decisions;
- calculate trading signals;
- manage risk;
- place orders;
- fetch market data;
- learn from trades.

Those responsibilities belong to later ORION components.

## Design choice
`tick()` is intentionally non-blocking. A higher-level runtime will determine the polling cadence. This keeps OR-CORE-001 small, testable, and independent of operating-system scheduling facilities.

## Acceptance criteria
1. Invalid jobs are rejected.
2. Duplicate job names are rejected.
3. A stopped scheduler executes nothing.
4. A started scheduler executes due jobs.
5. Jobs are not executed before their next due time.
6. The clock is injectable for deterministic tests.

## Current status
Implementation v1.0 — initial kernel component.
