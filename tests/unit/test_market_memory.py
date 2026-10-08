from datetime import datetime, timezone

import pytest

from src.evidence import Evidence
from src.evidence import EVIDENCE_CREATED_TOPIC
from src.event import Event, EventBus
from src.memory import (
    InvalidMemoryDependency,
    InvalidMemoryEvidence,
    InvalidMemoryIdentity,
    InvalidMemoryLimit,
    MarketMemory,
    MarketMemoryError,
    MemoryEvidenceNotFound,
)


def test_memory_exception_hierarchy():
    assert issubclass(InvalidMemoryDependency, MarketMemoryError)
    assert issubclass(InvalidMemoryDependency, TypeError)

    assert issubclass(InvalidMemoryEvidence, MarketMemoryError)
    assert issubclass(InvalidMemoryEvidence, TypeError)

    assert issubclass(InvalidMemoryIdentity, MarketMemoryError)
    assert issubclass(InvalidMemoryIdentity, TypeError)
    assert issubclass(InvalidMemoryIdentity, ValueError)

    assert issubclass(InvalidMemoryLimit, MarketMemoryError)
    assert issubclass(InvalidMemoryLimit, TypeError)
    assert issubclass(InvalidMemoryLimit, ValueError)

    assert issubclass(MemoryEvidenceNotFound, MarketMemoryError)
    assert issubclass(MemoryEvidenceNotFound, LookupError)


def test_market_memory_constructs_without_event_bus():
    memory = MarketMemory()

    assert memory.count() == 0


def test_market_memory_constructs_with_event_bus():
    event_bus = EventBus()

    memory = MarketMemory(event_bus=event_bus)

    assert memory.count() == 0


@pytest.mark.parametrize(
    "invalid_event_bus",
    [
        object(),
        "event-bus",
        123,
        False,
    ],
)
def test_market_memory_rejects_invalid_event_bus_dependency(
    invalid_event_bus,
):
    with pytest.raises(InvalidMemoryDependency):
        MarketMemory(event_bus=invalid_event_bus)


