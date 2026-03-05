from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from .fig_cdf import _cdf_xy
from .utils import has_valid_data, find_device_sets


def _prepare_leakage_data(leakage_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prep. leakage data and calc. R_pristine
    """
    if leakage_df is None or leakage_df.empty:
        return pd.DataFrame()

    df = leakage_df.copy()

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


def build_stack_level_cdf_figs(
        cdf_table: "pd.DataFrame",
        stack_id: str,
        devices: list[str],
        leakage_df: "pd.DataFrame | None" = None,
) -> list[go.Figure]:
    """
    Stack-Level CDFs: Every device aggregates all his endurance sets.
    Includes I_leakage and R_pristine if leakage data provided.
    """
    if not has_valid_data(cdf_table, devices):
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

    # append leakage data to param_map
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
            data_source = cdf_table

        if param not in data_source.columns:
            print(f"Debug: Parameter {param} nicht in Datenquelle")
            continue

        fig = go.Figure()
        is_log = info["scale"] == "log"
        has_any_data = False
        all_x_vals = []

        for device in devices:
            device_sets = find_device_sets(data_source, device)

            if not device_sets:
                print(f"Debug: Keine Sets für Device {device}")
                continue

            # aggregate
            df_device = data_source[data_source["source_file"].isin(device_sets)]

            if df_device.empty:
                continue

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
                        hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                    )
                )

        if not has_any_data:
            print(f"Debug: Keine Daten für Parameter {param}")
            continue

        if is_log:
            xaxis_kwargs = dict(
                type="log",
                tickmode="array",
                tickvals=tick_vals,
                ticktext=tick_text,
                title_text=f"|{info['pretty']}|",
                exponentformat="power",
                showgrid=True,
                gridcolor="#E5E5E5",
                zeroline=False,
                minor=dict(showgrid=False),
            )

            if all_x_vals:
                lmin = np.log10(min(all_x_vals))
                lmax = np.log10(max(all_x_vals))

                if (lmax - lmin) < 1.0:
                    mid = (lmin + lmax) / 2
                    xaxis_kwargs["range"] = [mid - 0.55, mid + 0.55]
                else:
                    pad = (lmax - lmin) * 0.05
                    xaxis_kwargs["range"] = [lmin - pad, lmax + pad]

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
            title=f"Stack {stack_id} – CDF {info['pretty']} ({info['scale'].capitalize()} Scale) | Device-Level",
            width=900,
            height=600,
            template="plotly_white",
            showlegend=True,
            meta={"param_id": param, "level": "stack", "stack_id": stack_id},
        )

        figures.append(fig)
        print(f"Debug: Figur für {param} erstellt")

    print(f"Debug: Insgesamt {len(figures)} Figuren erstellt")
    return figures