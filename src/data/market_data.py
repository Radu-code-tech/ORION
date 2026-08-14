"""Deterministic in-memory market-data storage for ORION."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must be non-empty")
        if self.low > self.high:
            raise ValueError("low must not exceed high")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC values are inconsistent")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")

class MarketDataStore:
    def __init__(self) -> None:
        self._bars: Dict[Tuple[str, str, datetime], MarketBar] = {}

    def add_bar(self, bar: MarketBar) -> None:
        key = (bar.symbol, bar.timeframe, bar.timestamp)
        if key in self._bars:
            raise ValueError("bar already exists")
        self._bars[key] = bar

    def add_bars(self, bars: Iterable[MarketBar]) -> None:
        for bar in bars:
            self.add_bar(bar)

    def get_bars(self, symbol: str, timeframe: str) -> List[MarketBar]:
        return sorted(
            (b for b in self._bars.values() if b.symbol == symbol and b.timeframe == timeframe),
            key=lambda b: b.timestamp,
        )

    def latest(self, symbol: str, timeframe: str) -> MarketBar:
        bars = self.get_bars(symbol, timeframe)
        if not bars:
            raise KeyError(f"no market data for {symbol}/{timeframe}")
        return bars[-1]

    def count(self, symbol=None, timeframe=None) -> int:
        return sum(1 for b in self._bars.values()
                   if (symbol is None or b.symbol == symbol)
                   and (timeframe is None or b.timeframe == timeframe))
