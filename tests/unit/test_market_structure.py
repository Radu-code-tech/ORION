from dataclasses import dataclass
from src.structure.market_structure import MarketStructureAnalyzer, StructureResult

@dataclass(frozen=True)
class Bar:
    high: float
    low: float

def make_bars(highs, lows):
    return [Bar(high, low) for high, low in zip(highs, lows)]

def test_bullish_structure():
    result = MarketStructureAnalyzer().analyze(make_bars([101, 103, 105], [99, 100, 102]))
    assert result is StructureResult.BULLISH

def test_bearish_structure():
    result = MarketStructureAnalyzer().analyze(make_bars([105, 103, 101], [103, 101, 99]))
    assert result is StructureResult.BEARISH

def test_range_structure():
    result = MarketStructureAnalyzer().analyze(make_bars([101, 103, 102], [99, 98, 100]))
    assert result is StructureResult.RANGE

def test_insufficient_data():
    result = MarketStructureAnalyzer().analyze(make_bars([101, 103], [99, 100]))
    assert result is StructureResult.INSUFFICIENT_DATA

def test_minimum_bars_is_validated():
    try:
        MarketStructureAnalyzer(2)
        assert False
    except ValueError:
        pass
