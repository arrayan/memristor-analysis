from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def build_boxplots_fig(box_table: pd.DataFrame, sets: list[str]) -> go.Figure:
    fig = go.Figure()

    if box_table is None or box_table.empty or not sets:
        fig.update_layout(title="Boxplots – no data")
        return fig

    param_map = {
        "VSET": "V_set (V)",
        "V_reset": "V_reset (V)",
        "R_LRS": "R_LRS (Ω)",
        "R_HRS": "R_HRS (Ω)",
        "I_reset_max": "I_reset_max (A)",
        "V_forming": "V_forming (V)",
    }

    param_map = {k: v for k, v in param_map.items() if k in box_table.columns}
    if not param_map:
        fig.update_layout(title="Boxplots – no valid columns")
        return fig

    params = list(param_map.keys())
    first_param = params[0]

    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    for p in params:
        for s in sets:
            df_s = box_table[box_table["source_file"] == s]
            fig.add_trace(
                go.Box(
                    y=df_s[p],
                    name=s,
                    visible=(p == first_param),
                    marker_color=color_map[s],
                    meta={"param": p},
                )
            )

    def vis(p):
        return [tr.meta["param"] == p for tr in fig.data]

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(
                        label=param_map[p],
                        method="update",
                        args=[
                            {"visible": vis(p)},
                            {"title": f"Boxplots – {param_map[p]}", "yaxis.title": param_map[p]},
                        ],
                    )
                    for p in params
                ],
                x=1.02,
                y=1.15,
            )
        ],
        title=f"Boxplots – {param_map[first_param]}",
        xaxis_title="Set",
        yaxis_title=param_map[first_param],
    )

    return fig
