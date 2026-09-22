"""Typed exceptions for OR-EVIDENCE-001."""


class EvidenceError(Exception):
    """Base exception for Evidence subsystem errors."""


class InvalidEvidence(EvidenceError, TypeError):
    """Raised when an object is not valid Evidence input."""


class InvalidTimestamp(EvidenceError, TypeError, ValueError):
    """Raised when an Evidence timestamp is invalid."""


class InvalidSource(EvidenceError, ValueError):
    """Raised when an Evidence source is invalid."""


class InvalidEvidenceType(EvidenceError, ValueError):
    """Raised when an Evidence type is invalid."""


class InvalidValue(EvidenceError, ValueError):
    """Raised when an Evidence value is invalid."""


class InvalidSymbol(EvidenceError, ValueError):
    """Raised when an Evidence symbol is invalid."""


class InvalidTimeframe(EvidenceError, ValueError):
    """Raised when an Evidence timeframe is invalid."""


class DuplicateEvidence(EvidenceError, ValueError):
    """Raised when an Evidence identity already exists."""


class EvidenceNotFound(EvidenceError, LookupError):
    """Raised by strict operations when Evidence is absent."""
