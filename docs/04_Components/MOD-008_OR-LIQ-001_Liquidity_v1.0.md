# MOD-008 — OR-LIQ-001 Liquidity Engine v1.0

**Status:** APPROVED — specification frozen; owner-approved
**Branch:** `MOD-008-v1.0-liquidity`
**Baseline:** `460fa5cf22aa4fc2d8a8cb740bc93042aa4e5bcd`
**Layer:** ORION Analysis
**Scope:** Deterministic OHLC-based *liquidity proxies*, not observed order-book liquidity.

## 1. Purpose and boundaries

OR-LIQ-001 detects reproducible candidate equal-high/equal-low price levels and subsequent price sweeps. It consumes existing immutable `MarketBar` objects; it does not collect data, persist data, infer real resting orders, forecast price, generate BUY/SELL/NO TRADE decisions, size positions, alter risk, or execute orders.

Evidence creation and historical retention remain the responsibilities of OR-EVIDENCE-001 and OR-MEM-001. In v1.0, the analyzer **returns structured findings**; orchestration may translate validated findings to `Evidence` without changing Evidence semantics. The analyzer must not own or instantiate an EvidenceStore or MarketMemory.

## 2. Inputs and configuration

Reference interface (exact public names to be finalized in Design):

`LiquidityAnalyzer(tolerance: float, minimum_touches: int = 2).analyze(bars: Sequence[MarketBar]) -> LiquidityAnalysis`

- `tolerance`: finite non-negative numeric price distance, measured in the instrument's raw quote units. Reject `bool`, NaN, infinities and negative values. Zero is valid and requires exact price equality.
- `minimum_touches`: v1.0 fixed to **2**; a configurable value other than 2 is out of scope. The proposed constructor parameter may therefore be omitted in Design to keep the public API minimal.
- All bars must be `MarketBar`, for exactly one `symbol` and one `timeframe`, with strictly increasing timestamps. Reject empty or invalid symbol/timeframe, mixed series, duplicate/out-of-order timestamps, naive timestamps, and non-finite OHLC values; do not silently sort, deduplicate, or coerce invalid input.
- Timestamp comparisons use absolute instants. Timezone-aware timestamps are required by this component even if `MarketBar` currently permits naive datetimes. The analyzer must not mutate the upstream object.
- No minimum volume and no volume-based interpretation.

## 3. Deterministic candidate levels

The following deterministic algorithm is approved as the v1.0 behavioral contract; implementation must be verified with explicit golden cases.

1. Process completed bars strictly in input order; live/incomplete bars are outside v1.0. At each bar, **first** evaluate sweeps against levels confirmed before that bar, **then** consume swept levels, **then** process the current bar's touches. This ordering prohibits same-bar confirmation and sweep.
2. For each side independently (`UPPER` uses `high`; `LOWER` uses `low`), the first unmatched touch creates an unconfirmed anchored candidate. The next compatible touch from a **different bar** confirms it when `abs(touch_price - anchor_price) <= tolerance`. The level price is always the first touch's exact price; no averaging, midpoint, or retroactive movement.
3. Each new touch may be allocated to **at most one active compatible candidate per side**, with priority: earliest anchor timestamp, then earliest confirmation timestamp (unconfirmed candidates rank before confirmed candidates at the same anchor time), then anchor price ascending. Because input timestamps are strictly increasing and each anchor starts at a distinct bar, earliest anchor normally resolves the tie. Touches are processed separately for `UPPER` and `LOWER`; the same bar may touch one candidate of each side.
4. A touch allocated to an already confirmed active candidate does not create a new level or change its confirmation timestamp, anchor, or state. If no active candidate matches, create a new unconfirmed candidate anchored at this bar. An unconfirmed candidate never produces a sweep.
5. Confirmation occurs at the **close of the second distinct matching bar**. The confirmed level becomes sweep-eligible only on the next bar. Each confirmed level is emitted once in the level collection; unconfirmed candidates are not emitted.
6. The first qualifying sweep **consumes** its confirmed level. A consumed level cannot match later touches or emit another sweep; it remains in the immutable audit result with `CONSUMED` state and its sweep timestamp. Later bars may anchor and confirm a fresh level at the same price.
7. v1.0 has no time-based expiry, candidate pruning, cross-level merging, or retained state between analyses. Candidate matching and event creation depend only on the supplied bar sequence and tolerance.

## 4. Sweep detection

For a confirmed upper level at price `L`, a later bar is an upper sweep iff `bar.high > L` and `bar.close < L`. For a confirmed lower level, a later bar is a lower sweep iff `bar.low < L` and `bar.close > L`.

- Equality does **not** satisfy either strict inequality: `high == L`, `low == L`, or `close == L` is not a sweep.
- A sweep bar cannot also be the bar confirming the same candidate.
- A sweep is evaluated only against levels already confirmed at the **start** of that bar's processing.
- If the same bar sweeps both upper and lower candidates, the analyzer must report an explicit **AMBIGUOUS** condition rather than infer intrabar event order from OHLC. No directional trading interpretation is permitted.
- The first qualifying sweep consumes its level immediately. If both sides are swept on the same bar, consume all qualifying levels and preserve all underlying factual sweep events, tagged as ambiguous for that bar. Do not infer which side swept first.

## 5. Outputs and deterministic ordering

