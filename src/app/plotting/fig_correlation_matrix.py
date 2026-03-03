from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def _prepare_data(df: pd.DataFrame, params: list[str]) -> pd.DataFrame:
    """Helper: Bereinigt Daten für Correlation Matrix."""
    log_params = ["I_LRS", "I_HRS", "R_LRS", "R_HRS", "I_reset_max"]

    df_numeric = df[params].apply(pd.to_numeric, errors="coerce")

    for p in params:
        if p in log_params:
            df_numeric[p] = df_numeric[p].abs()
            df_numeric.loc[df_numeric[p] <= 0, p] = np.nan

    return df_numeric


def _create_heatmap(
    corr_matrix: pd.DataFrame, param_labels: dict, params: list[str]
) -> go.Heatmap:
    """Helper: Erstellt Heatmap Trace."""
    labels = [param_labels.get(p, p) for p in params]

    return go.Heatmap(
        z=corr_matrix.values,
        x=labels,
        y=labels,
        zmin=-1,
        zmax=1,
        colorscale="RdBu_r",
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text:.2f}",
        textfont={"size": 10},
        hovertemplate="%{x} vs %{y}<br>Corr: %{z:.3f}<extra></extra>",
    )


def build_correlation_matrix_figs(
    scatter_df: "pd.DataFrame", sets: list[str], devices: list[str] | None = None
) -> list[go.Figure]:
    """
    Device-Level: Correlation matrix heatmaps.
    - One matrix per device
    - One matrix per set
    """
    if scatter_df is None or scatter_df.empty or not sets:
        return []

    params = ["V_set", "V_reset", "I_LRS", "I_HRS", "R_LRS", "R_HRS", "I_reset_max"]
    param_labels = {
        "V_set": "V_set",
        "V_reset": "V_reset",
        "I_LRS": "I_LRS",
        "I_HRS": "I_HRS",
        "R_LRS": "R_LRS",
        "R_HRS": "R_HRS",
        "I_reset_max": "I_reset_max",
    }

    available_params = [p for p in params if p in scatter_df.columns]
    if len(available_params) < 2:
        return []

    figures = []

    for s in sets:
        df_s = scatter_df[scatter_df["source_file"] == s].copy()
        if df_s.empty:
            continue

        df_numeric = _prepare_data(df_s, available_params)
        corr_matrix = df_numeric.corr()

        if corr_matrix.empty or corr_matrix.isna().all().all():
            continue

        fig = go.Figure(
            data=_create_heatmap(corr_matrix, param_labels, available_params)
        )

        fig.update_layout(
            title=f"Correlation Matrix – {s}",
            width=800,
            height=700,
            template="plotly_white",
            xaxis=dict(side="bottom"),
            yaxis=dict(autorange="reversed"),
            meta={"param_id": f"corr_matrix_{s}", "set": s, "type": "set"},
        )

        figures.append(fig)

    if devices:
        for device in devices:
            # find all sets
            device_pattern = f"_{device}_"
            device_sets = [
                s
                for s in scatter_df["source_file"].unique()
                if device_pattern in s or s.endswith(f"_{device}")
            ]
            if not device_sets:
                device_sets = [
                    s for s in scatter_df["source_file"].unique() if device in s
                ]

            if not device_sets:
                continue

            # aggregate all sets
            df_device = scatter_df[scatter_df["source_file"].isin(device_sets)].copy()
            if df_device.empty:
                continue

            df_numeric = _prepare_data(df_device, available_params)
            corr_matrix = df_numeric.corr()

            if corr_matrix.empty or corr_matrix.isna().all().all():
                continue

            fig = go.Figure(
                data=_create_heatmap(corr_matrix, param_labels, available_params)
            )

            fig.update_layout(
                title=f"Correlation Matrix – Device {device} (all sets aggregated)",
                width=800,
                height=700,
                template="plotly_white",
                xaxis=dict(side="bottom"),
                yaxis=dict(autorange="reversed"),
                meta={
                    "param_id": f"corr_matrix_device_{device}",
                    "device": device,
                    "type": "device",
                    "sets_included": device_sets,
                },
            )

            figures.append(fig)

    return figures
