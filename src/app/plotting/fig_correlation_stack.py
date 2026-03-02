from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


def build_stack_level_correlation_figs(
    scatter_df: "pd.DataFrame",
    stack_id: str,
    devices: list[str]
) -> list[go.Figure]:
    """
    Stack-Level: Correlation scatter plots (one per pair).
    Every device aggregates his endurance-sets.
    """
    if scatter_df is None or scatter_df.empty or not devices:
        return []

    pairs = [
        ("V_set", "I_HRS", "V_set (V) vs I_HRS (A)"),
        ("V_set", "R_HRS", "V_set (V) vs R_HRS (Ω)"),
        ("V_reset", "I_LRS", "V_reset (V) vs I_LRS (A)"),
        ("V_reset", "R_LRS", "V_reset (V) vs R_LRS (Ω)"),
        ("V_reset", "I_reset_max", "V_reset (V) vs I_reset_max (A)"),
        ("V_set", "V_reset", "V_set (V) vs V_reset (V)"),
    ]

    def get_scale(col_name):
        return "log" if any(x in col_name for x in ["I_", "R_"]) else "linear"

    base_cols = px.colors.qualitative.Plotly
    device_color_map = {d: base_cols[i % len(base_cols)] for i, d in enumerate(devices)}

    tick_vals = [10.0**i for i in range(-15, 16)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 16)]

    figures = []

    for x_col, y_col, title_text in pairs:
        fig = go.Figure()
        x_scale = get_scale(x_col)
        y_scale = get_scale(y_col)

        all_x, all_y = [], []

        for device in devices:
            # find all sets for device
            device_pattern = f"_{device}_"
            device_sets = [
                s for s in scatter_df["source_file"].unique()
                if device_pattern in s or s.endswith(f"_{device}")
            ]
            if not device_sets:
                device_sets = [s for s in scatter_df["source_file"].unique() if device in s]

            # aggregate
            df_device = scatter_df[scatter_df["source_file"].isin(device_sets)].copy()
            if df_device.empty:
                continue

            # data cleaning
            for col, scale in [(x_col, x_scale), (y_col, y_scale)]:
                df_device[col] = pd.to_numeric(df_device[col], errors="coerce")
                if scale == "log":
                    df_device[col] = df_device[col].abs()
                    df_device.loc[df_device[col] <= 0, col] = np.nan

            df_plot = df_device.dropna(subset=[x_col, y_col])
            if df_plot.empty:
                continue

            all_x.extend(df_plot[x_col].tolist())
            all_y.extend(df_plot[y_col].tolist())

            fig.add_trace(
                go.Scatter(
                    x=df_plot[x_col],
                    y=df_plot[y_col],
                    mode="markers",
                    marker=dict(
                        color=device_color_map[device],
                        size=7,
                        opacity=0.7
                    ),
                    name=device,
                    legendgroup=device,
                    hovertemplate=f"Device: {device}<br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>",
                )
            )

        # axis
        for axis_name, col, scale, all_vals in [
            ("xaxis", x_col, x_scale, all_x),
            ("yaxis", y_col, y_scale, all_y),
        ]:
            axis_config = dict(
                title_text=f"|{col}|" if scale == "log" else col,
                gridcolor="#E5E5E5",
                zeroline=(scale == "linear"),
                zerolinecolor="gray",
            )

            if scale == "log":
                axis_config.update(
                    dict(
                        type="log",
                        tickmode="array",
                        tickvals=tick_vals,
                        ticktext=tick_text,
                        exponentformat="power",
                        minor=dict(showgrid=False),
                    )
                )
                if all_vals:
                    lmin, lmax = np.log10(min(all_vals)), np.log10(max(all_vals))
                    if (lmax - lmin) < 1.0:
                        mid = (lmin + lmax) / 2
                        axis_config["range"] = [mid - 0.55, mid + 0.55]

            fig.update_layout({axis_name: axis_config})

        param_id = f"{x_col}_vs_{y_col}"
        fig.update_layout(
            title=f"Stack {stack_id} – Correlation: {title_text} | Device-Level",
            width=900,
            height=700,
            template="plotly_white",
            legend=dict(title="Devices (Click to toggle)"),
            meta={
                "param_id": param_id,
                "level": "stack",
                "stack_id": stack_id
            },
        )
        figures.append(fig)

    return figures