class MarketMemoryError(Exception):
    """Base exception for OR-MEM-001 Market Memory."""


class InvalidMemoryDependency(MarketMemoryError, TypeError):
    """Raised when a MarketMemory dependency is invalid."""


class InvalidMemoryEvidence(MarketMemoryError, TypeError):
    """Raised when input is not a valid Evidence instance."""


class InvalidMemoryIdentity(MarketMemoryError, TypeError, ValueError):
    """Raised when an evidence identity is invalid."""


class InvalidMemoryLimit(MarketMemoryError, TypeError, ValueError):
    """Raised when a historical result limit is invalid."""


class MemoryEvidenceNotFound(MarketMemoryError, LookupError):
    """Raised when required Evidence is absent from Market Memory."""
