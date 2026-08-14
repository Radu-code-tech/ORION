# MOD-004 — OR-MSE-001 Market Structure v1.0

## Purpose
Provide a deterministic first-pass Market Structure Engine (MSE) for ORION.

## Scope
- classify ordered OHLC bars as BULLISH, BEARISH, RANGE, or INSUFFICIENT_DATA
- validate minimum input size
- use higher-high/higher-low and lower-high/lower-low progression
- remain independent from trading signals, risk, execution, and broker connectivity

## Non-goals
No order execution, indicators, prediction, scoring, signal generation, or live data acquisition.

## Acceptance criteria
1. Rising highs and lows produce BULLISH.
2. Falling highs and lows produce BEARISH.
3. Mixed progression produces RANGE.
4. Insufficient bars produce INSUFFICIENT_DATA.
5. Invalid minimum-bars configuration is rejected.
6. Unit tests pass independently.
7. The module can be integrated into the existing ORION repository without modifying prior modules.
