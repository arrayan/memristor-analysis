from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def build_correlation_scatter_fig(scatter_df: "pd.DataFrame", sets: list[str]) -> go.Figure:
    """
    Device-level correlation scatter plots.
    Two dropdowns: pair + set.

    Expects scatter_df columns (from transforms.build_scatter_table):
      source_file, cycle_number, V_set, V_reset, I_HRS, I_LRS, I_reset_max, R_HRS, R_LRS
    """
    fig = go.Figure()

    if scatter_df is None or scatter_df.empty or not sets:
        fig.update_layout(title="Device correlation – no data")
        return fig

    pairs = [
        ("I_HRS", "V_set", "I_HRS (A) vs V_set (V)"),
        ("R_HRS", "V_set", "R_HRS (Ω) vs V_set (V)"),
        ("I_LRS", "V_reset", "I_LRS (A) vs V_reset (V)"),
        ("R_LRS", "V_reset", "R_LRS (Ω) vs V_reset (V)"),
        ("I_reset_max", "V_reset", "I_reset_max (A) vs V_reset (V)"),
        ("V_set", "V_reset", "V_set (V) vs V_reset (V)"),
    ]

    first_pair = pairs[0]
    first_set = sets[0]

    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    # One trace per (pair, set)
    for x_col, y_col, title in pairs:
        for s in sets:
            df_s = scatter_df[scatter_df["source_file"] == s]
            fig.add_trace(
                go.Scatter(
                    x=df_s[x_col] if (not df_s.empty and x_col in df_s.columns) else [],
                    y=df_s[y_col] if (not df_s.empty and y_col in df_s.columns) else [],
                    mode="markers",
                    marker=dict(color=color_map.get(s, None), size=6),
                    name=s,
                    visible=False,
                    meta={"x": x_col, "y": y_col, "set": s, "title": title},
                    hovertemplate=f"{s}<br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>",
                )
            )

    # default visibility
    for tr in fig.data:
        tr.visible = (tr.meta["x"] == first_pair[0]) and (tr.meta["y"] == first_pair[1]) and (tr.meta["set"] == first_set)

    def vis_for(x_col: str, y_col: str, set_val: str) -> list[bool]:
        return [(tr.meta["x"] == x_col) and (tr.meta["y"] == y_col) and (tr.meta["set"] == set_val) for tr in fig.data]

    # Pair dropdown (keep current set)
    pair_buttons = []
    for x_col, y_col, title in pairs:
        pair_buttons.append(
            dict(
                label=title,
                method="update",
                args=[
                    {"visible": vis_for(x_col, y_col, first_set)},
                    {"xaxis.title.text": x_col, "yaxis.title.text": y_col, "title": f"{title} – {first_set}"},
                ],
            )
        )

    # Set dropdown (keep current pair)
    set_buttons = []
    for s in sets:
        x_col, y_col, title = first_pair
        set_buttons.append(
            dict(
                label=s,
                method="update",
                args=[
                    {"visible": vis_for(x_col, y_col, s)},
                    {"title": f"{title} – {s}"},
                ],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(buttons=pair_buttons, direction="down", showactive=True, x=1.02, y=1.15, xanchor="left", yanchor="top"),
            dict(buttons=set_buttons, direction="down", showactive=True, x=1.02, y=1.05, xanchor="left", yanchor="top"),
        ],
        title=f"{first_pair[2]} – {first_set}",
        xaxis_title=first_pair[0],
        yaxis_title=first_pair[1],
        width=900,
        height=600,
    )

    return fig