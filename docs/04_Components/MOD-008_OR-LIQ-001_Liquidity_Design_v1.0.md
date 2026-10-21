# MOD-008 — OR-LIQ-001
# Liquidity Engine — Technical Design v1.0

**Status:** APPROVED — owner-approved; Design frozen
**Branch:** `MOD-008-v1.0-liquidity`
**Specification baseline:** `docs/04_Components/MOD-008_OR-LIQ-001_Liquidity_v1.0.md` (approved; commits `548633f`, `7f7bffb`)
**Starting code baseline:** `460fa5c`
**Scope:** Deterministic OHLC-derived liquidity *proxies*, not real order-book liquidity.

## 1. Objective and boundaries

Implement the approved MOD-008 specification without changing `MarketBar`, `MarketStructureAnalyzer`, Evidence, Market Memory, Risk, Decision or Execution. No signals, predictions, order submission, persistence, networking, wall-clock access, learning, or hidden state. All input bars must represent completed historical bars; this is a caller precondition because `MarketBar` has no completion marker.

## 2. Source and test layout

- `src/structure/liquidity.py`: all MOD-008 enums, immutable value types, exceptions, analyzer and internal candidate bookkeeping.
- `src/structure/__init__.py`: add public exports while preserving `MarketStructureAnalyzer` and `StructureResult`.
- `tests/unit/test_liquidity.py`: deterministic behavior and negative tests.
- `tests/integration/test_liquidity_integration.py`: use real `MarketBar` objects and existing public package imports; any Evidence adapter test is deferred until an adapter is actually in scope.
- No new directories, stores, adapters, services, dependencies or changes to other production modules.

## 3. Public Python contract

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Sequence
from src.data.market_data import MarketBar

class LiquiditySide(str, Enum):
    UPPER = "UPPER"
    LOWER = "LOWER"

class LiquidityLevelState(str, Enum):
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"