def _make_evidence(*, metadata=None):
    return Evidence(
        timestamp=datetime(
            2026,
            10,
            7,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
        metadata={} if metadata is None else metadata,
    )


def test_remember_accepts_new_evidence():
    memory = MarketMemory()
    evidence = _make_evidence()

    result = memory.remember(evidence)

    assert result is True
    assert memory.count() == 1


def test_remember_identical_replay_is_idempotent():
    memory = MarketMemory()
    evidence = _make_evidence()

    assert memory.remember(evidence) is True
    assert memory.remember(evidence) is False
    assert memory.count() == 1


def test_remember_replay_with_different_metadata_preserves_first_evidence():
    memory = MarketMemory()

    first = _make_evidence(metadata={"origin": "first"})
    replay = _make_evidence(metadata={"origin": "replay"})

    assert first.evidence_id == replay.evidence_id
    assert first is not replay

    assert memory.remember(first) is True
    assert memory.remember(replay) is False
    assert memory.count() == 1

    stored = memory._store.get(first.evidence_id)

    assert stored is first
    assert stored is not replay
    assert stored.metadata == first.metadata


@pytest.mark.parametrize(
    "invalid_evidence",
    [
        None,
        object(),
        "evidence",
        123,
        False,
    ],
)
def test_remember_rejects_non_evidence(invalid_evidence):
    memory = MarketMemory()

    with pytest.raises(InvalidMemoryEvidence):
        memory.remember(invalid_evidence)

    assert memory.count() == 0


def test_get_returns_first_accepted_evidence():
    memory = MarketMemory()

    first = _make_evidence(metadata={"origin": "first"})
    replay = _make_evidence(metadata={"origin": "replay"})

    assert memory.remember(first) is True
    assert memory.remember(replay) is False

    assert memory.get(first.evidence_id) is first


def test_get_returns_none_when_evidence_is_absent():
    memory = MarketMemory()

    assert memory.get("missing-evidence-id") is None


def test_require_returns_existing_evidence():
    memory = MarketMemory()
    evidence = _make_evidence()

    assert memory.remember(evidence) is True

    assert memory.require(evidence.evidence_id) is evidence


def test_require_raises_when_evidence_is_absent():
    memory = MarketMemory()

    with pytest.raises(MemoryEvidenceNotFound):
        memory.require("missing-evidence-id")


def test_contains_reflects_membership():
    memory = MarketMemory()
    evidence = _make_evidence()

    assert memory.contains(evidence.evidence_id) is False

    assert memory.remember(evidence) is True

    assert memory.contains(evidence.evidence_id) is True


@pytest.mark.parametrize(
    "invalid_evidence_id",
    [
        None,
        object(),
        123,
        False,
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ],
)
@pytest.mark.parametrize(
    "method_name",
    [
        "get",
        "require",
        "contains",
    ],
)
def test_identity_apis_reject_invalid_evidence_id(
    method_name,
    invalid_evidence_id,
):
    memory = MarketMemory()
    method = getattr(memory, method_name)

    with pytest.raises(InvalidMemoryIdentity):
        method(invalid_evidence_id)


def test_identity_is_exact_and_not_trimmed():
    memory = MarketMemory()
    evidence = _make_evidence()

    assert memory.remember(evidence) is True

    assert memory.get(evidence.evidence_id) is evidence
    assert memory.get(f" {evidence.evidence_id}") is None
    assert memory.get(f"{evidence.evidence_id} ") is None

    assert memory.contains(f" {evidence.evidence_id}") is False
    assert memory.contains(f"{evidence.evidence_id} ") is False


def _make_query_evidence(
    *,
    minute,
    source="OR-MSE-001",
    type="market_structure",
    value="bullish",
    symbol="XAUUSD",
    timeframe="H1",
):
    return Evidence(
        timestamp=datetime(
            2026,
            10,
            7,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        source=source,
        type=type,
        value=value,
        symbol=symbol,
        timeframe=timeframe,
    )


def test_query_empty_memory_returns_empty_tuple():
    memory = MarketMemory()

    result = memory.query()

    assert result == ()
    assert isinstance(result, tuple)


def test_query_returns_immutable_tuple_in_canonical_order():
    memory = MarketMemory()

    later = _make_query_evidence(minute=20)
    earlier = _make_query_evidence(minute=10)

    memory.remember(later)
    memory.remember(earlier)

    result = memory.query()

    assert isinstance(result, tuple)
    assert result == (earlier, later)


@pytest.mark.parametrize(
    ("filter_name", "matching_value"),
    [
        ("source", "OR-MSE-001"),
        ("type", "market_structure"),
        ("symbol", "XAUUSD"),
        ("timeframe", "H1"),
    ],
)
def test_query_filters_by_evidence_attributes(
    filter_name,
    matching_value,
):
    memory = MarketMemory()

    matching = _make_query_evidence(minute=10)
    other = _make_query_evidence(
        minute=20,
        source="OR-TREND-001",
        type="trend",
        symbol="EURUSD",
        timeframe="M15",
    )

    memory.remember(other)
    memory.remember(matching)

    result = memory.query(**{filter_name: matching_value})

    assert result == (matching,)


def test_query_filters_conjunctively():
    memory = MarketMemory()

    matching = _make_query_evidence(
        minute=10,
        source="OR-MSE-001",
        symbol="XAUUSD",
    )
    wrong_source = _make_query_evidence(
        minute=20,
        source="OR-TREND-001",
        symbol="XAUUSD",
    )
    wrong_symbol = _make_query_evidence(
        minute=30,
        source="OR-MSE-001",
        symbol="EURUSD",
    )

    for evidence in (wrong_symbol, matching, wrong_source):
        memory.remember(evidence)

    result = memory.query(
        source="OR-MSE-001",
        symbol="XAUUSD",
    )

    assert result == (matching,)


def test_query_filters_by_evidence_id():
    memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    memory.remember(first)
    memory.remember(second)

    result = memory.query(evidence_id=second.evidence_id)

    assert result == (second,)


def test_query_evidence_id_absent_returns_empty_tuple():
    memory = MarketMemory()
    memory.remember(_make_query_evidence(minute=10))

    assert memory.query(
        evidence_id="missing-evidence-id"
    ) == ()


def test_query_uses_half_open_timestamp_range():
    memory = MarketMemory()

    before = _make_query_evidence(minute=5)
    at_start = _make_query_evidence(minute=10)
    inside = _make_query_evidence(minute=20)
    at_end = _make_query_evidence(minute=30)

    for evidence in (at_end, before, inside, at_start):
        memory.remember(evidence)

    start = datetime(
        2026,
        10,
        7,
        12,
        10,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        10,
        7,
        12,
        30,
        tzinfo=timezone.utc,
    )

    result = memory.query(start=start, end=end)

    assert result == (at_start, inside)


def test_query_order_is_independent_of_ingestion_order():
    first_memory = MarketMemory()
    second_memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)
    third = _make_query_evidence(minute=30)

    for evidence in (third, first, second):
        first_memory.remember(evidence)

    for evidence in (second, third, first):
        second_memory.remember(evidence)

    assert first_memory.query() == (first, second, third)
    assert second_memory.query() == (first, second, third)
    assert first_memory.query() == second_memory.query()


def test_query_invalid_evidence_id_has_precedence_over_invalid_timestamp():
    memory = MarketMemory()

    invalid_start = datetime(2026, 10, 7, 12, 0)
    invalid_end = datetime(2026, 10, 7, 11, 0)

    with pytest.raises(InvalidMemoryIdentity):
        memory.query(
            evidence_id="   ",
            start=invalid_start,
            end=invalid_end,
        )


def test_recent_returns_final_n_in_canonical_order():
    memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)
    third = _make_query_evidence(minute=30)
    fourth = _make_query_evidence(minute=40)

    for evidence in (third, first, fourth, second):
        memory.remember(evidence)

    result = memory.recent(2)

    assert isinstance(result, tuple)
    assert result == (third, fourth)


