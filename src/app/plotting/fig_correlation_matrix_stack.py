from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def build_stack_level_correlation_matrix_figs(
        scatter_df: "pd.DataFrame",
        stack_id: str,
        devices: list[str]
) -> list[go.Figure]:
    """
    Stack-Level: Correlation matrix heatmap (one per device).
    Every device aggregates his endurance-sets.
    """
    if scatter_df is None or scatter_df.empty or not devices:
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

    for device in devices:
        # find all sets for device
        device_pattern = f"_{device}_"
        device_sets = [
            s for s in scatter_df["source_file"].unique()
            if device_pattern in s or s.endswith(f"_{device}")
        ]
        if not device_sets:
            device_sets = [s for s in scatter_df["source_file"].unique() if device in s]

        # aggregate all data from a device
        df_device = scatter_df[scatter_df["source_file"].isin(device_sets)].copy()
        if df_device.empty:
            continue

        # cleanup data
        df_numeric = df_device[available_params].apply(pd.to_numeric, errors="coerce")

        log_params = ["I_LRS", "I_HRS", "R_LRS", "R_HRS", "I_reset_max"]
        for p in available_params:
            if p in log_params:
                df_numeric[p] = df_numeric[p].abs()
                df_numeric.loc[df_numeric[p] <= 0, p] = np.nan

        # Correlation
        corr_matrix = df_numeric.corr()

        if corr_matrix.empty or corr_matrix.isna().all().all():
            continue

        # Heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=[param_labels.get(p, p) for p in available_params],
            y=[param_labels.get(p, p) for p in available_params],
            zmin=-1,
            zmax=1,
            colorscale="RdBu_r",
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
            hovertemplate="%{x} vs %{y}<br>Corr: %{z:.3f}<extra></extra>",
        ))

        fig.update_layout(
            title=f"Stack {stack_id} – Correlation Matrix – {device}",
            width=800,
            height=700,
            template="plotly_white",
            xaxis=dict(side="bottom"),
            yaxis=dict(autorange="reversed"),
            meta={
                "param_id": f"corr_matrix_{device}",
                "device": device,
                "level": "stack",
                "stack_id": stack_id,
            },
        )

        figures.append(fig)

    # Zusätzlich: Eine Matrix für den gesamten Stack (alle Devices aggregiert)
    df_all = scatter_df[scatter_df["source_file"].isin(
        [s for d in devices for s in scatter_df["source_file"].unique() if d in s]
    )].copy()

    if not df_all.empty:
        df_numeric_all = df_all[available_params].apply(pd.to_numeric, errors="coerce")
        for p in available_params:
            if p in log_params:
                df_numeric_all[p] = df_numeric_all[p].abs()
                df_numeric_all.loc[df_numeric_all[p] <= 0, p] = np.nan

        corr_matrix_all = df_numeric_all.corr()

        if not corr_matrix_all.empty:
            fig_all = go.Figure(data=go.Heatmap(
                z=corr_matrix_all.values,
                x=[param_labels.get(p, p) for p in available_params],
                y=[param_labels.get(p, p) for p in available_params],
                zmin=-1,
                zmax=1,
                colorscale="RdBu_r",
                text=np.round(corr_matrix_all.values, 2),
                texttemplate="%{text:.2f}",
                textfont={"size": 10},
                hovertemplate="%{x} vs %{y}<br>Corr: %{z:.3f}<extra></extra>",
            ))

            fig_all.update_layout(
                title=f"Stack {stack_id} – Correlation Matrix – All Devices",
                width=800,
                height=700,
                template="plotly_white",
                xaxis=dict(side="bottom"),
                yaxis=dict(autorange="reversed"),
                meta={
                    "param_id": "corr_matrix_stack_all",
                    "level": "stack",
                    "stack_id": stack_id,
                },
            )
            figures.append(fig_all)

    return figures