class LiquidityStatus(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NO_EVENT = "NO_EVENT"
    EVENTS = "EVENTS"
    AMBIGUOUS = "AMBIGUOUS"

@dataclass(frozen=True)
class LiquidityLevel:
    symbol: str
    timeframe: str
    side: LiquiditySide
    anchor_price: float
    first_touch_at: datetime
    confirmed_at: datetime
    state: LiquidityLevelState
    consumed_at: datetime | None

@dataclass(frozen=True)
class LiquiditySweep:
    symbol: str
    timeframe: str
    side: LiquiditySide
    anchor_price: float
    first_touch_at: datetime
    confirmed_at: datetime
    swept_at: datetime
    high: float
    low: float
    close: float
    ambiguous: bool

@dataclass(frozen=True)
class LiquidityAnalysis:
    status: LiquidityStatus
    levels: tuple[LiquidityLevel, ...]
    sweeps: tuple[LiquiditySweep, ...]

class LiquidityError(Exception): ...
class LiquidityConfigurationError(LiquidityError, ValueError): ...
class LiquidityInputError(LiquidityError, ValueError): ...

class LiquidityAnalyzer:
    def __init__(self, tolerance: float) -> None: ...
    def analyze(self, bars: Sequence[MarketBar]) -> LiquidityAnalysis: ...
```

No public `minimum_touches`: v1.0 fixes confirmation at exactly two distinct matching bars. No public mutable candidate type. The sweep's stable level identity is the tuple `(symbol, timeframe, side, first_touch_at UTC instant, anchor_price)`, represented by its individual fields; no opaque random identifier. Dataclasses are frozen; collections are tuples. No return of mutable internal objects.

## 4. Validation and error semantics

- Constructor accepts a finite, non-negative real numeric `tolerance` (`int` or `float`, excluding `bool`); normalize once to `float`. Reject NaN, infinity, negative values, nonnumeric types, and values not representable as finite float with `LiquidityConfigurationError`.
- `bars` must be a non-`None` `Sequence`, excluding strings/bytes. Each element must be an actual `MarketBar` instance. Reject malformed sequence, wrong element type, mixed symbol/timeframe, naive timestamp, and timestamps not strictly increasing as UTC instants with `LiquidityInputError`. Empty sequence is valid insufficient history.
- `MarketBar` already validates its OHLC shape and numeric finiteness on construction; do not repeat that logic. Because its constructor accepts `bool` as numeric, no extra OHLC boolean rule is introduced in MOD-008. Input bars are not modified or reordered.
- Aware datetimes must have a valid non-`None` UTC offset; convert to UTC only for comparisons and sort keys. Preserve original datetimes in outputs. Equal instants with different offsets are duplicates and fail validation.
- Do not swallow exceptions from malformed custom `Sequence` implementations; ordinary `MarketBar` inputs are the supported contract. Never treat invalid input as `INSUFFICIENT_DATA`.

## 5. Internal candidate state

Maintain a **per-invocation** local list of candidates for each side. Each candidate contains: `side`, `anchor_price`, `first_touch_at`, optional `confirmed_at`, optional `consumed_at`. Internal candidate records may be mutable but never escape `analyze()`.

A candidate is **unconfirmed** until its second compatible touch on a distinct later bar; then **ACTIVE** until swept; then **CONSUMED** permanently. Unconfirmed candidates are not returned. A confirmed candidate's anchor, confirmation timestamp and identity never change. No expiry or pruning. A consumed candidate is excluded from future matching and sweep checks, but included in the returned confirmed-level audit collection.

## 6. Processing algorithm (normative)

For each validated bar in input order:

1. Take a snapshot of all previously confirmed **ACTIVE** candidates on both sides. Evaluate every candidate independently using that bar's `high`, `low`, and `close` (see §7). Collect qualifying sweeps before mutating candidate states.
2. If this bar has qualifying sweeps on both `UPPER` and `LOWER`, mark **all** sweeps on this bar `ambiguous=True`; otherwise `False`. Append one factual event per qualifying level. Set `consumed_at` to the current bar timestamp for each swept candidate.
3. For each side separately, take this bar's `high` (UPPER) or `low` (LOWER). Find **non-consumed** candidates whose `abs(touch - anchor_price) <= tolerance`.
4. If multiple candidates match, select one using ascending `(first_touch_at UTC instant, confirmation-priority, anchor_price)`; unconfirmed precedes confirmed only in the otherwise impossible same-anchor-time tie. The selected candidate receives the touch. If unconfirmed, set `confirmed_at` to this bar's timestamp; if already confirmed, leave it unchanged. Do not create a second candidate for this side from this touch.
5. If none match, create one unconfirmed candidate anchored at the current touch and timestamp. A candidate created or confirmed in this step cannot be swept until a later bar.

**Important:** A bar that consumes a level in step 2 may create a new unconfirmed candidate at the same price in steps 3–5; this does not resurrect the consumed level. One bar can contribute independently to one upper and one lower candidate. The algorithm is deterministic and replays from scratch on every call.

## 7. Sweep predicates and ambiguity

- UPPER at anchor `L`: `bar.high > L and bar.close < L`.
- LOWER at anchor `L`: `bar.low < L and bar.close > L`.
- Strict comparisons: equality at either boundary is not a sweep.
- Every eligible active level meeting its predicate produces exactly one `LiquiditySweep`, even if multiple same-side levels sweep on the same bar. All are consumed.
- Ambiguity is **per bar**, not per event pair: if any upper and any lower sweep qualify on the same bar, all events on that bar have `ambiguous=True`. No intrabar ordering or direction is inferred.
- Overall `LiquidityStatus` is `AMBIGUOUS` if any bar is ambiguous; otherwise `EVENTS` if any sweep exists; otherwise `NO_EVENT` if at least two valid bars; otherwise `INSUFFICIENT_DATA`.

## 8. Output construction and canonical ordering

Return a newly constructed `LiquidityAnalysis` with immutable tuple collections. Include all confirmed levels, including consumed ones, and exclude unconfirmed candidates.

- Level ordering: `(confirmed_at UTC instant, side priority UPPER=0/LOWER=1, first_touch_at UTC instant, anchor_price)`.
- Sweep ordering: `(swept_at UTC instant, side priority UPPER=0/LOWER=1, first_touch_at UTC instant, anchor_price)`.
- Preserve the input timezone-aware datetime objects' values in `first_touch_at`, `confirmed_at`, `consumed_at`, `swept_at`; only ordering and identity comparisons use UTC instants.
- `INSUFFICIENT_DATA` has empty levels and sweeps. For two valid bars, a level can be confirmed but there can be no sweep of that newly confirmed level on the same bar.
- Same input values and same tolerance must produce equal outputs across calls, irrespective of previous calls to the same analyzer instance.

## 9. Golden TDD cases

Tests must build valid `MarketBar` objects with UTC-aware timestamps unless specifically testing another timezone. Avoid relying on volume or external stores.

1. `[]` and `[bar]` -> `INSUFFICIENT_DATA`, empty tuples; invalid one-bar input still fails.
2. Two equal highs -> one confirmed upper level, `NO_EVENT`; third bar `high > L`, `close < L` -> one upper sweep, `EVENTS`, consumed level.
3. Two equal lows -> confirmed lower; third bar `low < L`, `close > L` -> lower sweep.
4. Exact tolerance boundary matches; just-outside boundary does not; zero tolerance matches only exact equality.
5. First touch determines anchor, even when the second touch differs within tolerance; subsequent touches never reprice or reconfirm it.
6. A third bar equal to `L` at high/low or close is not a sweep; strict predicates are enforced.
7. No same-bar confirmation and sweep; no look-ahead on any prefix of a sequence.
8. Multiple matching candidates select earliest anchor; each touch contributes to at most one candidate per side. No retroactive merge.
9. A level sweeps once, is retained as `CONSUMED`, and never emits again; later bars may establish a new candidate at the same price.
10. A bar sweeping both sides creates both factual events with `ambiguous=True`, overall `AMBIGUOUS`; events on other bars remain unambiguous.
11. Multiple same-side active levels swept in one bar emit one event each in canonical order.
12. Naive timestamps, duplicate UTC instants with different offsets, out-of-order bars, mixed symbols/timeframes, wrong bar types and malformed configuration fail explicitly.
13. Equal absolute instants across differing offsets are rejected; distinct aware offsets are ordered correctly without changing the stored datetime representations.
14. Frozen dataclasses, tuple collections, repeated calls, prefix replay and independent analyzer instances are deterministic and state-free.
15. Existing `src.structure` exports remain usable. `MarketBar`, MarketStructure, Evidence and Memory code remain unchanged.

For each numerical case, explicitly choose OHLC-consistent bars and ensure unintended opposite-side candidates do not obscure the assertion. Add regression tests for tolerance floating-point boundaries using values exactly representable in binary (e.g., integer or dyadic fractions) to avoid asserting a false mathematical decimal boundary.

## 10. Complexity and observability

Simple linear candidate scans are preferred for v1.0 clarity. Worst-case time is `O(N^2)` across N bars and accumulated candidates, with `O(N)` local candidate/event storage. Do not introduce indexes, caches or optimization frameworks without profiling evidence and Design amendment. No logging of trading decisions or hidden telemetry; structured returned results provide auditability.

## 11. Integration and backward compatibility

`LiquidityAnalyzer` consumes the existing `MarketBar` type directly and exports its own API via `src.structure`. It does not call `MarketStructureAnalyzer`, `EvidenceEngine`, `MarketMemory`, Risk or Execution. An external future orchestration may convert results to Evidence, but no adapter is created in this module; no Evidence integration test may claim functionality that has not been implemented. Integration tests verify public imports and realistic `MarketBar` sequences without modifying other module contracts.

## 12. Implementation and acceptance gates

1. **Specification:** approved and committed (`548633f`, `7f7bffb`).
2. **Design:** this document reviewed, amended if needed, explicitly owner-approved, then committed.
3. **TDD:** write failing focused tests first; confirm expected red; implement only `src/structure/liquidity.py` and necessary exports.
4. **Testing:** all new unit/integration tests green; run entire existing regression suite and check no regressions.
5. **Validation:** verify determinism, immutability, absence of look-ahead, error semantics, Git diff scope and performance sanity.
6. **Owner acceptance:** present results and obtain explicit approval before merging into `main`.
7. **Merge:** only after acceptance, verify clean worktree and `main` integration.

**Design status: APPROVED. Implementation may proceed under the agreed TDD and validation gates.**
