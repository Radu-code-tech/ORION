from datetime import datetime, timezone

import pytest

from src.data.market_data import MarketBar, MarketDataStore


def make_bar(ts, close=101.0):
    return MarketBar(
        "DE30EUR",
        "H1",
        ts,
        100.0,
        max(102.0, close),
        min(99.0, close),
        close,
        10.0,
    )


def test_bars_are_returned_in_timestamp_order():
    store = MarketDataStore()

    t1 = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 14, 11, tzinfo=timezone.utc)

    store.add_bars([
        make_bar(t2, 103),
        make_bar(t1, 101),
    ])

    assert [bar.timestamp for bar in store.get_bars("DE30EUR", "H1")] == [
        t1,
        t2,
    ]


def test_latest_returns_newest_bar():
    store = MarketDataStore()

    t1 = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 14, 11, tzinfo=timezone.utc)

    store.add_bars([
        make_bar(t1),
        make_bar(t2, 103),
    ])

    assert store.latest("DE30EUR", "H1").close == 103


def test_duplicate_bar_is_rejected():
    store = MarketDataStore()

    t = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)

    store.add_bar(make_bar(t))

    with pytest.raises(ValueError):
        store.add_bar(make_bar(t))


def test_invalid_ohlcv_is_rejected():
    with pytest.raises(ValueError):
        MarketBar(
            "DE30EUR",
            "H1",
            datetime.now(timezone.utc),
            100,
            99,
            98,
            100,
        )


def test_missing_latest_data_raises_key_error():
    store = MarketDataStore()

    with pytest.raises(KeyError):
        store.latest("DE30EUR", "H1")


def test_market_bar_rejects_empty_symbol():
    with pytest.raises(ValueError):
        MarketBar(
            "",
            "H1",
            datetime.now(timezone.utc),
            100,
            101,
            99,
            100,
        )


def test_market_bar_rejects_empty_timeframe():
    with pytest.raises(ValueError):
        MarketBar(
            "DE30EUR",
            "",
            datetime.now(timezone.utc),
            100,
            101,
            99,
            100,
        )


def test_market_bar_rejects_non_datetime_timestamp():
    with pytest.raises(TypeError):
        MarketBar(
            "DE30EUR",
            "H1",
            "2026-08-14T10:00:00Z",
            100,
            101,
            99,
            100,
        )


def test_market_bar_rejects_nan_price():
    with pytest.raises(ValueError):
        MarketBar(
            "DE30EUR",
            "H1",
            datetime.now(timezone.utc),
            float("nan"),
            101,
            99,
            100,
        )


def test_market_bar_rejects_infinite_price():
    with pytest.raises(ValueError):
        MarketBar(
            "DE30EUR",
            "H1",
            datetime.now(timezone.utc),
            100,
            float("inf"),
            99,
            100,
        )


def test_market_bar_rejects_negative_volume():
    with pytest.raises(ValueError):
        MarketBar(
            "DE30EUR",
            "H1",
            datetime.now(timezone.utc),
            100,
            101,
            99,
            100,
            -1,
        )


def test_add_bar_rejects_non_market_bar():
    store = MarketDataStore()

    with pytest.raises(TypeError):
        store.add_bar("not-a-market-bar")


def test_query_validation_rejects_invalid_symbol_and_timeframe():
    store = MarketDataStore()

    with pytest.raises(ValueError):
        store.get_bars("", "H1")

    with pytest.raises(ValueError):
        store.get_bars("DE30EUR", "")

    with pytest.raises(ValueError):
        store.count(symbol="")

    with pytest.raises(ValueError):
        store.count(timeframe="")


def test_count_supports_symbol_and_timeframe_filters():
    store = MarketDataStore()

    t1 = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 14, 11, tzinfo=timezone.utc)
    t3 = datetime(2026, 8, 14, 12, tzinfo=timezone.utc)

    store.add_bar(make_bar(t1))
    store.add_bar(make_bar(t2))

    store.add_bar(
        MarketBar(
            "EURUSD",
            "M15",
            t3,
            1.1000,
            1.1010,
            1.0990,
            1.1005,
            50,
        )
    )

    assert store.count() == 3
    assert store.count(symbol="DE30EUR") == 2
    assert store.count(timeframe="H1") == 2
    assert store.count(symbol="EURUSD") == 1
    assert store.count(symbol="DE30EUR", timeframe="H1") == 2


def test_market_bar_is_immutable():
    bar = make_bar(datetime(2026, 8, 14, 10, tzinfo=timezone.utc))

    with pytest.raises(AttributeError):
        bar.close = 200