from datetime import datetime, timedelta, timezone

from src.data.market_data import MarketBar
from src.structure import (
    MarketStructureAnalyzer,
    StructureResult,
    LiquidityAnalyzer,
    LiquidityAnalysis,
    LiquidityStatus,
)


def test_public_exports_and_shared_market_data():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    bars = [
        MarketBar(
            symbol="TEST",
            timeframe="1h",
            timestamp=start + timedelta(hours=i),
            open=95,
            high=100,
            low=90,
            close=95,
            volume=100,
        )
        for i in range(3)
    ]

    liquidity = LiquidityAnalyzer(tolerance=0).analyze(bars)

    assert isinstance(liquidity, LiquidityAnalysis)
    assert liquidity.status == LiquidityStatus.NO_EVENT
    assert MarketStructureAnalyzer is not None
    assert StructureResult is not None


def test_market_structure_and_liquidity_analyze_same_bars():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    bars = [
        MarketBar(
            symbol="TEST",
            timeframe="1h",
            timestamp=start + timedelta(hours=i),
            open=95,
            high=100,
            low=90,
            close=95,
            volume=100,
        )
        for i in range(4)
    ]

    structure = MarketStructureAnalyzer(minimum_bars=3).analyze(bars)
    liquidity = LiquidityAnalyzer(tolerance=0).analyze(bars)

    assert isinstance(structure, StructureResult)
    assert isinstance(liquidity, LiquidityAnalysis)
    assert liquidity.status == LiquidityStatus.NO_EVENT
