from datetime import datetime, timezone
from src.data.market_data import MarketBar, MarketDataStore

def make_bar(ts, close=101.0):
    return MarketBar("DE30EUR", "H1", ts, 100.0, max(102.0, close), min(99.0, close), close, 10.0)

def test_bars_are_returned_in_timestamp_order():
    store = MarketDataStore()
    t1 = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 14, 11, tzinfo=timezone.utc)
    store.add_bars([make_bar(t2, 103), make_bar(t1, 101)])
    assert [b.timestamp for b in store.get_bars("DE30EUR", "H1")] == [t1, t2]

def test_latest_returns_newest_bar():
    store = MarketDataStore()
    t1 = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 14, 11, tzinfo=timezone.utc)
    store.add_bars([make_bar(t1), make_bar(t2, 103)])
    assert store.latest("DE30EUR", "H1").close == 103

def test_duplicate_bar_is_rejected():
    store = MarketDataStore()
    t = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)
    store.add_bar(make_bar(t))
    try:
        store.add_bar(make_bar(t)); assert False
    except ValueError: pass

def test_invalid_ohlcv_is_rejected():
    try:
        MarketBar("DE30EUR", "H1", datetime.now(timezone.utc), 100, 99, 98, 100)
        assert False
    except ValueError: pass

def test_missing_latest_data_raises_key_error():
    store = MarketDataStore()
    try:
        store.latest("DE30EUR", "H1"); assert False
    except KeyError: pass
