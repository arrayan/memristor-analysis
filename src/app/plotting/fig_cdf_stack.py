from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from .fig_cdf import _cdf_xy
from .utils import has_valid_data, find_device_sets, log_axis_config


def build_stack_level_cdf_figs(
    cdf_table: "pd.DataFrame", stack_id: str, devices: list[str]
) -> list[go.Figure]:
    """
    Stack-Level CDFs: one curve per device (aggregated) PLUS a unified
    'All Devices' curve combining the entire stack into one dataset.
    """
    if not has_valid_data(cdf_table, devices):
        return []

    param_map = {
        "VSET": {"pretty": "V_set (V)", "scale": "linear"},
        "V_reset": {"pretty": "V_reset (V)", "scale": "linear"},
        "R_LRS": {"pretty": "R_LRS (Ω)", "scale": "log"},
        "R_HRS": {"pretty": "R_HRS (Ω)", "scale": "log"},
        "I_reset_max": {"pretty": "I_reset_max (A)", "scale": "log"},
        "V_forming": {"pretty": "V_forming (V)", "scale": "linear"},
        "I_leakage_pristine": {"pretty": "I_leakage pristine (A)", "scale": "log"},
    }

    cols = px.colors.sample_colorscale("Viridis", max(len(devices), 2))
    color_map = {d: cols[i] for i, d in enumerate(devices)}

    figures = []

    for param, info in param_map.items():
        if param not in cdf_table.columns:
            continue

        fig = go.Figure()
        is_log = info["scale"] == "log"
        has_any_data = False
        all_x_vals = []

        # One curve per device (aggregated across all its sets)
        for device in devices:
            device_sets = find_device_sets(cdf_table, device, stack_id=stack_id)
            df_device = cdf_table[cdf_table["source_file"].isin(device_sets)]
            x, y = _cdf_xy(df_device[param], is_log=is_log)

            if x.size > 0:
                has_any_data = True
                all_x_vals.extend(x)
                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        mode="lines+markers",
                        name=device,
                        marker=dict(size=4),
                        line=dict(color=color_map.get(device), width=2),
                        opacity=0.8,
                        legendgroup="devices",
                        hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                    )
                )

        # Unified "All Devices" curve — entire stack as one dataset
        x_all, y_all = _cdf_xy(cdf_table[param], is_log=is_log)
        if x_all.size > 0:
            has_any_data = True
            all_x_vals.extend(x_all)
            fig.add_trace(
                go.Scatter(
                    x=x_all,
                    y=y_all,
                    mode="lines",
                    name="All Devices (unified)",
                    line=dict(color="black", width=2.5),
                    legendgroup="unified",
                    hovertemplate="All<br>%{x}<br>%{y:.1f}%<extra></extra>",
                )
            )

        if is_log:
            xaxis_kwargs = dict(
                type="log",
                title_text=f"|{info['pretty']}|",
                exponentformat="power",
                showgrid=True,
                gridcolor="#E5E5E5",
                zeroline=False,
                minor=dict(showgrid=False),
            )
            xaxis_kwargs.update(log_axis_config(all_x_vals))
            fig.update_xaxes(**xaxis_kwargs)
        else:
            fig.update_xaxes(
                type="linear",
                title_text=info["pretty"],
                showgrid=True,
                gridcolor="#E5E5E5",
                zeroline=True,
                zerolinecolor="gray",
                autorange=True,
            )

        fig.update_yaxes(
            title_text="Probability (%)",
            range=[-2, 102],
            showgrid=True,
            gridcolor="#E5E5E5",
        )

        fig.update_layout(
            title=f"Stack {stack_id} – CDF {info['pretty']} ({info['scale'].capitalize()} Scale)",
            width=900,
            height=600,
            template="plotly_white",
            showlegend=True,
            meta={"param_id": param, "level": "stack", "stack_id": stack_id},
        )

        if not has_any_data:
            fig.add_annotation(
                text="No valid data found for this scale type",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(color="red", size=14),
            )

        figures.append(fig)

    return figures
