"""OR-EVIDENCE-001: Evidence lifecycle orchestration."""

from __future__ import annotations

from src.evidence.evidence import Evidence
from src.evidence.store import EvidenceStore
from src.event.event_bus import Event, EventBus


EVIDENCE_CREATED_TOPIC = "evidence.created"


class EvidenceEngine:
    """Coordinate Evidence storage and optional EventBus publication."""

    def __init__(
        self,
        *,
        store: EvidenceStore,
        event_bus: EventBus | None = None,
    ) -> None:
        if not isinstance(store, EvidenceStore):
            raise TypeError("store must be an EvidenceStore instance")

        if event_bus is not None and not isinstance(event_bus, EventBus):
            raise TypeError("event_bus must be an EventBus instance or None")

        self._store = store
        self._event_bus = event_bus

    def submit(self, evidence: Evidence) -> list[Exception]:
        """Store Evidence, then optionally publish it.

        Successful storage is the commit point. Publication failures are
        returned to the caller and never roll back stored Evidence.
        """

        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be an Evidence instance")

        self._store.add(evidence)

        if self._event_bus is None:
            return []

        event = Event(
            topic=EVIDENCE_CREATED_TOPIC,
            payload=evidence,
            event_id=evidence.evidence_id,
        )

        return self._event_bus.publish(event)
