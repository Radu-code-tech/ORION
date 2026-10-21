import pytest
import pytest
from datetime import datetime, timedelta, timezone

from src.data.market_data import MarketBar
from src.structure.liquidity import (
    LiquidityAnalyzer,
    LiquidityConfigurationError,
    LiquidityInputError,
    LiquidityLevelState,
    LiquiditySide,
    LiquidityStatus,
)


def bar(index, high, low, close):
    return MarketBar(
        symbol="TEST",
        timeframe="1h",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)
        + timedelta(hours=index),
        open=close,
        high=high,
        low=low,
        close=close,
    )


def test_insufficient_data():
    result = LiquidityAnalyzer(tolerance=0).analyze([])
    assert result.status == LiquidityStatus.INSUFFICIENT_DATA
    assert result.levels == ()
    assert result.sweeps == ()


def test_two_touches_confirm_upper_level():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
    ])

    assert result.status == LiquidityStatus.NO_EVENT
    assert len(result.levels) == 1
    assert result.levels[0].side == LiquiditySide.UPPER
    assert result.levels[0].anchor_price == 100
    assert result.levels[0].state == LiquidityLevelState.ACTIVE
    assert result.sweeps == ()


def test_upper_sweep_consumes_confirmed_level():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 101, 92, 99),
    ])

    assert result.status == LiquidityStatus.EVENTS
    assert len(result.sweeps) == 1
    assert result.sweeps[0].side == LiquiditySide.UPPER
    assert result.sweeps[0].anchor_price == 100
    assert result.levels[0].state == LiquidityLevelState.CONSUMED


def test_lower_sweep_consumes_confirmed_level():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 101, 90, 96),
        bar(2, 102, 89, 95),
    ])

    assert result.status == LiquidityStatus.EVENTS
    assert len(result.sweeps) == 1
    assert result.sweeps[0].side == LiquiditySide.LOWER
    assert result.sweeps[0].anchor_price == 90
    assert result.levels[0].state == LiquidityLevelState.CONSUMED


def test_simultaneous_upper_and_lower_sweeps_are_ambiguous():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 90, 95),
        bar(2, 101, 89, 95),
    ])

    assert result.status == LiquidityStatus.AMBIGUOUS
    assert len(result.sweeps) == 2
    assert all(event.ambiguous for event in result.sweeps)
    assert {event.side for event in result.sweeps} == {
        LiquiditySide.UPPER,
        LiquiditySide.LOWER,
    }


def test_tolerance_allows_second_touch_within_boundary():
    result = LiquidityAnalyzer(tolerance=0.5).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100.5, 91, 96),
    ])

    assert result.status == LiquidityStatus.NO_EVENT
    assert len(result.levels) == 1
    assert result.levels[0].side == LiquiditySide.UPPER
    assert result.levels[0].anchor_price == 100


def test_confirmation_bar_cannot_sweep_its_new_level():
    result = LiquidityAnalyzer(tolerance=0.5).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100.5, 91, 99),
    ])

    assert result.status == LiquidityStatus.NO_EVENT
    assert len(result.levels) == 1
    assert result.sweeps == ()


def test_negative_tolerance_is_rejected():
    import pytest
    from src.structure.liquidity import LiquidityConfigurationError

    with pytest.raises(LiquidityConfigurationError):
        LiquidityAnalyzer(tolerance=-0.1)


def test_nan_tolerance_is_rejected():
    import pytest
    from src.structure.liquidity import LiquidityConfigurationError

    with pytest.raises(LiquidityConfigurationError):
        LiquidityAnalyzer(tolerance=float("nan"))


def test_naive_timestamp_is_rejected():
    import pytest
    from src.structure.liquidity import LiquidityInputError

    invalid = MarketBar(
        symbol="TEST",
        timeframe="1h",
        timestamp=datetime(2026, 1, 1),
        open=95,
        high=100,
        low=90,
        close=95,
    )

    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(tolerance=0).analyze([invalid])


def test_duplicate_timestamps_are_rejected():
    import pytest
    from src.structure.liquidity import LiquidityInputError

    bars = [
        bar(0, 100, 90, 95),
        bar(0, 101, 91, 96),
    ]

    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(tolerance=0).analyze(bars)


def test_repeated_analysis_is_deterministic():
    bars = [
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 101, 92, 99),
    ]

    analyzer = LiquidityAnalyzer(tolerance=0)

    first = analyzer.analyze(bars)
    second = analyzer.analyze(bars)

    assert first == second
    assert first is not second


def test_analysis_outputs_are_immutable():
    import pytest
    from dataclasses import FrozenInstanceError

    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 101, 92, 99),
    ])

    assert isinstance(result.levels, tuple)
    assert isinstance(result.sweeps, tuple)

    with pytest.raises(FrozenInstanceError):
        result.status = LiquidityStatus.NO_EVENT

    with pytest.raises(FrozenInstanceError):
        result.levels[0].anchor_price = 200

    with pytest.raises(FrozenInstanceError):
        result.sweeps[0].ambiguous = True


