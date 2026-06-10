"""Shared fixtures for slidebox tests."""

from __future__ import annotations

import pytest

from slidebox import Deck


@pytest.fixture
def hello_deck() -> Deck:
    db = (
        Deck.new(title="Hello", object_id="hello")
        .slide(bg="white", label="cover", object_id="cover")
        .header("Hello, slidebox.", col=1, row=3, span=(10, 3), object_id="cover_title")
        .subtitle(
            "A grid-based deck library.",
            col=1,
            row=6,
            span=(8, 1),
            object_id="cover_sub",
        )
    )
    return db.build()


@pytest.fixture
def kpi_deck() -> Deck:
    db = (
        Deck.new(title="Q1 KPIs", object_id="q1")
        .slide(bg="beige", label="kpis")
        .header("Q1 results.", size="display", col=1, row=2, span=(10, 2))
        .kpi(
            label="Revenue",
            value="4,2",
            unit="M€",
            delta="+12%",
            delta_dir="up",
            size="lg",
            col=1,
            row=4,
            span=(4, 4),
            object_id="kpi_rev",
        )
        .kpi(
            label="Users",
            value="58",
            unit="K",
            delta="+8%",
            delta_dir="up",
            col=5,
            row=4,
            span=(4, 4),
            object_id="kpi_users",
        )
    )
    return db.build()
