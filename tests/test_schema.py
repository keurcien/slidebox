"""Pydantic schema validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from slidebox import Deck
from slidebox.schema import (
    HeaderCard,
    KpiCard,
    Slide,
)


def test_header_word_cap_rejected() -> None:
    with pytest.raises(ValidationError):
        HeaderCard(
            object_id="x",
            col_start=1,
            col_span=8,
            row_start=1,
            row_span=2,
            text=" ".join(["word"] * 16),
        )


def test_header_word_cap_accepted_at_boundary() -> None:
    HeaderCard(
        object_id="x",
        col_start=1,
        col_span=8,
        row_start=1,
        row_span=2,
        text=" ".join(["w"] * 15),
    )


def test_kpi_value_must_be_string() -> None:
    with pytest.raises(ValidationError):
        KpiCard(
            object_id="x",
            col_start=1,
            col_span=4,
            row_start=1,
            row_span=4,
            value=42,  # type: ignore[arg-type]
        )


def test_overlap_rejected() -> None:
    with pytest.raises(ValidationError):
        Slide(
            object_id="s",
            cards=[
                HeaderCard(
                    object_id="a",
                    col_start=1,
                    col_span=6,
                    row_start=1,
                    row_span=3,
                    text="A",
                ),
                HeaderCard(
                    object_id="b",
                    col_start=4,
                    col_span=4,
                    row_start=2,
                    row_span=3,
                    text="B",
                ),
            ],
        )


def test_out_of_bounds_rejected() -> None:
    with pytest.raises(ValidationError):
        Slide(
            object_id="s",
            cards=[
                HeaderCard(
                    object_id="a",
                    col_start=10,
                    col_span=4,
                    row_start=1,
                    row_span=2,
                    text="A",
                )
            ],
        )


def test_duplicate_object_ids_rejected() -> None:
    db = (
        Deck.new(title="dup", object_id="dup")
        .slide(object_id="s")
        .header("A", col=1, row=1, span=(4, 2), object_id="x")
        .header("B", col=5, row=1, span=(4, 2), object_id="x")
    )
    with pytest.raises(ValidationError):
        db.build()


def test_find_returns_card(kpi_deck: Deck) -> None:
    card = kpi_deck.find("kpi_rev")
    assert card.object_id == "kpi_rev"  # type: ignore[union-attr]


def test_to_json_canonical_is_idempotent(hello_deck: Deck) -> None:
    a = hello_deck.to_json(canonical=True)
    b = hello_deck.to_json(canonical=True)
    assert a == b
    # Sanity: at least one slide-level "background" precedes the slide's "object_id"
    bg = a.index('"background"')
    next_oid = a.index('"object_id"', bg)
    assert bg < next_oid
