"""Component re-exports. Import the classes users actually instantiate."""

from __future__ import annotations

from slidebox.components.base import Component, ContainerComponent, LeafComponent
from slidebox.components.image import Image
from slidebox.components.kpi import Kpi
from slidebox.components.kpi_grid import KpiGrid
from slidebox.components.layout import Col, Grid, Row, Spacer
from slidebox.components.shape import Shape, ShapeType
from slidebox.components.slide import Slide
from slidebox.components.text import Heading, Subtitle, Text, Title

__all__ = [
    "Col",
    "Component",
    "ContainerComponent",
    "Grid",
    "Heading",
    "Image",
    "Kpi",
    "KpiGrid",
    "LeafComponent",
    "Row",
    "Shape",
    "ShapeType",
    "Slide",
    "Spacer",
    "Subtitle",
    "Text",
    "Title",
]
