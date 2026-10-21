"""Deterministic OHLC liquidity proxies (MOD-008 / OR-LIQ-001)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math

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


class LiquidityError(Exception):
    """Base exception for liquidity analysis."""


class LiquidityConfigurationError(LiquidityError, ValueError):
    """Invalid analyzer configuration."""


class LiquidityInputError(LiquidityError, ValueError):
    """Invalid market bar sequence."""


@dataclass
class _Candidate:
    side: LiquiditySide
    anchor_price: float
    first_touch_at: datetime
    confirmed_at: datetime | None = None
    consumed_at: datetime | None = None


def _utc(timestamp: datetime) -> datetime:
    return timestamp.astimezone(timezone.utc)


def _side_order(side: LiquiditySide) -> int:
    return 0 if side == LiquiditySide.UPPER else 1


class LiquidityAnalyzer:
    def __init__(self, tolerance: float) -> None:
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise LiquidityConfigurationError("tolerance must be a finite nonnegative number")
        try:
            normalized = float(tolerance)
        except (ValueError, OverflowError) as exc:
            raise LiquidityConfigurationError("tolerance cannot be converted to float") from exc
        if not math.isfinite(normalized) or normalized < 0:
            raise LiquidityConfigurationError("tolerance must be finite and nonnegative")
        self._tolerance = normalized

    def analyze(self, bars: Sequence[MarketBar]) -> LiquidityAnalysis:
        if not isinstance(bars, Sequence) or isinstance(bars, (str, bytes, bytearray)):
            raise LiquidityInputError("bars must be a sequence of MarketBar")

        previous_instant: datetime | None = None
        symbol: str | None = None
        timeframe: str | None = None
        for bar in bars:
            if not isinstance(bar, MarketBar):
                raise LiquidityInputError("all bars must be MarketBar instances")
            timestamp = bar.timestamp
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise LiquidityInputError("timestamps must be timezone-aware")
            instant = _utc(timestamp)
            if previous_instant is not None and instant <= previous_instant:
                raise LiquidityInputError("timestamps must strictly increase by UTC instant")
            if symbol is None:
                symbol, timeframe = bar.symbol, bar.timeframe
            elif (bar.symbol, bar.timeframe) != (symbol, timeframe):
                raise LiquidityInputError("mixed symbols or timeframes")
            previous_instant = instant

        if len(bars) < 2:
            return LiquidityAnalysis(LiquidityStatus.INSUFFICIENT_DATA, (), ())

        candidates: dict[LiquiditySide, list[_Candidate]] = {
            LiquiditySide.UPPER: [], LiquiditySide.LOWER: []
        }
        sweeps: list[LiquiditySweep] = []
        has_ambiguity = False

        for bar in bars:
            qualifying: list[_Candidate] = []
            for side in (LiquiditySide.UPPER, LiquiditySide.LOWER):
                for candidate in candidates[side]:
                    if candidate.confirmed_at is None or candidate.consumed_at is not None:
                        continue
                    level = candidate.anchor_price
                    swept = (
                        bar.high > level and bar.close < level
                        if side == LiquiditySide.UPPER
                        else bar.low < level and bar.close > level
                    )
                    if swept:
                        qualifying.append(candidate)

            sides = {candidate.side for candidate in qualifying}
            ambiguous = len(sides) == 2
            has_ambiguity |= ambiguous
            for candidate in qualifying:
                candidate.consumed_at = bar.timestamp
                sweeps.append(LiquiditySweep(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    side=candidate.side,
                    anchor_price=candidate.anchor_price,
                    first_touch_at=candidate.first_touch_at,
                    confirmed_at=candidate.confirmed_at,
                    swept_at=bar.timestamp,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    ambiguous=ambiguous,
                ))

            for side, touch in ((LiquiditySide.UPPER, bar.high), (LiquiditySide.LOWER, bar.low)):
                matches = [
                    candidate for candidate in candidates[side]
                    if candidate.consumed_at is None
                    and abs(touch - candidate.anchor_price) <= self._tolerance
                ]
                if matches:
                    selected = min(matches, key=lambda candidate: (
                        _utc(candidate.first_touch_at),
                        0 if candidate.confirmed_at is None else 1,
                        candidate.anchor_price,
                    ))
                    if selected.confirmed_at is None:
                        selected.confirmed_at = bar.timestamp
                else:
                    candidates[side].append(_Candidate(side, touch, bar.timestamp))

        levels = [
            LiquidityLevel(
                symbol=symbol,
                timeframe=timeframe,
                side=candidate.side,
                anchor_price=candidate.anchor_price,
                first_touch_at=candidate.first_touch_at,
                confirmed_at=candidate.confirmed_at,
                state=(LiquidityLevelState.CONSUMED if candidate.consumed_at is not None
                       else LiquidityLevelState.ACTIVE),
                consumed_at=candidate.consumed_at,
            )
            for side in (LiquiditySide.UPPER, LiquiditySide.LOWER)
            for candidate in candidates[side]
            if candidate.confirmed_at is not None
        ]
        levels.sort(key=lambda level: (
            _utc(level.confirmed_at), _side_order(level.side),
            _utc(level.first_touch_at), level.anchor_price,
        ))
        sweeps.sort(key=lambda sweep: (
            _utc(sweep.swept_at), _side_order(sweep.side),
            _utc(sweep.first_touch_at), sweep.anchor_price,
        ))
        status = (LiquidityStatus.AMBIGUOUS if has_ambiguity else
                  LiquidityStatus.EVENTS if sweeps else LiquidityStatus.NO_EVENT)
        return LiquidityAnalysis(status, tuple(levels), tuple(sweeps))
