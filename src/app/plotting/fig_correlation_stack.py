from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from .utils import has_valid_data, find_device_sets


def _prepare_leakage_with_forming(
        leakage_df: pd.DataFrame | None,
        forming_v: float | None
) -> pd.DataFrame:
    """
    Bereitet Leakage-Daten vor, berechnet R_pristine und fügt V_forming hinzu.
    """
    if leakage_df is None or leakage_df.empty:
        return pd.DataFrame()

    df = leakage_df.copy()

    # I_leakage aus AI
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

    # V_forming als konstante Spalte hinzufügen (für Korrelation)
    if forming_v is not None and not np.isnan(forming_v):
        df["V_forming"] = forming_v

    return df


def build_stack_level_correlation_figs(
        scatter_df: "pd.DataFrame",
        stack_id: str,
        devices: list[str],
        leakage_df: "pd.DataFrame | None" = None,
        forming_v: "float | None" = None,
        first_v_reset: "dict[str, float] | None" = None,
) -> list[go.Figure]:
    """
    Stack-Level: Correlation scatter plots (one per pair).
    Every device aggregates his endurance-sets.
    Includes Leakage correlations if data available.
    """
    if not has_valid_data(scatter_df, devices):
        return []

    # Basis pairs
    pairs = [
        ("V_set", "I_HRS", "V_set (V) vs I_HRS (A)"),
        ("V_set", "R_HRS", "V_set (V) vs R_HRS (Ω)"),
        ("V_reset", "I_LRS", "V_reset (V) vs I_LRS (A)"),
        ("V_reset", "R_LRS", "V_reset (V) vs R_LRS (Ω)"),
        ("V_reset", "I_reset_max", "V_reset (V) vs I_reset_max (A)"),
        ("V_set", "V_reset", "V_set (V) vs V_reset (V)"),
    ]

    # Leakage-Daten vorbereiten
    prepared_leakage = _prepare_leakage_with_forming(leakage_df, forming_v)

    # Leakage pairs hinzufügen (falls Daten vorhanden)
    if not prepared_leakage.empty and forming_v is not None:
        if "I_leakage" in prepared_leakage.columns:
            pairs.append(("V_forming", "I_leakage", "V_forming (V) vs I_leakage (A)"))
        if "R_pristine" in prepared_leakage.columns:
            pairs.append(("V_forming", "R_pristine", "V_forming (V) vs R_pristine (Ω)"))

    # V_forming vs 1st V_reset: inject both as scalar columns into scatter_df
    # so the existing per-device aggregation loop works unchanged.
    # Build a per-device scalar DataFrame for the V_forming vs 1st V_reset pair.
    # Each device gets its own (V_forming, first_V_reset) point.
    include_forming_reset_pair = (
        forming_v is not None
        and not np.isnan(forming_v)
        and first_v_reset  # non-empty dict
    )
    if include_forming_reset_pair:
        forming_reset_rows = [
            {"device": device, "V_forming": forming_v, "first_V_reset": first_v_reset[device]}
            for device in devices
            if device in first_v_reset
        ]
        forming_reset_df = pd.DataFrame(forming_reset_rows)
        pairs.append(("V_forming", "first_V_reset", "V_forming (V) vs 1st V_reset (V)"))
    else:
        forming_reset_df = pd.DataFrame()

    def get_scale(col_name):
        return "log" if any(x in col_name for x in ["I_", "R_"]) else "linear"

    base_cols = px.colors.qualitative.Plotly
    device_color_map = {d: base_cols[i % len(base_cols)] for i, d in enumerate(devices)}

    tick_vals = [10.0 ** i for i in range(-15, 16)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 16)]

    figures = []

    for x_col, y_col, title_text in pairs:
        # Bestimme Datenquelle
        is_leakage_pair = x_col in ["V_forming"] and y_col in ["I_leakage", "R_pristine"]
        is_forming_reset_pair = x_col == "V_forming" and y_col == "first_V_reset"

        if is_leakage_pair:
            if prepared_leakage.empty:
                continue
            data_source = prepared_leakage
        elif is_forming_reset_pair:
            if forming_reset_df.empty:
                continue
            data_source = None  # handled separately below
        else:
            data_source = scatter_df

        if not is_forming_reset_pair:
            # Prüfe ob Spalten existieren
            if x_col not in data_source.columns or y_col not in data_source.columns:
                continue

        fig = go.Figure()
        x_scale = get_scale(x_col)
        y_scale = get_scale(y_col)

        all_x, all_y = [], []

        if is_forming_reset_pair:
            # One point per device, values already in forming_reset_df
            for _, row in forming_reset_df.iterrows():
                device = row["device"]
                x_val = float(row["V_forming"])
                y_val = float(row["first_V_reset"])
                all_x.append(x_val)
                all_y.append(y_val)
                fig.add_trace(
                    go.Scatter(
                        x=[x_val],
                        y=[y_val],
                        mode="markers",
                        marker=dict(color=device_color_map.get(device), size=10, opacity=0.9),
                        name=device,
                        legendgroup=device,
                        hovertemplate=f"Device: {device}<br>V_forming: %{{x:.3f}} V<br>1st V_reset: %{{y:.3f}} V<extra></extra>",
                    )
                )
        else:
            for device in devices:
                device_sets = find_device_sets(data_source, device)

                # aggregate
                df_device = data_source[data_source["source_file"].isin(device_sets)].copy()
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
                        marker=dict(color=device_color_map[device], size=7, opacity=0.7),
                        name=device,
                        legendgroup=device,
                        hovertemplate=f"Device: {device}<br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>",
                    )
                )

        if not all_x or not all_y:
            continue

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
            meta={"param_id": param_id, "level": "stack", "stack_id": stack_id},
        )
        figures.append(fig)

    return figures