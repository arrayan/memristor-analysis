from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
# TODO Create plotting/fig_cdf.py

# plotting/fig_boxplots.py

# plotting/fig_endurance.py

# plotting/fig_correlation.py


def build_characteristic_fig(
    raw_by_set: dict[str, "pd.DataFrame"], sets: list[str]
) -> go.Figure:
    """
    AI / NORM_COND vs AV per cycle, with dropdowns:
      - Y: AI (log) or NORM_COND (linear)
      - Set: choose endurance set
    raw_by_set expects columns: cycle_number, AV, AI, NORM_COND
    """
    import pandas as pd  # local import to keep module lightweight

    if not sets:
        return go.Figure()

    fig = go.Figure()

    # color per cycle inside each set
    colors: dict[str, list[str]] = {}
    for s in sets:
        n = raw_by_set[s]["cycle_number"].nunique()
        colors[s] = px.colors.sample_colorscale("Viridis", n)

    y_label_map = {"AI": "AI (A)", "NORM_COND": "NORM_COND (S)"}

    # add traces (hidden by default)
    for y_col in ["AI", "NORM_COND"]:
        for s in sets:
            df = raw_by_set[s]
            cycles = df["cycle_number"].unique()
            for idx, cyc in enumerate(cycles):
                tiny = df[df["cycle_number"] == cyc]
                fig.add_trace(
                    go.Scatter(
                        x=tiny["AV"],
                        y=tiny[y_col].abs() if y_col == "AI" else tiny[y_col],
                        mode="lines",
                        line=dict(color=colors[s][idx], width=1.5),
                        opacity=0.7,
                        name=f"Cycle {cyc}",
                        visible=False,
                        showlegend=False,
                        meta={"set": s, "y": y_col},
                    )
                )

    # default visibility: AI for first set
    for tr in fig.data:
        tr.visible = (tr.meta["y"] == "AI") and (tr.meta["set"] == sets[0])

    def build_vis(y_val: str, set_val: str) -> list[bool]:
        return [
            (tr.meta["y"] == y_val and tr.meta["set"] == set_val) for tr in fig.data
        ]

    # axis templates
    # AI axis (log)
    dticks = 10.0 ** np.arange(-12, -5)
    yaxis_ai = dict(
        type="log",
        tickmode="array",
        tickvals=dticks,
        ticktext=[f"1×10<sup>{int(np.log10(d))}</sup>" for d in dticks],
        title="AI (A)",
    )

    # NORM_COND axis (linear, dynamic range across all sets)
    norm_min = min(raw_by_set[s]["NORM_COND"].min(skipna=True) for s in sets)
    norm_max = max(raw_by_set[s]["NORM_COND"].max(skipna=True) for s in sets)
    norm_min = (
        0
        if (pd.notna(norm_min) and norm_min < 0)
        else (0 if pd.isna(norm_min) else float(norm_min))
    )
    norm_max = 5 if pd.isna(norm_max) else float(np.ceil(norm_max / 5) * 5)

    yaxis_norm = dict(
        type="linear",
        tickmode="linear",
        tick0=0,
        dtick=5,
        range=[norm_min, norm_max],
        title="NORM_COND (S)",
    )

    # dropdown buttons
    y_buttons = []
    for y_col in ["AI", "NORM_COND"]:
        visible = build_vis(y_col, sets[0])
        yax = yaxis_ai if y_col == "AI" else yaxis_norm
        y_buttons.append(
            dict(
                label=y_label_map[y_col],
                method="update",
                args=[
                    {"visible": visible},
                    {"yaxis": yax, "title": f"{sets[0]} – {y_label_map[y_col]}"},
                ],
            )
        )

    set_buttons = []
    for s in sets:
        # determine currently visible y by checking any visible trace
        current_y = next((tr.meta["y"] for tr in fig.data if tr.visible), "AI")
        visible = build_vis(current_y, s)
        yax = yaxis_ai if current_y == "AI" else yaxis_norm
        set_buttons.append(
            dict(
                label=s,
                method="update",
                args=[
                    {"visible": visible},
                    {"yaxis": yax, "title": f"{s} – {y_label_map[current_y]}"},
                ],
            )
        )

    # layout
    fig.update_xaxes(autorange="reversed", title="AV (V)")
    fig.update_yaxes(**yaxis_ai)

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=y_buttons,
                direction="down",
                showactive=True,
                x=1.02,
                xanchor="left",
                y=1.15,
                yanchor="top",
            ),
            dict(
                buttons=set_buttons,
                direction="down",
                showactive=True,
                x=1.02,
                xanchor="left",
                y=1.05,
                yanchor="top",
            ),
        ],
        title=f"{sets[0]} – AI vs AV",
        width=900,
        height=600,
    )

    return fig
