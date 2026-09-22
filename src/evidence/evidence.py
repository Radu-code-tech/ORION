"""OR-EVIDENCE-001: immutable evidence model for ORION."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

from src.evidence.exceptions import (
    InvalidEvidenceType,
    InvalidSource,
    InvalidSymbol,
    InvalidTimeframe,
    InvalidTimestamp,
    InvalidValue,
)


_CANONICAL_PREFIX = b"ORION-EVIDENCE-1|"


def _validate_value(value: Any) -> None:
    """Validate an Evidence value recursively."""

    if value is None:
        return

    if isinstance(value, bool):
        return

    if isinstance(value, int):
        return

    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidValue("value float must be finite")
        return

    if isinstance(value, str):
        return

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidValue("value mapping keys must be strings")
            _validate_value(item)
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_value(item)
        return

    raise InvalidValue(
        f"unsupported evidence value type: {type(value).__name__}"
    )


def _validate_metadata(metadata: Any) -> None:
    """Validate Evidence metadata recursively."""

    if metadata is None:
        return

    if not isinstance(metadata, dict):
        raise InvalidValue("metadata must be a mapping or None")

    _validate_value(metadata)


def _freeze(value: Any) -> Any:
    """Recursively convert containers to immutable equivalents."""

    if isinstance(value, dict):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)

    return value


def _normalize_text(
    name: str,
    value: Any,
    *,
    optional: bool = False,
) -> str | None:
    """Validate and trim an Evidence text field."""

    if optional and value is None:
        return None

    error_types = {
        "source": InvalidSource,
        "type": InvalidEvidenceType,
        "symbol": InvalidSymbol,
        "timeframe": InvalidTimeframe,
    }

    error_type = error_types[name]

    if not isinstance(value, str):
        raise error_type(f"{name} must be a non-empty string")

    normalized = value.strip()

    if not normalized:
        raise error_type(f"{name} must be a non-empty string")

    return normalized


def _encode_string(value: str) -> bytes:
    """Encode a string with its UTF-8 byte length."""

    encoded = value.encode("utf-8")
    return b"S:" + str(len(encoded)).encode("ascii") + b":" + encoded


def _encode_value(value: Any) -> bytes:
    """Encode a supported value into canonical ORION bytes."""

    if value is None:
        return b"N"

    if isinstance(value, bool):
        return b"B1" if value else b"B0"

    if isinstance(value, int):
        return b"I" + str(value).encode("ascii")

    if isinstance(value, float):
        return b"F" + value.hex().encode("ascii")

    if isinstance(value, str):
        return _encode_string(value)

    if isinstance(value, (dict, MappingProxyType)):
        items = sorted(
            value.items(),
            key=lambda item: item[0].encode("utf-8"),
        )

        encoded_items = b"".join(
            _encode_string(key) + _encode_value(item)
            for key, item in items
        )

        return (
            b"M:"
            + str(len(items)).encode("ascii")
            + b":["
            + encoded_items
            + b"]"
        )

    if isinstance(value, (list, tuple)):
        encoded_items = b"".join(
            _encode_value(item)
            for item in value
        )

        return (
            b"Q:"
            + str(len(value)).encode("ascii")
            + b":["
            + encoded_items
            + b"]"
        )

    raise TypeError(
        f"unsupported canonical value type: {type(value).__name__}"
    )


def _encode_field(name: str, value: Any) -> bytes:
    """Frame one identity field using canonical byte length."""

    encoded_value = _encode_value(value)

    return (
        name.encode("ascii")
        + b":"
        + str(len(encoded_value)).encode("ascii")
        + b":"
        + encoded_value
    )


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence record."""

    timestamp: datetime
    source: str
    type: str
    value: Any
    symbol: str | None = None
    timeframe: str | None = None
    metadata: Any = None

    canonical_bytes: bytes = field(init=False, repr=False)
    evidence_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            raise InvalidTimestamp("timestamp must be a datetime")

        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise InvalidTimestamp("timestamp must be timezone-aware")

        object.__setattr__(
            self,
            "timestamp",
            self.timestamp.astimezone(timezone.utc),
        )

        object.__setattr__(
            self,
            "source",
            _normalize_text("source", self.source),
        )
        object.__setattr__(
            self,
            "type",
            _normalize_text("type", self.type),
        )
        object.__setattr__(
            self,
            "symbol",
            _normalize_text("symbol", self.symbol, optional=True),
        )
        object.__setattr__(
            self,
            "timeframe",
            _normalize_text("timeframe", self.timeframe, optional=True),
        )

        _validate_value(self.value)
        _validate_metadata(self.metadata)

        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        canonical = self._build_canonical_bytes()

        object.__setattr__(self, "canonical_bytes", canonical)
        object.__setattr__(
            self,
            "evidence_id",
            hashlib.sha256(canonical).hexdigest(),
        )

    def _build_canonical_bytes(self) -> bytes:
        """Build the complete versioned canonical identity."""

        timestamp_value = self.timestamp.isoformat(
            timespec="microseconds"
        ).replace("+00:00", "Z")

        fields = (
            ("timestamp", timestamp_value),
            ("source", self.source),
            ("type", self.type),
            ("value", self.value),
            ("symbol", self.symbol),
            ("timeframe", self.timeframe),
        )

        return (
            _CANONICAL_PREFIX
            + b"|".join(
                _encode_field(name, value)
                for name, value in fields
            )
            + b"|"
        )
