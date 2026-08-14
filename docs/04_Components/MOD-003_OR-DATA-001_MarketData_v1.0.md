# MOD-003 — OR-DATA-001 Market Data v1.0

## Purpose
Provide a deterministic, validated in-memory OHLCV data store for downstream ORION components.

## Scope
- validated OHLCV market bars
- symbol/timeframe/timestamp identity
- batch insertion
- chronological retrieval
- latest-bar lookup
- duplicate rejection
- record counting

## Non-goals
No broker/exchange connection, persistence, live streaming, resampling, indicators,
or external data normalization in v1.0.

## Acceptance criteria
1. Valid bars can be stored.
2. Invalid OHLCV data is rejected.
3. Duplicate records are rejected.
4. Retrieval is chronological.
5. Latest-bar lookup returns newest data.
6. Missing data is explicit.
7. Unit tests pass.
