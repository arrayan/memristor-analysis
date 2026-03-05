from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from .utils import has_valid_data, find_device_sets


def _prepare_leakage_data(leakage_df: pd.DataFrame | None) -> pd.DataFrame:
    """
    Prep. leakage data and calc. R_prestine
    """
    if leakage_df is None or leakage_df.empty:
        return pd.DataFrame()

    df = leakage_df.copy()

    # I_leakage from AI
    if "AI" in df.columns:
        df["I_leakage"] = pd.to_numeric(df["AI"], errors="coerce").abs()

    # R_pristine = V / I_leakage
    if "AV" in df.columns and "I_leakage" in df.columns:
        v = pd.to_numeric(df["AV"], errors="coerce")
        i = df["I_leakage"]
        df["R_pristine"] = np.where(
            (v.notna()) & (i.notna()) & (i > 0),
            v / i,
            np.nan
        )

    return df


def build_stack_level_boxplots(
        box_table: pd.DataFrame,
        stack_id: str,
        devices: list[str],
        leakage_df: pd.DataFrame | None = None,
) -> list[go.Figure]:
    """
    Stack-Level Boxplots: every device
    Includes I_leakage and R_pristine if leakage data provided.
    """
    if not has_valid_data(box_table, devices):
        return []

    # param_map
    param_map = {
        "VSET": {"pretty": "V_set (V)", "scale": "linear"},
        "V_reset": {"pretty": "V_reset (V)", "scale": "linear"},
        "R_LRS": {"pretty": "R_LRS (Ω)", "scale": "log"},
        "R_HRS": {"pretty": "R_HRS (Ω)", "scale": "log"},
        "I_reset_max": {"pretty": "I_reset_max (A)", "scale": "log"},
        "V_forming": {"pretty": "V_forming (V)", "scale": "linear"},
    }

    prepared_leakage = _prepare_leakage_data(leakage_df)

    # append to param_map
    if not prepared_leakage.empty:
        if "I_leakage" in prepared_leakage.columns:
            param_map["I_leakage"] = {"pretty": "I_leakage (A)", "scale": "log"}
        if "R_pristine" in prepared_leakage.columns:
            param_map["R_pristine"] = {"pretty": "R_pristine (Ω)", "scale": "log"}

    cols = px.colors.sample_colorscale("Viridis", max(len(devices), 2))
    color_map = {d: cols[i] for i, d in enumerate(devices)}

    tick_vals = [10.0 ** i for i in range(-15, 16)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 16)]

    figures = []

    for param, info in param_map.items():
        if param in ["I_leakage", "R_pristine"]:
            if prepared_leakage.empty:
                continue
            data_source = prepared_leakage
        else:
            data_source = box_table

        if param not in data_source.columns:
            continue

        fig = go.Figure()
        is_log = info["scale"] == "log"
        has_any_data = False
        all_vals_for_param = []

        for device in devices:
            device_sets = find_device_sets(data_source, device)

            # aggregation
            df_device = data_source[data_source["source_file"].isin(device_sets)]
            vals = pd.to_numeric(df_device[param], errors="coerce").dropna()

            if is_log:
                vals = vals.abs()
                vals = vals[vals > 0]

            if not vals.empty:
                has_any_data = True
                all_vals_for_param.extend(vals.tolist())

            fig.add_trace(
                go.Box(
                    y=vals,
                    name=device,
                    marker_color=color_map.get(device),
                    line=dict(width=2),
                    fillcolor=color_map.get(device),
                    opacity=0.7,
                    boxpoints=False,
                    boxmean=False,
                )
            )

        if not has_any_data:
            continue

        if is_log:
            yaxis_config = dict(
                type="log",
                tickmode="array",
                tickvals=tick_vals,
                ticktext=tick_text,
                title_text=f"|{info['pretty']}|",
                exponentformat="power",
                showgrid=True,
                gridcolor="#E5E5E5",
                minor=dict(showgrid=False),
                zeroline=False,
            )

            if all_vals_for_param:
                lmin = np.log10(min(all_vals_for_param))
                lmax = np.log10(max(all_vals_for_param))

                if (lmax - lmin) < 1.0:
                    mid = (lmin + lmax) / 2
                    yaxis_config["range"] = [mid - 0.55, mid + 0.55]
                else:
                    yaxis_config["autorange"] = True

            fig.update_yaxes(**yaxis_config)
        else:
            fig.update_yaxes(
                type="linear",
                title_text=info["pretty"],
                autorange=True,
                showgrid=True,
                gridcolor="#E5E5E5",
                zeroline=True,
                zerolinecolor="gray",
            )

        fig.update_xaxes(title_text="Device", showgrid=True, gridcolor="#E5E5E5")

        fig.update_layout(
            title=f"Stack {stack_id} – {info['pretty']} ({info['scale'].capitalize()} Scale) | Device-Level Aggregation",
            width=900,
            height=600,
            template="plotly_white",
            showlegend=True,
            boxmode="group",
            meta={"param_id": param, "level": "stack", "stack_id": stack_id},
        )

        figures.append(fig)

    return figures