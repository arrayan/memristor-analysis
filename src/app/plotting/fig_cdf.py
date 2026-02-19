from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def _cdf_xy(values: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Return sorted x and cumulative probability in percent."""
    v = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
    if v.size == 0:
        return np.array([]), np.array([])
    x = np.sort(v)
    y = (np.arange(1, x.size + 1) / x.size) * 100.0
    return x, y


def build_cdf_fig(cdf_table: "pd.DataFrame", sets: list[str]) -> go.Figure:
    """
    CDF plots with two dropdowns: parameter + set.

    Expects cdf_table columns (from transforms.build_cdf_table):
      source_file, cycle_number, VSET, R_LRS, R_HRS, V_reset, I_reset_max, V_forming
    """
    fig = go.Figure()

    if cdf_table is None or cdf_table.empty or not sets:
        fig.update_layout(title="CDF – no data")
        return fig

    # Map of internal column -> display / axis scaling
    param_map = {
        "VSET": {"pretty": "V_set (V)", "scale": "linear"},
        "V_reset": {"pretty": "V_reset (V)", "scale": "linear"},
        "R_LRS": {"pretty": "R_LRS (Ω)", "scale": "log"},
        "R_HRS": {"pretty": "R_HRS (Ω)", "scale": "log"},
        "I_reset_max": {"pretty": "I_reset_max (A)", "scale": "log"},
        "V_forming": {"pretty": "V_forming (V)", "scale": "linear"},
    }

    # colors: one color per set (CDF is one line per set)
    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    # Add traces for every (param, set)
    for param in param_map.keys():
        for s in sets:
            df_s = cdf_table[cdf_table["source_file"] == s]
            x, y = _cdf_xy(
                df_s[param] if param in df_s.columns else pd.Series(dtype=float)
            )
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    line=dict(color=color_map.get(s, None), width=2),
                    name=s,
                    visible=False,
                    meta={"param": param, "set": s},
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                )
            )

    first_param = "VSET" if "VSET" in param_map else next(iter(param_map))
    first_set = sets[0]

    # default visibility: first_param + first_set
    for tr in fig.data:
        tr.visible = (tr.meta["param"] == first_param) and (tr.meta["set"] == first_set)

    def vis_for(param_val: str, set_val: str) -> list[bool]:
        return [
            (tr.meta["param"] == param_val) and (tr.meta["set"] == set_val)
            for tr in fig.data
        ]

    # parameter dropdown (preserve currently selected set)
    param_buttons = []
    for param, info in param_map.items():
        visible = vis_for(param, first_set)
        param_buttons.append(
            dict(
                label=info["pretty"],
                method="update",
                args=[
                    {"visible": visible},
                    {
                        "xaxis.title.text": info["pretty"],
                        "yaxis": dict(type="linear", title="Probability (%)"),
                        "title": f"CDF – {info['pretty']} ({first_set})",
                    },
                ],
            )
        )

    # set dropdown (preserve currently selected param)
    set_buttons = []
    for s in sets:
        visible = vis_for(first_param, s)
        info = param_map[first_param]
        set_buttons.append(
            dict(
                label=s,
                method="update",
                args=[
                    {"visible": visible},
                    {"title": f"CDF – {info['pretty']} ({s})"},
                ],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=param_buttons,
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
        title=f"CDF – {param_map[first_param]['pretty']} ({first_set})",
        xaxis_title=param_map[first_param]["pretty"],
        yaxis_title="Probability (%)",
        width=900,
        height=600,
        hovermode="x unified",
    )

    return fig
