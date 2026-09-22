"""Deterministic in-memory Evidence store for ORION."""

from __future__ import annotations

from datetime import datetime, timezone

from src.evidence.evidence import Evidence
from src.evidence.exceptions import (
    DuplicateEvidence,
    InvalidEvidence,
    InvalidTimestamp,
)



class EvidenceStore:
    """Deterministic in-memory store for immutable Evidence records."""

    def __init__(self) -> None:
        self._evidence: dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> None:
        """Add Evidence without allowing silent replacement."""

        if not isinstance(evidence, Evidence):
            raise InvalidEvidence("evidence must be an Evidence instance")

        if evidence.evidence_id in self._evidence:
            raise DuplicateEvidence(
                f"duplicate evidence: {evidence.evidence_id}"
            )

        self._evidence[evidence.evidence_id] = evidence

    def get(self, evidence_id: str) -> Evidence | None:
        """Return Evidence by identity, or None when absent."""

        return self._evidence.get(evidence_id)

    def query(
        self,
        *,
        source: str | None = None,
        type: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[Evidence, ...]:
        """Query Evidence using conjunctive filters.

        Time ranges use [start, end): start inclusive, end exclusive.
        Results are deterministically ordered by timestamp and evidence_id.
        """

        normalized_start = self._normalize_boundary("start", start)
        normalized_end = self._normalize_boundary("end", end)

        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_start >= normalized_end
        ):
            raise InvalidTimestamp("start must be earlier than end")

        result = []

        for evidence in self._evidence.values():
            if source is not None and evidence.source != source:
                continue

            if type is not None and evidence.type != type:
                continue

            if symbol is not None and evidence.symbol != symbol:
                continue

            if timeframe is not None and evidence.timeframe != timeframe:
                continue

            if (
                normalized_start is not None
                and evidence.timestamp < normalized_start
            ):
                continue

            if (
                normalized_end is not None
                and evidence.timestamp >= normalized_end
            ):
                continue

            result.append(evidence)

        result.sort(
            key=lambda evidence: (
                evidence.timestamp,
                evidence.evidence_id,
            )
        )

        return tuple(result)

    def count(self) -> int:
        """Return the number of stored Evidence records."""

        return len(self._evidence)

    def clear(self) -> None:
        """Remove all Evidence records."""

        self._evidence.clear()

    @staticmethod
    def _normalize_boundary(
        name: str,
        value: datetime | None,
    ) -> datetime | None:
        """Validate and normalize a query time boundary to UTC."""

        if value is None:
            return None

        if not isinstance(value, datetime):
            raise InvalidTimestamp(f"{name} must be a datetime or None")

        if value.tzinfo is None or value.utcoffset() is None:
            raise InvalidTimestamp(f"{name} must be timezone-aware")

        return value.astimezone(timezone.utc)
