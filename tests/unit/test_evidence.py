from datetime import datetime, timezone

import pytest

from src.evidence.evidence import Evidence


def test_evidence_is_immutable():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
        metadata={"strength": 0.8},
    )

    with pytest.raises((AttributeError, TypeError)):
        evidence.source = "CHANGED"


def test_evidence_metadata_is_recursively_immutable():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
        metadata={
            "strength": 0.8,
            "context": {
                "levels": [2300.0, 2310.0],
            },
        },
    )

    with pytest.raises(TypeError):
        evidence.metadata["strength"] = 0.9

    with pytest.raises(TypeError):
        evidence.metadata["context"]["levels"][0] = 9999.0


def test_evidence_value_is_recursively_immutable():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value={
            "direction": "bullish",
            "levels": [2300.0, 2310.0],
        },
        symbol="XAUUSD",
        timeframe="H1",
        metadata=None,
    )

    with pytest.raises(TypeError):
        evidence.value["direction"] = "bearish"

    with pytest.raises(TypeError):
        evidence.value["levels"][0] = 9999.0


def test_evidence_rejects_non_datetime_timestamp():
    with pytest.raises(TypeError):
        Evidence(
            timestamp="2026-09-22T12:00:00Z",
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
        )


def test_evidence_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0),
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
        )


def test_evidence_normalizes_timestamp_to_utc():
    local_timezone = timezone.utc.__class__(
        __import__("datetime").timedelta(hours=3)
    )

    evidence = Evidence(
        timestamp=datetime(
            2026, 9, 22, 15, 0,
            tzinfo=local_timezone,
        ),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
    )

    assert evidence.timestamp == datetime(
        2026, 9, 22, 12, 0,
        tzinfo=timezone.utc,
    )
    assert evidence.timestamp.tzinfo == timezone.utc


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", ""),
        ("source", "   "),
        ("source", None),
        ("type", ""),
        ("type", "   "),
        ("type", None),
    ],
)
def test_evidence_rejects_invalid_required_text_fields(field, value):
    kwargs = {
        "timestamp": datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        "source": "OR-MSE-001",
        "type": "market_structure",
        "value": "bullish",
    }
    kwargs[field] = value

    with pytest.raises(ValueError):
        Evidence(**kwargs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("symbol", ""),
        ("symbol", "   "),
        ("timeframe", ""),
        ("timeframe", "   "),
    ],
)
def test_evidence_rejects_invalid_optional_text_when_present(field, value):
    kwargs = {
        "timestamp": datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        "source": "OR-MSE-001",
        "type": "market_structure",
        "value": "bullish",
        field: value,
    }

    with pytest.raises(ValueError):
        Evidence(**kwargs)


@pytest.mark.parametrize(
    "field",
    ["source", "type", "symbol", "timeframe"],
)
def test_evidence_rejects_non_string_text_fields(field):
    kwargs = {
        "timestamp": datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        "source": "OR-MSE-001",
        "type": "market_structure",
        "value": "bullish",
        "symbol": "XAUUSD",
        "timeframe": "H1",
    }
    kwargs[field] = 123

    with pytest.raises(ValueError):
        Evidence(**kwargs)


def test_evidence_trims_text_fields_but_preserves_case_and_internal_characters():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="  OR-Mse-001  ",
        type="  Market Structure  ",
        value="bullish",
        symbol="  Xau-Usd  ",
        timeframe="  H1 Custom  ",
    )

    assert evidence.source == "OR-Mse-001"
    assert evidence.type == "Market Structure"
    assert evidence.symbol == "Xau-Usd"
    assert evidence.timeframe == "H1 Custom"


def test_evidence_allows_absent_optional_text_fields():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol=None,
        timeframe=None,
    )

    assert evidence.symbol is None
    assert evidence.timeframe is None


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_evidence_rejects_non_finite_float_value(value):
    with pytest.raises(ValueError):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        {"nested": float("nan")},
        {"nested": [1.0, float("inf")]},
        [1.0, {"deep": float("-inf")}],
    ],
)
def test_evidence_rejects_nested_non_finite_float_value(value):
    with pytest.raises(ValueError):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        False,
        True,
        0,
        -42,
        3.5,
        "bullish",
        {"direction": "bullish", "strength": 0.8},
        [1, "two", False, None],
        {
            "nested": {
                "sequence": [1, 2.5, True, None],
            },
        },
    ],
)
def test_evidence_accepts_supported_value_types(value):
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value=value,
    )

    assert evidence is not None


@pytest.mark.parametrize(
    "value",
    [
        {1, 2, 3},
        b"bytes",
        complex(1, 2),
        object(),
    ],
)
def test_evidence_rejects_unsupported_value_types(value):
    with pytest.raises((TypeError, ValueError)):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value=value,
        )


def test_evidence_rejects_mapping_with_non_string_key():
    with pytest.raises((TypeError, ValueError)):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value={
                "valid": 1,
                2: "invalid-key",
            },
        )


def test_evidence_accepts_none_metadata():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        metadata=None,
    )

    assert evidence.metadata is None


def test_evidence_accepts_valid_nested_metadata():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        metadata={
            "strength": 0.8,
            "confirmed": True,
            "details": {
                "levels": [1, 2.5, None, "major"],
            },
        },
    )

    assert evidence.metadata["strength"] == 0.8
    assert evidence.metadata["confirmed"] is True


