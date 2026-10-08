from src.evidence import EVIDENCE_CREATED_TOPIC, Evidence, EvidenceStore
from src.event import EventBus

from .exceptions import (
    InvalidMemoryDependency,
    InvalidMemoryEvidence,
    InvalidMemoryIdentity,
    InvalidMemoryLimit,
    MemoryEvidenceNotFound,
)


class MarketMemory:
    """Deterministic historical memory of validated Evidence."""

    def __init__(self, *, event_bus: EventBus | None = None):
        if event_bus is not None and not isinstance(event_bus, EventBus):
            raise InvalidMemoryDependency(
                "event_bus must be an EventBus instance or None"
            )

        self._store = EvidenceStore()
        self._event_bus = event_bus
        self._event_handler = None

        if event_bus is not None:
            self._event_handler = self._on_evidence_created
            event_bus.subscribe(
                EVIDENCE_CREATED_TOPIC,
                self._event_handler,
            )

    def remember(self, evidence: Evidence) -> bool:
        if not isinstance(evidence, Evidence):
            raise InvalidMemoryEvidence(
                "evidence must be an Evidence instance"
            )

        if self._store.get(evidence.evidence_id) is not None:
            return False

        self._store.add(evidence)
        return True

    def get(self, evidence_id: str) -> Evidence | None:
        self._validate_evidence_id(evidence_id)
        return self._store.get(evidence_id)

    def require(self, evidence_id: str) -> Evidence:
        self._validate_evidence_id(evidence_id)

        evidence = self._store.get(evidence_id)

        if evidence is None:
            raise MemoryEvidenceNotFound(
                f"Evidence not found in Market Memory: {evidence_id}"
            )

        return evidence

    def contains(self, evidence_id: str) -> bool:
        self._validate_evidence_id(evidence_id)
        return self._store.get(evidence_id) is not None

    def query(
        self,
        *,
        evidence_id: str | None = None,
        source: str | None = None,
        type: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        start=None,
        end=None,
    ) -> tuple[Evidence, ...]:
        if evidence_id is not None:
            self._validate_evidence_id(evidence_id)

        results = self._store.query(
            source=source,
            type=type,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )

        if evidence_id is None:
            return results

        return tuple(
            evidence
            for evidence in results
            if evidence.evidence_id == evidence_id
        )

    def recent(
        self,
        limit: int,
        *,
        evidence_id: str | None = None,
        source: str | None = None,
        type: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        start=None,
        end=None,
    ) -> tuple[Evidence, ...]:
        if limit.__class__ is not int or limit <= 0:
            raise InvalidMemoryLimit(
                "limit must be an integer greater than zero"
            )

        results = self.query(
            evidence_id=evidence_id,
            source=source,
            type=type,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
        )

        return results[-limit:]

    def clear(self) -> None:
        self._store.clear()

    def close(self) -> None:
        if self._event_bus is None or self._event_handler is None:
            return

        self._event_bus.unsubscribe(
            EVIDENCE_CREATED_TOPIC,
            self._event_handler,
        )
        self._event_handler = None

    def count(self) -> int:
        return self._store.count()

    @staticmethod
    def _validate_evidence_id(evidence_id: str) -> None:
        if not isinstance(evidence_id, str):
            raise InvalidMemoryIdentity(
                "evidence_id must be a string"
            )

        if not evidence_id.strip():
            raise InvalidMemoryIdentity(
                "evidence_id must not be empty or whitespace-only"
            )

    def _on_evidence_created(self, event) -> None:
        self.remember(event.payload)
