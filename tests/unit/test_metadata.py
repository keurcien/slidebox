from __future__ import annotations

from slidebox.compile.metadata import decode_metadata, encode_metadata


def test_round_trip() -> None:
    encoded = encode_metadata("Text", {"source": "bigquery", "row": 42})
    decoded = decode_metadata(encoded)
    assert decoded is not None
    kind, meta = decoded
    assert kind == "Text"
    assert meta == {"source": "bigquery", "row": 42}


def test_no_metadata_produces_marker_only() -> None:
    encoded = encode_metadata("Text", None)
    assert encoded.startswith("slidebox:v1:Text:")
    decoded = decode_metadata(encoded)
    assert decoded == ("Text", {})


def test_decode_rejects_unknown_prefix() -> None:
    assert decode_metadata("something else") is None
    assert decode_metadata(None) is None


def test_oversized_payload_falls_back_to_marker() -> None:
    huge = {"k": "x" * 5000}
    encoded = encode_metadata("Text", huge)
    # Fallback: marker only, payload dropped
    assert encoded == "slidebox:v1:Text:"
