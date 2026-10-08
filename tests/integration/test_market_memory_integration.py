from datetime import datetime, timezone

from src.evidence import (
    EVIDENCE_CREATED_TOPIC,
    Evidence,
    EvidenceEngine,
    EvidenceStore,
)
from src.event import Event, EventBus
from src.memory import MarketMemory


def _make_evidence(
    *,
    minute: int,
    symbol: str = "XAUUSD",
) -> Evidence:
    return Evidence(
        timestamp=datetime(
            2026,
            9,
            22,
            12,
            minute,
            tzinfo=timezone.utc,
        ),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol=symbol,
        timeframe="H1",
    )


def test_evidence_engine_submission_reaches_market_memory():
    bus = EventBus()
    authoritative_store = EvidenceStore()
    engine = EvidenceEngine(
        store=authoritative_store,
        event_bus=bus,
    )
    memory = MarketMemory(event_bus=bus)
    evidence = _make_evidence(minute=10)

    errors = engine.submit(evidence)

    assert errors == []
    assert authoritative_store.get(evidence.evidence_id) is evidence
    assert memory.get(evidence.evidence_id) is evidence
    assert memory.count() == 1


def test_market_memory_clear_does_not_modify_authoritative_store():
    bus = EventBus()
    authoritative_store = EvidenceStore()
    engine = EvidenceEngine(
        store=authoritative_store,
        event_bus=bus,
    )
    memory = MarketMemory(event_bus=bus)
    evidence = _make_evidence(minute=10)

    assert engine.submit(evidence) == []
    assert authoritative_store.count() == 1
    assert memory.count() == 1

    memory.clear()

    assert memory.count() == 0
    assert memory.get(evidence.evidence_id) is None
    assert authoritative_store.count() == 1
    assert authoritative_store.get(evidence.evidence_id) is evidence


def test_replayed_evidence_created_event_is_idempotent_in_memory():
    bus = EventBus()
    authoritative_store = EvidenceStore()
    engine = EvidenceEngine(
        store=authoritative_store,
        event_bus=bus,
    )
    memory = MarketMemory(event_bus=bus)
    evidence = _make_evidence(minute=10)

    assert engine.submit(evidence) == []

    replay_errors = bus.publish(
        Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload=evidence,
            event_id=evidence.evidence_id,
        )
    )

    assert replay_errors == []
    assert authoritative_store.count() == 1
    assert memory.count() == 1
    assert memory.get(evidence.evidence_id) is evidence


def test_out_of_order_engine_submissions_have_canonical_memory_order():
    bus = EventBus()
    authoritative_store = EvidenceStore()
    engine = EvidenceEngine(
        store=authoritative_store,
        event_bus=bus,
    )
    memory = MarketMemory(event_bus=bus)

    first = _make_evidence(minute=10)
    second = _make_evidence(minute=20)
    third = _make_evidence(minute=30)

    assert engine.submit(third) == []
    assert engine.submit(first) == []
    assert engine.submit(second) == []

    assert memory.query() == (
        first,
        second,
        third,
    )

    assert memory.recent(2) == (
        second,
        third,
    )


def test_subscriber_failure_does_not_rollback_evidence_or_memory():
    bus = EventBus()

    def failing_subscriber(event: Event) -> None:
        raise RuntimeError("intentional integration failure")

    bus.subscribe(
        EVIDENCE_CREATED_TOPIC,
        failing_subscriber,
    )

    authoritative_store = EvidenceStore()
    engine = EvidenceEngine(
        store=authoritative_store,
        event_bus=bus,
    )

    # MarketMemory subscribes after the failing subscriber.
    # EventBus must isolate the first failure and continue delivery.
    memory = MarketMemory(event_bus=bus)
    evidence = _make_evidence(minute=10)

    errors = engine.submit(evidence)

    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert str(errors[0]) == "intentional integration failure"

    assert authoritative_store.get(evidence.evidence_id) is evidence
    assert authoritative_store.count() == 1

    assert memory.get(evidence.evidence_id) is evidence
    assert memory.count() == 1
