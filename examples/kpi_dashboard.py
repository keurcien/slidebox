"""KPI dashboard — demonstrates nested layout and theming."""

from __future__ import annotations

import os

from slidebox import Col, Kpi, Presentation, Row, Slide, Title, themes


def main() -> None:
    sa = os.environ.get("SLIDEBOX_SA_JSON")
    with Presentation(
        title="Q1 KPIs",
        theme=themes.dark(),
        service_account_file=sa,
    ) as deck:
        with Slide(id="slide_kpis"):
            with Col(gap="24pt", padding="48pt"):
                Title("Q1 KPIs", id="text_title")
                with Row(gap="16pt"):
                    Kpi("Revenue", "$4.2M", trend="+12%", id="kpi_rev")
                    Kpi("Users", "58K", trend="+8%", id="kpi_users")
                    Kpi("Retention", "94%", trend="+2%", id="kpi_ret")

    pid = deck.push()
    print(f"https://docs.google.com/presentation/d/{pid}")


if __name__ == "__main__":
    main()