def test_recent_limit_larger_than_result_returns_all():
    memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    memory.remember(second)
    memory.remember(first)

    assert memory.recent(10) == (first, second)


def test_recent_applies_filters_before_limit():
    memory = MarketMemory()

    first_match = _make_query_evidence(
        minute=10,
        symbol="XAUUSD",
    )
    other = _make_query_evidence(
        minute=20,
        symbol="EURUSD",
    )
    second_match = _make_query_evidence(
        minute=30,
        symbol="XAUUSD",
    )
    third_match = _make_query_evidence(
        minute=40,
        symbol="XAUUSD",
    )

    for evidence in (
        third_match,
        first_match,
        other,
        second_match,
    ):
        memory.remember(evidence)

    result = memory.recent(
        2,
        symbol="XAUUSD",
    )

    assert result == (second_match, third_match)


def test_recent_supports_evidence_id_filter():
    memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    memory.remember(first)
    memory.remember(second)

    assert memory.recent(
        1,
        evidence_id=first.evidence_id,
    ) == (first,)


def test_recent_returns_empty_tuple_when_no_match():
    memory = MarketMemory()
    memory.remember(_make_query_evidence(minute=10))

    assert memory.recent(
        3,
        symbol="EURUSD",
    ) == ()


@pytest.mark.parametrize(
    "invalid_limit",
    [
        None,
        True,
        False,
        0,
        -1,
        1.0,
        "1",
        object(),
    ],
)
def test_recent_rejects_invalid_limit(invalid_limit):
    memory = MarketMemory()

    with pytest.raises(InvalidMemoryLimit):
        memory.recent(invalid_limit)


