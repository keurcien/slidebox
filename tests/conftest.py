"""Shared fixtures for slidebox tests."""

from __future__ import annotations

import pytest

from slidebox import Col, Kpi, Presentation, Row, Slide, Text, Title


@pytest.fixture
def hello_deck() -> Presentation:
    with Presentation(title="Hello") as deck, Slide(id="slide_hello"):
        Title("Hello world", id="text_title")
        Text("A tiny deck", id="text_body")
    return deck


@pytest.fixture
def kpi_deck() -> Presentation:
    with Presentation(title="KPIs") as deck, Slide(id="slide_kpis"), Col(gap=24, padding=48):
        Title("Q1 KPIs", id="text_q1")
        with Row(gap=16):
            Kpi("Revenue", "$4.2M", trend="+12%", id="k_rev")
            Kpi("Users", "58K", trend="+8%", id="k_users")
            Kpi("Retention", "94%", trend="+2%", id="k_ret")
    return deck