def test_same_utc_instant_different_offsets_is_rejected():
    import pytest
    from src.structure.liquidity import LiquidityInputError

    first = bar(0, 100, 90, 95)

    second = MarketBar(
        symbol="TEST",
        timeframe="1h",
        timestamp=datetime(
            2026, 1, 1, 2, 0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        open=95,
        high=100,
        low=90,
        close=95,
    )

    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(tolerance=0).analyze([first, second])


def test_distinct_utc_instants_with_offsets_are_accepted():
    first = bar(0, 100, 90, 95)

    second = MarketBar(
        symbol="TEST",
        timeframe="1h",
        timestamp=datetime(
            2026, 1, 1, 3, 0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        open=96,
        high=100,
        low=91,
        close=96,
    )

    result = LiquidityAnalyzer(tolerance=0).analyze([
        first, second,
    ])

    assert result.status == LiquidityStatus.NO_EVENT
    assert len(result.levels) == 1
    assert result.levels[0].confirmed_at == second.timestamp


def test_touch_outside_tolerance_does_not_confirm():
    result = LiquidityAnalyzer(tolerance=0.5).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100.75, 91, 96),
    ])
    assert result.status == LiquidityStatus.NO_EVENT
    assert result.levels == ()


def test_first_touch_remains_anchor():
    result = LiquidityAnalyzer(tolerance=0.5).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100.5, 91, 96),
        bar(2, 100.25, 92, 97),
    ])
    assert len(result.levels) == 1
    assert result.levels[0].anchor_price == 100
    assert result.levels[0].first_touch_at == bar(0, 100, 90, 95).timestamp
    assert result.levels[0].confirmed_at == bar(1, 100.5, 91, 96).timestamp


def test_consumed_level_cannot_sweep_twice():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 101, 92, 99),
        bar(3, 102, 93, 98),
    ])
    assert len(result.sweeps) == 1
    assert result.sweeps[0].swept_at == bar(2, 101, 92, 99).timestamp


def test_prefix_analysis_has_no_lookahead():
    bars = [
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 101, 92, 99),
    ]
    analyzer = LiquidityAnalyzer(tolerance=0)

    prefix = analyzer.analyze(bars[:2])
    complete = analyzer.analyze(bars)

    assert prefix.status == LiquidityStatus.NO_EVENT
    assert prefix.sweeps == ()
    assert complete.status == LiquidityStatus.EVENTS
    assert len(complete.sweeps) == 1


def test_overlapping_candidates_select_earliest_anchor():
    result = LiquidityAnalyzer(tolerance=1).analyze([
        bar(0, 100, 90, 95),
        bar(1, 102, 91, 96),
        bar(2, 101, 92, 97),
    ])

    upper = [
        level for level in result.levels
        if level.side == LiquiditySide.UPPER
    ]

    assert len(upper) == 1
    assert upper[0].anchor_price == 100
    assert upper[0].first_touch_at == bar(0, 100, 90, 95).timestamp
    assert upper[0].confirmed_at == bar(2, 101, 92, 97).timestamp


def test_multiple_upper_sweeps_have_canonical_order():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 91, 96),
        bar(2, 105, 92, 103),
        bar(3, 105, 93, 104),
        bar(4, 106, 94, 99),
    ])

    assert result.status == LiquidityStatus.EVENTS
    assert len(result.sweeps) == 2
    assert [event.side for event in result.sweeps] == [
        LiquiditySide.UPPER,
        LiquiditySide.UPPER,
    ]
    assert [event.anchor_price for event in result.sweeps] == [
        100,
        105,
    ]
    assert all(not event.ambiguous for event in result.sweeps)
    assert all(
        event.swept_at == bar(4, 106, 94, 99).timestamp
        for event in result.sweeps
    )


def test_simultaneous_sweeps_order_upper_before_lower():
    result = LiquidityAnalyzer(tolerance=0).analyze([
        bar(0, 100, 90, 95),
        bar(1, 100, 90, 95),
        bar(2, 101, 89, 95),
    ])

    assert result.status == LiquidityStatus.AMBIGUOUS
    assert [event.side for event in result.sweeps] == [
        LiquiditySide.UPPER,
        LiquiditySide.LOWER,
    ]
    assert all(event.ambiguous for event in result.sweeps)
    assert [level.side for level in result.levels] == [
        LiquiditySide.UPPER,
        LiquiditySide.LOWER,
    ]


def test_mixed_symbols_are_rejected():
    import dataclasses

    first = bar(0, 100, 90, 95)
    second = dataclasses.replace(
        bar(1, 100, 90, 95),
        symbol="DIFFERENT_SYMBOL",
    )

    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(0).analyze([first, second])


def test_out_of_order_timestamps_are_rejected():
    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(0).analyze([
            bar(2, 100, 90, 95),
            bar(1, 100, 90, 95),
        ])


def test_non_marketbar_input_is_rejected():
    with pytest.raises(LiquidityInputError):
        LiquidityAnalyzer(0).analyze([
            bar(0, 100, 90, 95),
            "invalid",
        ])


@pytest.mark.parametrize("tolerance", [True, False, float("inf"), float("-inf")])
def test_invalid_tolerance_types_are_rejected(tolerance):
    with pytest.raises(LiquidityConfigurationError):
        LiquidityAnalyzer(tolerance)
