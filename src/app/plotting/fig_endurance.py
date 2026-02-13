from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def build_endurance_fig(end_df: "pd.DataFrame", sets: list[str]) -> go.Figure:
    """
    Endurance: performance parameter vs cycle number, dropdown for parameter.

    Expects end_df columns (from transforms.build_endurance_table):
      source_file, cycle_number, V_set, V_reset, I_LRS, I_HRS, R_LRS, R_HRS, I_reset_max, Memory_window
    """
    fig = go.Figure()

    if end_df is None or end_df.empty or not sets:
        fig.update_layout(title="Endurance – no data")
        return fig

    param_map = {
        "V_set": {"pretty": "V_set (V)"},
        "V_reset": {"pretty": "V_reset (V)"},
        "I_LRS": {"pretty": "I_LRS (A)"},
        "I_HRS": {"pretty": "I_HRS (A)"},
        "R_LRS": {"pretty": "R_LRS (Ω)"},
        "R_HRS": {"pretty": "R_HRS (Ω)"},
        "I_reset_max": {"pretty": "I_reset_max (A)"},
        "Memory_window": {"pretty": "Memory Window (Ω)"},
    }

    first_param = "V_set" if "V_set" in param_map else next(iter(param_map))

    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    for param in param_map.keys():
        for s in sets:
            df_s = end_df[end_df["source_file"] == s]
            if df_s.empty or param not in df_s.columns:
                fig.add_trace(
                    go.Scatter(
                        x=[],
                        y=[],
                        mode="lines+markers",
                        name=s,
                        visible=(param == first_param),
                        meta={"param": param},
                        line=dict(color=color_map.get(s, None), width=2),
                        marker=dict(size=5),
                        showlegend=True,
                    )
                )
                continue

            fig.add_trace(
                go.Scatter(
                    x=df_s["cycle_number"],
                    y=df_s[param],
                    mode="lines+markers",
                    name=s,
                    visible=(param == first_param),
                    meta={"param": param},
                    line=dict(color=color_map.get(s, None), width=2),
                    marker=dict(size=5),
                    hovertemplate="Cycle %{x}<br>%{y}<extra></extra>",
                )
            )

    def vis_for(param_val: str) -> list[bool]:
        return [tr.meta["param"] == param_val for tr in fig.data]

    buttons = []
    for param, info in param_map.items():
        buttons.append(
            dict(
                label=info["pretty"],
                method="update",
                args=[
                    {"visible": vis_for(param)},
                    {
                        "title": f"Endurance – {info['pretty']}",
                        "yaxis.title.text": info["pretty"],
                    },
                ],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.02,
                xanchor="left",
                y=1.15,
                yanchor="top",
            )
        ],
        title=f"Endurance – {param_map[first_param]['pretty']}",
        xaxis_title="Cycle Number",
        yaxis_title=param_map[first_param]["pretty"],
        width=900,
        height=600,
        hovermode="x unified",
    )

    return fig