@pytest.mark.parametrize(
    "invalid_limit",
    [
        None,
        True,
        0,
        -1,
        1.0,
        "1",
    ],
)
def test_recent_invalid_limit_has_precedence_over_invalid_query_filter(
    invalid_limit,
):
    memory = MarketMemory()

    invalid_start = datetime(2026, 10, 7, 12, 0)
    invalid_end = datetime(2026, 10, 7, 11, 0)

    with pytest.raises(InvalidMemoryLimit):
        memory.recent(
            invalid_limit,
            evidence_id="   ",
            start=invalid_start,
            end=invalid_end,
        )

def test_clear_removes_all_memory_memberships():
    memory = MarketMemory()

    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    memory.remember(first)
    memory.remember(second)

    assert memory.count() == 2

    result = memory.clear()

    assert result is None
    assert memory.count() == 0


def test_clear_removes_evidence_from_retrieval_and_membership():
    memory = MarketMemory()
    evidence = _make_query_evidence(minute=10)

    memory.remember(evidence)

    assert memory.get(evidence.evidence_id) is evidence
    assert memory.contains(evidence.evidence_id) is True

    memory.clear()

    assert memory.get(evidence.evidence_id) is None
    assert memory.contains(evidence.evidence_id) is False


def test_clear_removes_evidence_from_historical_queries():
    memory = MarketMemory()

    first = _make_query_evidence(
        minute=10,
        symbol="XAUUSD",
    )
    second = _make_query_evidence(
        minute=20,
        symbol="XAUUSD",
    )

    memory.remember(first)
    memory.remember(second)

    memory.clear()

    assert memory.query() == ()
    assert memory.query(symbol="XAUUSD") == ()
    assert memory.recent(1) == ()
    assert memory.recent(5, symbol="XAUUSD") == ()


def test_clear_allows_same_evidence_to_be_remembered_again():
    memory = MarketMemory()
    evidence = _make_query_evidence(minute=10)

    assert memory.remember(evidence) is True
    assert memory.remember(evidence) is False

    memory.clear()

    assert memory.count() == 0
    assert memory.remember(evidence) is True
    assert memory.count() == 1
    assert memory.get(evidence.evidence_id) is evidence


def test_clear_is_idempotent_on_empty_memory():
    memory = MarketMemory()

    assert memory.count() == 0

    first_result = memory.clear()
    second_result = memory.clear()

    assert first_result is None
    assert second_result is None
    assert memory.count() == 0
    assert memory.query() == ()

def test_event_bus_subscription_remembers_evidence():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    evidence = _make_query_evidence(minute=10)

    errors = bus.publish(
        Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload=evidence,
            event_id=evidence.evidence_id,
        )
    )

    assert errors == []
    assert memory.count() == 1
    assert memory.get(evidence.evidence_id) is evidence


def test_event_bus_replay_is_idempotent():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    evidence = _make_query_evidence(minute=10)

    event = Event(
        topic=EVIDENCE_CREATED_TOPIC,
        payload=evidence,
        event_id=evidence.evidence_id,
    )

    first_errors = bus.publish(event)
    second_errors = bus.publish(event)

    assert first_errors == []
    assert second_errors == []
    assert memory.count() == 1
    assert memory.get(evidence.evidence_id) is evidence


def test_event_bus_invalid_payload_is_rejected_without_membership():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)

    errors = bus.publish(
        Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload={"not": "evidence"},
            event_id="invalid-payload",
        )
    )

    assert memory.count() == 0
    assert len(errors) == 1
    assert isinstance(errors[0], InvalidMemoryEvidence)


def test_unrelated_event_topic_does_not_change_memory():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    evidence = _make_query_evidence(minute=10)

    errors = bus.publish(
        Event(
            topic="unrelated.topic",
            payload=evidence,
            event_id=evidence.evidence_id,
        )
    )

    assert errors == []
    assert memory.count() == 0