The analyzer returns one immutable result with `status`, a separate immutable collection of **confirmed levels** (including consumed levels), and an immutable collection of **sweep events**. Exact public dataclass and enum names are determined in Design, not by changing these semantics.

- Each confirmed level includes `symbol`, `timeframe`, side (`UPPER`/`LOWER`), immutable anchor price, first-touch timestamp, confirmation timestamp, lifecycle state (`ACTIVE` or `CONSUMED`), and optional consumption timestamp. Unconfirmed candidates are internal only.
- Each sweep event includes its associated level's stable deterministic identity (derived from side, first-touch timestamp and anchor price within the analyzed series), sweep timestamp, the observed `high`, `low`, `close`, and an `ambiguous` flag. No inferred intrabar order or trading direction is included.
- `INSUFFICIENT_DATA`: fewer than two valid bars; no confirmed levels or events. Two bars may confirm a level but cannot sweep it in the confirmation bar.
- `NO_EVENT`: at least two valid bars and no sweep; confirmed levels may exist.
- `EVENTS`: at least one sweep and **no** bar with simultaneous upper and lower sweeps.
- `AMBIGUOUS`: at least one bar sweeps levels on **both sides**. Preserve all factual events, marking events on such bars `ambiguous=True`; retain unambiguous events on other bars. This aggregate status takes precedence over `EVENTS`.
- Canonical event order: sweep timestamp (absolute UTC instant), side (`UPPER` before `LOWER`), anchor timestamp (absolute UTC instant), anchor price ascending. Canonical level order: confirmation timestamp (UTC instant), side (`UPPER` before `LOWER`), anchor timestamp (UTC instant), anchor price ascending. No random or insertion-dependent tie-breaks.
- Input timestamps must be timezone-aware and strictly increasing by **UTC instant**. Preserve the original timezone-aware `datetime` values in the output, with no conversion or mutation; ordering and identity comparisons use UTC instants. A timestamp with a different offset but the same instant counts as duplicate.
- Result objects and nested collections are immutable; no wall-clock reads, randomness, hidden caches, network calls, or retained state between calls.

## 6. Failure semantics

- Invalid configuration, invalid bar type, mixed symbols/timeframes, naive/duplicate/out-of-order timestamps, and invalid OHLC input must fail explicitly, not produce `INSUFFICIENT_DATA`.
- Valid but insufficient history returns `INSUFFICIENT_DATA` rather than raising.
- Use a small, explicit exception hierarchy defined in Design; do not duplicate `MarketBar`'s validation logic beyond requirements specific to the analyzer.
- Do not silently repair inputs or assume missing data.

## 7. Integration boundaries

- **MarketData:** source of validated `MarketBar`; analyzer accepts a sequence rather than owning the store.
- **MarketStructure:** remains solely responsible for bullish/bearish/range classification. Liquidity findings are independent of structure classification.
- **Evidence:** optional external adapter/orchestrator may submit deterministic findings to `EvidenceEngine`; Evidence IDs, canonical encoding and validation remain Evidence-owned.
- **Market Memory:** consumes committed Evidence through existing integration; Liquidity Engine does not write to memory directly.
- **Risk/Decision/Execution:** no direct control or side effects.

## 8. Required tests and acceptance

Unit tests must cover: exact-equal and tolerance-boundary touches; just-outside-tolerance; first-touch anchoring; two distinct bars; two-bar confirmation and third-bar eligibility; strict high/low/close inequalities; equal-close rejection; no look-ahead; upper/lower sweeps; simultaneous upper/lower ambiguity; multiple matching candidate levels; duplicate and unordered timestamps; naive and timezone-offset-aware timestamps; mixed symbols/timeframes; invalid numeric input and bool configuration; insufficient data; no-event valid data; immutable output; reproducibility across repeated calls; and no retained analyzer state.

Integration tests must verify that any future orchestration creates valid Evidence through the existing Evidence API, without changing authoritative Evidence storage or Market Memory contracts. Full existing repository regression must remain green.

## 9. Approved decisions and design constraints

1. **Candidate overlap:** each touch is assigned to at most one active matching candidate **per side**, using the deterministic tie-break in §3; no retroactive merge.
2. **Repeated sweeps:** the first sweep consumes the level; a consumed level is retained for audit but cannot emit again. A new level can form later.
3. **Ambiguity:** preserve individual factual upper/lower events on the same bar, mark them ambiguous, and set aggregate status `AMBIGUOUS`.
4. **Output:** expose confirmed levels and sweep events in separate immutable collections; precise public class/enum names belong to Design.
5. **Timestamps:** require aware datetimes; compare and order by UTC instants; retain original datetime representations in findings.
6. **Processing order:** sweep existing confirmed levels, consume them, then process current-bar touches; confirmation takes effect only for subsequent bars.
7. **No inference from OHLC:** a simultaneous two-sided sweep is a factual detection with unknown intrabar sequence, not a directional signal.

## 10. Definition of Done

Specification approved; Design approved; deterministic TDD; focused unit and integration tests; full regression green; clean Git diff; only necessary new source/tests/docs; review against existing module contracts; owner acceptance before merge; no production auto-upgrade or trading side effects.

**Specification review checkpoint:** §9 decisions owner-approved. Full document remains REVIEW until explicit owner approval to freeze and commit.
