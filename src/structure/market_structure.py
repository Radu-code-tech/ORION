"""OR-MSE-001: deterministic market-structure analysis for ORION."""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Sequence


class StructureResult(str, Enum):
    """Allowed market-structure classification results."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class MarketStructureAnalyzer:
    """Deterministic market-structure analyzer based on OHLC progression."""

    def __init__(self, minimum_bars: int = 3) -> None:
        if not isinstance(minimum_bars, int):
            raise TypeError("minimum_bars must be an integer")

        if minimum_bars < 3:
            raise ValueError("minimum_bars must be at least 3")

        self.minimum_bars = minimum_bars

    def analyze(self, bars: Sequence[object]) -> StructureResult:
        """Classify ordered bars as bullish, bearish, range, or insufficient."""

        if bars is None:
            raise TypeError("bars must be a sequence")

        if len(bars) < self.minimum_bars:
            return StructureResult.INSUFFICIENT_DATA

        highs = []
        lows = []

        for bar in bars:
            if not hasattr(bar, "high") or not hasattr(bar, "low"):
                raise TypeError("each bar must provide high and low attributes")

            high = float(bar.high)
            low = float(bar.low)

            if not isfinite(high) or not isfinite(low):
                raise ValueError("high and low must be finite")

            if low > high:
                raise ValueError("low must not exceed high")

            highs.append(high)
            lows.append(low)

        higher_highs = all(
            highs[i] > highs[i - 1]
            for i in range(1, len(highs))
        )

        higher_lows = all(
            lows[i] > lows[i - 1]
            for i in range(1, len(lows))
        )

        lower_highs = all(
            highs[i] < highs[i - 1]
            for i in range(1, len(highs))
        )

        lower_lows = all(
            lows[i] < lows[i - 1]
            for i in range(1, len(lows))
        )

        if higher_highs and higher_lows:
            return StructureResult.BULLISH

        if lower_highs and lower_lows:
            return StructureResult.BEARISH

        return StructureResult.RANGE