@pytest.mark.parametrize(
    "metadata",
    [
        [],
        "metadata",
        42,
        3.5,
        True,
    ],
)
def test_evidence_rejects_non_mapping_metadata(metadata):
    with pytest.raises((TypeError, ValueError)):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
            metadata=metadata,
        )


def test_evidence_rejects_metadata_with_non_string_key():
    with pytest.raises((TypeError, ValueError)):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
            metadata={
                "valid": 1,
                2: "invalid-key",
            },
        )


@pytest.mark.parametrize(
    "metadata",
    [
        {"bad": float("nan")},
        {"bad": float("inf")},
        {"nested": {"bad": float("-inf")}},
        {"nested": [1, {"bad": float("nan")}]},
    ],
)
def test_evidence_rejects_non_finite_float_in_metadata(metadata):
    with pytest.raises(ValueError):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
            metadata=metadata,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        {"bad": {1, 2}},
        {"bad": b"bytes"},
        {"nested": {"bad": complex(1, 2)}},
        {"nested": [object()]},
    ],
)
def test_evidence_rejects_unsupported_metadata_values(metadata):
    with pytest.raises((TypeError, ValueError)):
        Evidence(
            timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            source="OR-MSE-001",
            type="market_structure",
            value="bullish",
            metadata=metadata,
        )


def test_evidence_canonicalization_is_deterministic():
    first = Evidence(
        timestamp=datetime(2026, 9, 22, 15, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value={
            "strength": 0.8,
            "confirmed": True,
            "levels": [100, 101.5, None],
        },
        symbol="XAUUSD",
        timeframe="H1",
        metadata={"note": "first"},
    )

    second = Evidence(
        timestamp=datetime(2026, 9, 22, 15, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value={
            "levels": [100, 101.5, None],
            "confirmed": True,
            "strength": 0.8,
        },
        symbol="XAUUSD",
        timeframe="H1",
        metadata={"note": "different metadata"},
    )

    assert first.canonical_bytes == second.canonical_bytes
    assert first.evidence_id == second.evidence_id


def test_evidence_metadata_does_not_affect_identity():
    first = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
        metadata={"strength": 0.8},
    )

    second = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
        metadata={"strength": 0.2, "other": True},
    )

    assert first.evidence_id == second.evidence_id


def test_evidence_identity_changes_when_identity_field_changes():
    base = {
        "timestamp": datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        "source": "OR-MSE-001",
        "type": "market_structure",
        "value": "bullish",
        "symbol": "XAUUSD",
        "timeframe": "H1",
    }

    original = Evidence(**base)

    variants = [
        Evidence(**{**base, "source": "OR-TREND-001"}),
        Evidence(**{**base, "type": "trend"}),
        Evidence(**{**base, "value": "bearish"}),
        Evidence(**{**base, "symbol": "EURUSD"}),
        Evidence(**{**base, "timeframe": "M15"}),
        Evidence(
            **{
                **base,
                "timestamp": datetime(
                    2026, 9, 22, 12, 0, 1,
                    tzinfo=timezone.utc,
                ),
            }
        ),
    ]

    for variant in variants:
        assert variant.evidence_id != original.evidence_id


def test_evidence_identity_distinguishes_bool_int_and_float():
    common = {
        "timestamp": datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        "source": "OR-MSE-001",
        "type": "test",
    }

    boolean = Evidence(value=True, **common)
    integer = Evidence(value=1, **common)
    floating = Evidence(value=1.0, **common)

    assert len(
        {
            boolean.evidence_id,
            integer.evidence_id,
            floating.evidence_id,
        }
    ) == 3


def test_evidence_canonicalization_handles_utf8_and_optional_nulls():
    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="structură",
        value={"direcție": "creștere"},
        symbol=None,
        timeframe=None,
    )

    canonical = evidence.canonical_bytes

    assert isinstance(canonical, bytes)
    assert canonical.startswith(b"ORION-EVIDENCE-1|")
    assert "structură".encode("utf-8") in canonical
    assert "direcție".encode("utf-8") in canonical
    assert "creștere".encode("utf-8") in canonical


def test_evidence_id_is_sha256_of_canonical_bytes():
    import hashlib

    evidence = Evidence(
        timestamp=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
        source="OR-MSE-001",
        type="market_structure",
        value="bullish",
        symbol="XAUUSD",
        timeframe="H1",
    )

    expected = hashlib.sha256(evidence.canonical_bytes).hexdigest()

    assert evidence.evidence_id == expected
    assert len(evidence.evidence_id) == 64


def test_evidence_golden_canonical_bytes_and_sha256():
    evidence = Evidence(
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

    expected_canonical = (
        b"ORION-EVIDENCE-1|"
        b"timestamp:32:S:27:2026-09-22T12:00:00.000000Z|"
        b"source:15:S:10:OR-MSE-001|"
        b"type:21:S:16:market_structure|"
        b"value:11:S:7:bullish|"
        b"symbol:10:S:6:XAUUSD|"
        b"timeframe:6:S:2:H1|"
    )

    expected_sha256 = (
        "dd8f52d6f7203fdac6bc1fd3eb6a41f8"
        "7cbf016c4a939557ea454ac0803422ac"
    )

    assert evidence.canonical_bytes == expected_canonical
    assert evidence.evidence_id == expected_sha256
