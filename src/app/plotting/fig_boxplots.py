from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def build_boxplots_fig(box_table: "pd.DataFrame", sets: list[str]) -> go.Figure:
    """
    Boxplots with a dropdown for parameter.

    Expects box_table columns (from transforms.build_box_table / build_cdf_table):
      source_file, cycle_number, VSET, R_LRS, R_HRS, V_reset, I_reset_max, V_forming
    """
    fig = go.Figure()

    if box_table is None or box_table.empty or not sets:
        fig.update_layout(title="Boxplot – no data")
        return fig

    param_map = {
        "VSET": {"pretty": "V_set (V)"},
        "V_reset": {"pretty": "V_reset (V)"},
        "R_LRS": {"pretty": "R_LRS (Ω)"},
        "R_HRS": {"pretty": "R_HRS (Ω)"},
        "I_reset_max": {"pretty": "I_reset_max (A)"},
        "V_forming": {"pretty": "V_forming (V)"},
    }

    first_param = "VSET" if "VSET" in param_map else next(iter(param_map))

    # one color per set
    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    for param in param_map.keys():
        for s in sets:
            df_s = box_table[box_table["source_file"] == s]
            vals = (
                pd.to_numeric(df_s[param], errors="coerce").dropna()
                if param in df_s.columns
                else pd.Series(dtype=float)
            )
            if vals.empty:
                # still create an “empty” trace so visibility logic stays consistent
                fig.add_trace(
                    go.Box(
                        y=[],
                        name=s,
                        marker_color=color_map.get(s, None),
                        visible=(param == first_param),
                        meta={"param": param},
                        showlegend=False,
                    )
                )
                continue

            fig.add_trace(
                go.Box(
                    y=vals,
                    name=s,
                    boxmean=False,
                    marker_color=color_map.get(s, None),
                    line=dict(width=2),
                    visible=(param == first_param),
                    meta={"param": param},
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
                        "title": f"Boxplot – {info['pretty']}",
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
        title=f"Boxplot – {param_map[first_param]['pretty']}",
        xaxis_title="Set / File",
        yaxis_title=param_map[first_param]["pretty"],
        yaxis_type="log" if "R_LRS" in param_map else "linear",
        width=900,
        height=600,
        boxmode="group",
    )

    return fig
