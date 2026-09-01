from dataclasses import dataclass

import pytest

from src.structure.market_structure import (
    MarketStructureAnalyzer,
    StructureResult,
)


@dataclass(frozen=True)
class Bar:
    high: float
    low: float


def make_bars(highs, lows):
    return [Bar(high, low) for high, low in zip(highs, lows)]


def test_bullish_structure():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [101, 103, 105],
            [99, 100, 102],
        )
    )

    assert result is StructureResult.BULLISH


def test_bearish_structure():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [105, 103, 101],
            [103, 101, 99],
        )
    )

    assert result is StructureResult.BEARISH


def test_range_structure():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [101, 103, 102],
            [99, 98, 100],
        )
    )

    assert result is StructureResult.RANGE


def test_insufficient_data():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [101, 103],
            [99, 100],
        )
    )

    assert result is StructureResult.INSUFFICIENT_DATA


def test_minimum_bars_is_validated():
    with pytest.raises(ValueError):
        MarketStructureAnalyzer(2)


def test_minimum_bars_rejects_non_integer():
    with pytest.raises(TypeError):
        MarketStructureAnalyzer(3.5)


def test_missing_high_attribute_is_rejected():
    @dataclass(frozen=True)
    class InvalidBar:
        low: float

    bars = [
        InvalidBar(99),
        InvalidBar(100),
        InvalidBar(101),
    ]

    with pytest.raises(TypeError):
        MarketStructureAnalyzer().analyze(bars)


def test_missing_low_attribute_is_rejected():
    @dataclass(frozen=True)
    class InvalidBar:
        high: float

    bars = [
        InvalidBar(101),
        InvalidBar(103),
        InvalidBar(105),
    ]

    with pytest.raises(TypeError):
        MarketStructureAnalyzer().analyze(bars)


def test_nan_price_is_rejected():
    bars = make_bars(
        [101, float("nan"), 105],
        [99, 100, 102],
    )

    with pytest.raises(ValueError):
        MarketStructureAnalyzer().analyze(bars)


def test_infinite_price_is_rejected():
    bars = make_bars(
        [101, float("inf"), 105],
        [99, 100, 102],
    )

    with pytest.raises(ValueError):
        MarketStructureAnalyzer().analyze(bars)


def test_invalid_bar_range_is_rejected():
    bars = make_bars(
        [101, 103, 105],
        [99, 104, 102],
    )

    with pytest.raises(ValueError):
        MarketStructureAnalyzer().analyze(bars)


def test_none_bars_is_rejected():
    with pytest.raises(TypeError):
        MarketStructureAnalyzer().analyze(None)


def test_equal_highs_and_lows_produce_range():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [101, 101, 101],
            [99, 99, 99],
        )
    )

    assert result is StructureResult.RANGE


def test_mixed_high_progression_produces_range():
    result = MarketStructureAnalyzer().analyze(
        make_bars(
            [101, 103, 102, 104],
            [99, 100, 101, 102],
        )
    )

    assert result is StructureResult.RANGE