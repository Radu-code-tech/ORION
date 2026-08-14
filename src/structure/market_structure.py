"""Deterministic market-structure analysis for ORION."""
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

class StructureResult(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGE = "RANGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class MarketStructureAnalyzer:
    """Classifies ordered OHLC bars using higher-high/lower-low progression."""

    def __init__(self, minimum_bars: int = 3) -> None:
        if minimum_bars < 3:
            raise ValueError("minimum_bars must be at least 3")
        self.minimum_bars = minimum_bars

    def analyze(self, bars: Sequence[object]) -> StructureResult:
        if len(bars) < self.minimum_bars:
            return StructureResult.INSUFFICIENT_DATA

        highs = [float(b.high) for b in bars]
        lows = [float(b.low) for b in bars]

        higher_highs = all(highs[i] > highs[i - 1] for i in range(1, len(highs)))
        higher_lows = all(lows[i] > lows[i - 1] for i in range(1, len(lows)))
        lower_highs = all(highs[i] < highs[i - 1] for i in range(1, len(highs)))
        lower_lows = all(lows[i] < lows[i - 1] for i in range(1, len(lows)))

        if higher_highs and higher_lows:
            return StructureResult.BULLISH
        if lower_highs and lower_lows:
            return StructureResult.BEARISH
        return StructureResult.RANGE
