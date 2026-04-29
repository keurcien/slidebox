"""Patch an existing deck without rebuilding it — the Updater pattern.

Assumes you already created a deck with `kpi_dashboard.py`. Set
SLIDEBOX_PRESENTATION_ID to its id and run this script to refresh
each KPI in place.
"""

from __future__ import annotations

import os

from slidebox import Updater


def main() -> None:
    pid = os.environ["SLIDEBOX_PRESENTATION_ID"]
    sa = os.environ.get("SLIDEBOX_SA_JSON")

    (
        Updater(pid, service_account_file=sa)
        .replace_text("kpi_rev_value", "$4.8M")
        .replace_text("kpi_rev_trend", "+14%")
        .replace_text("kpi_users_value", "61K")
        .replace_text("kpi_users_trend", "+11%")
        .replace_text("kpi_ret_value", "95%")
        .replace_text("kpi_ret_trend", "+1%")
        .apply()
    )
    print(f"patched: https://docs.google.com/presentation/d/{pid}")


if __name__ == "__main__":
    main()
