from datetime import datetime, timedelta, timezone

import pytest

from src.evidence.evidence import Evidence
from src.evidence.store import DuplicateEvidence, EvidenceStore


def make_evidence(
    *,
    seconds=0,
    source="OR-MSE-001",
    type="market_structure",
    value="bullish",
    symbol="XAUUSD",
    timeframe="H1",
):
    return Evidence(
        timestamp=datetime(
            2026, 9, 22, 12, 0,
            tzinfo=timezone.utc,
        ) + timedelta(seconds=seconds),
        source=source,
        type=type,
        value=value,
        symbol=symbol,
        timeframe=timeframe,
    )


def test_store_add_get_count_and_clear():
    store = EvidenceStore()
    evidence = make_evidence()

    store.add(evidence)

    assert store.count() == 1
    assert store.get(evidence.evidence_id) is evidence

    store.clear()

    assert store.count() == 0
    assert store.get(evidence.evidence_id) is None


def test_store_rejects_duplicate_evidence():
    store = EvidenceStore()
    evidence = make_evidence()

    store.add(evidence)

    with pytest.raises(DuplicateEvidence):
        store.add(evidence)

    assert store.count() == 1


def test_store_get_missing_returns_none():
    store = EvidenceStore()

    assert store.get("missing-id") is None


def test_store_query_filters_conjunctively():
    store = EvidenceStore()

    target = make_evidence(
        seconds=10,
        source="OR-MSE-001",
        type="market_structure",
        symbol="XAUUSD",
        timeframe="H1",
    )
    wrong_source = make_evidence(
        seconds=20,
        source="OR-TREND-001",
        type="market_structure",
        symbol="XAUUSD",
        timeframe="H1",
    )
    wrong_symbol = make_evidence(
        seconds=30,
        source="OR-MSE-001",
        type="market_structure",
        symbol="EURUSD",
        timeframe="H1",
    )

    store.add(wrong_symbol)
    store.add(target)
    store.add(wrong_source)

    result = store.query(
        source="OR-MSE-001",
        type="market_structure",
        symbol="XAUUSD",
        timeframe="H1",
    )

    assert result == (target,)


def test_store_query_uses_start_inclusive_end_exclusive():
    store = EvidenceStore()

    at_start = make_evidence(seconds=10)
    inside = make_evidence(seconds=20)
    at_end = make_evidence(seconds=30)

    store.add(at_end)
    store.add(inside)
    store.add(at_start)

    start = datetime(
        2026, 9, 22, 12, 0, 10,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026, 9, 22, 12, 0, 30,
        tzinfo=timezone.utc,
    )

    result = store.query(start=start, end=end)

    assert result == (at_start, inside)


def test_store_query_rejects_invalid_time_range():
    store = EvidenceStore()

    instant = datetime(
        2026, 9, 22, 12, 0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(ValueError):
        store.query(start=instant, end=instant)

    with pytest.raises(ValueError):
        store.query(
            start=instant + timedelta(seconds=1),
            end=instant,
        )


def test_store_query_is_deterministic_and_insertion_order_independent():
    first = make_evidence(seconds=10, value="first")
    second = make_evidence(seconds=20, value="second")
    third = make_evidence(seconds=30, value="third")

    store_a = EvidenceStore()
    store_b = EvidenceStore()

    for evidence in (third, first, second):
        store_a.add(evidence)

    for evidence in (second, third, first):
        store_b.add(evidence)

    assert store_a.query() == (first, second, third)
    assert store_b.query() == (first, second, third)


def test_store_rejects_non_evidence_objects():
    store = EvidenceStore()

    with pytest.raises(TypeError):
        store.add("not-evidence")