def test_close_unsubscribes_from_evidence_created():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)

    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 1

    result = memory.close()

    assert result is None
    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 0

    evidence = _make_query_evidence(minute=10)

    errors = bus.publish(
        Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload=evidence,
            event_id=evidence.evidence_id,
        )
    )

    assert errors == []
    assert memory.count() == 0


def test_close_is_idempotent():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)

    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 1

    first_result = memory.close()
    second_result = memory.close()

    assert first_result is None
    assert second_result is None
    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 0


def test_close_without_event_bus_is_no_op():
    memory = MarketMemory()

    first_result = memory.close()
    second_result = memory.close()

    assert first_result is None
    assert second_result is None
    assert memory.count() == 0


def test_close_preserves_existing_memory():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    evidence = _make_query_evidence(minute=10)

    assert memory.remember(evidence) is True
    assert memory.count() == 1

    memory.close()

    assert memory.count() == 1
    assert memory.get(evidence.evidence_id) is evidence
    assert memory.contains(evidence.evidence_id) is True
    assert memory.query() == (evidence,)
    assert memory.recent(1) == (evidence,)


def test_direct_api_remains_usable_after_close():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    assert memory.remember(first) is True

    memory.close()

    assert memory.remember(second) is True
    assert memory.remember(second) is False
    assert memory.count() == 2
    assert memory.get(second.evidence_id) is second
    assert memory.require(second.evidence_id) is second
    assert memory.contains(second.evidence_id) is True
    assert memory.query() == (first, second)
    assert memory.recent(1) == (second,)


def test_clear_after_close_remains_usable():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    evidence = _make_query_evidence(minute=10)

    memory.remember(evidence)
    memory.close()

    result = memory.clear()

    assert result is None
    assert memory.count() == 0
    assert memory.get(evidence.evidence_id) is None

    assert memory.remember(evidence) is True
    assert memory.count() == 1

def test_query_evidence_id_is_conjunctive_with_other_filters():
    memory = MarketMemory()
    evidence = _make_query_evidence(
        minute=10,
        symbol="XAUUSD",
    )

    memory.remember(evidence)

    assert memory.query(
        evidence_id=evidence.evidence_id,
        symbol="EURUSD",
    ) == ()

    assert memory.query(
        evidence_id=evidence.evidence_id,
        symbol="XAUUSD",
    ) == (evidence,)


def test_query_invalid_non_string_identity_precedes_invalid_timestamp():
    memory = MarketMemory()

    with pytest.raises(InvalidMemoryIdentity):
        memory.query(
            evidence_id=123,
            start="not-a-timestamp",
            end="also-not-a-timestamp",
        )


def test_recent_rejects_int_subclass():
    class IntSubclass(int):
        pass

    memory = MarketMemory()

    with pytest.raises(InvalidMemoryLimit):
        memory.recent(IntSubclass(1))


def test_clear_does_not_unsubscribe_event_bus():
    bus = EventBus()
    memory = MarketMemory(event_bus=bus)
    first = _make_query_evidence(minute=10)
    second = _make_query_evidence(minute=20)

    memory.remember(first)

    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 1

    memory.clear()

    assert memory.count() == 0
    assert bus.subscriber_count(EVIDENCE_CREATED_TOPIC) == 1

    errors = bus.publish(
        Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload=second,
            event_id=second.evidence_id,
        )
    )

    assert errors == []
    assert memory.count() == 1
    assert memory.get(second.evidence_id) is second

def test_recent_applies_type_filter_before_limit():
    memory = MarketMemory()

    older_match = _make_query_evidence(
        minute=10,
        type="market_structure",
    )
    newer_non_match = _make_query_evidence(
        minute=20,
        type="liquidity",
    )

    memory.remember(older_match)
    memory.remember(newer_non_match)

    assert memory.recent(
        1,
        type="market_structure",
    ) == (older_match,)
