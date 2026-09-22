from datetime import datetime, timezone

import pytest

from src.evidence.engine import EvidenceEngine
from src.evidence.evidence import Evidence
from src.evidence.store import DuplicateEvidence, EvidenceStore
from src.event.event_bus import EventBus


def make_evidence():
    return Evidence(
        timestamp=datetime(
            2026, 9, 22, 12, 0,
            tzinfo=timezone.utc,
        ),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
    )


def test_engine_stores_then_publishes_evidence():
    store = EvidenceStore()
    bus = EventBus()
    engine = EvidenceEngine(store=store, event_bus=bus)

    evidence = make_evidence()
    received = []

    def subscriber(event):
        assert store.get(evidence.evidence_id) is evidence
        received.append(event)

    bus.subscribe("evidence.created", subscriber)

    failures = engine.submit(evidence)

    assert failures == []
    assert store.get(evidence.evidence_id) is evidence
    assert len(received) == 1
    assert received[0].topic == "evidence.created"
    assert received[0].payload is evidence
    assert received[0].event_id == evidence.evidence_id


def test_engine_does_not_publish_duplicate_evidence():
    store = EvidenceStore()
    bus = EventBus()
    engine = EvidenceEngine(store=store, event_bus=bus)

    evidence = make_evidence()
    received = []

    bus.subscribe(
        "evidence.created",
        lambda event: received.append(event),
    )

    engine.submit(evidence)

    with pytest.raises(DuplicateEvidence):
        engine.submit(evidence)

    assert store.count() == 1
    assert len(received) == 1


def test_publication_failure_is_observable_and_evidence_remains_stored():
    store = EvidenceStore()
    bus = EventBus()
    engine = EvidenceEngine(store=store, event_bus=bus)

    evidence = make_evidence()

    def failing_subscriber(event):
        raise RuntimeError("subscriber failure")

    bus.subscribe("evidence.created", failing_subscriber)

    failures = engine.submit(evidence)

    assert len(failures) == 1
    assert isinstance(failures[0], RuntimeError)
    assert str(failures[0]) == "subscriber failure"

    assert store.count() == 1
    assert store.get(evidence.evidence_id) is evidence


def test_engine_can_store_without_event_bus():
    store = EvidenceStore()
    engine = EvidenceEngine(store=store)

    evidence = make_evidence()

    failures = engine.submit(evidence)

    assert failures == []
    assert store.get(evidence.evidence_id) is evidence
