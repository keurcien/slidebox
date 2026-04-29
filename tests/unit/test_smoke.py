from __future__ import annotations

import slidebox


def test_version_exposed() -> None:
    assert slidebox.__version__
    assert isinstance(slidebox.__version__, str)


def test_star_import_exposes_core_names() -> None:
    for name in ["Presentation", "Slide", "Row", "Col", "Text", "Kpi", "Updater"]:
        assert hasattr(slidebox, name), f"public API missing {name}"
