"""OR-DATA-001: deterministic in-memory market-data storage for ORION."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class MarketBar:
    """Immutable OHLCV market bar."""

    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be a non-empty string")

        if not isinstance(self.timeframe, str) or not self.timeframe.strip():
            raise ValueError("timeframe must be a non-empty string")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime")

        prices = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

        for name, value in prices.items():
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric")

            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")

        if self.low > self.high:
            raise ValueError("low must not exceed high")

        if self.high < max(self.open, self.close):
            raise ValueError("high must be greater than or equal to open and close")

        if self.low > min(self.open, self.close):
            raise ValueError("low must be less than or equal to open and close")

        if self.volume < 0:
            raise ValueError("volume must be non-negative")


class MarketDataStore:
    """Deterministic in-memory market-data store."""

    def __init__(self) -> None:
        self._bars: dict[tuple[str, str, datetime], MarketBar] = {}

    def add_bar(self, bar: MarketBar) -> None:
        """Add one validated market bar.

        Bars are uniquely identified by symbol, timeframe, and timestamp.
        """
        if not isinstance(bar, MarketBar):
            raise TypeError("bar must be a MarketBar instance")

        key = (bar.symbol, bar.timeframe, bar.timestamp)

        if key in self._bars:
            raise ValueError("bar already exists")

        self._bars[key] = bar

    def add_bars(self, bars: Iterable[MarketBar]) -> None:
        """Add multiple market bars in iteration order."""
        for bar in bars:
            self.add_bar(bar)

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
    ) -> list[MarketBar]:
        """Return matching bars in ascending timestamp order."""
        self._validate_symbol(symbol)
        self._validate_timeframe(timeframe)

        return sorted(
            (
                bar
                for bar in self._bars.values()
                if bar.symbol == symbol and bar.timeframe == timeframe
            ),
            key=lambda bar: bar.timestamp,
        )

    def latest(
        self,
        symbol: str,
        timeframe: str,
    ) -> MarketBar:
        """Return the newest bar for a symbol/timeframe."""
        bars = self.get_bars(symbol, timeframe)

        if not bars:
            raise KeyError(f"no market data for {symbol}/{timeframe}")

        return bars[-1]

    def count(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> int:
        """Return the number of stored bars matching optional filters."""
        if symbol is not None:
            self._validate_symbol(symbol)

        if timeframe is not None:
            self._validate_timeframe(timeframe)

        return sum(
            1
            for bar in self._bars.values()
            if (symbol is None or bar.symbol == symbol)
            and (timeframe is None or bar.timeframe == timeframe)
        )

    @staticmethod
    def _validate_symbol(symbol: str) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")

    @staticmethod
    def _validate_timeframe(timeframe: str) -> None:
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe must be a non-empty string")