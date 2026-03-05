from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def build_characteristic_figs(
    raw_by_set: dict[str, "pd.DataFrame"],
    sets: list[str],
    raw_reset_by_set: "dict[str, pd.DataFrame] | None" = None,
) -> list[go.Figure]:
    """
    Creates three figures:
    1. AI (Current) vs AV - Log Scale
    2. NORM_COND (Conductance) vs AV - Linear Scale
    3. Butterfly Curve - Set + Reset |I| vs V, all cycles overlaid
    """
    if not sets:
        return []

    base_cols = px.colors.qualitative.Plotly
    set_color_map = {s: base_cols[i % len(base_cols)] for i, s in enumerate(sets)}

    tick_vals = [10.0**i for i in range(-15, 1)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 1)]

    figures = []

    # AI vs AV
    fig1 = go.Figure()
    all_y_vals_1 = []

    for s in sets:
        df = raw_by_set[s]
        cycles = df["cycle_number"].unique()
        color = set_color_map[s]

        for idx, cyc in enumerate(cycles):
            tiny = df[df["cycle_number"] == cyc]

            y_vals = pd.to_numeric(tiny["AI"], errors="coerce").abs()
            all_y_vals_1.extend(y_vals[y_vals > 0].tolist())

            fig1.add_trace(
                go.Scatter(
                    x=tiny["AV"],
                    y=y_vals,
                    mode="lines",
                    line=dict(color=color, width=1.2),
                    opacity=0.5,
                    name=f"Cycle {cyc}",
                    legendgroup=s,
                    legendgrouptitle=dict(text=s) if idx == 0 else None,
                    showlegend=(idx == 0),
                    hovertemplate=f"Set: {s}<br>Cycle: {cyc}<br>V: %{{x}}V<br>I: %{{y}}<extra></extra>",
                )
            )

    fig1.update_xaxes(
        title_text="AV (V)",
        autorange="reversed",
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="gray",
    )

    yaxis_config_1 = dict(
        type="log",
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_text,
        exponentformat="power",
        gridcolor="#E5E5E5",
        minor=dict(showgrid=False),
        title_text="|Current (A)|",
    )
    if all_y_vals_1:
        lmin, lmax = np.log10(min(all_y_vals_1)), np.log10(max(all_y_vals_1))
        if (lmax - lmin) < 1.0:
            mid = (lmin + lmax) / 2
            yaxis_config_1["range"] = [mid - 0.55, mid + 0.55]
    fig1.update_yaxes(**yaxis_config_1)

    fig1.update_layout(
        title="Characteristic Plot – |Current| vs V (All Sets)",
        width=1000,
        height=700,
        template="plotly_white",
        legend=dict(groupclick="togglegroup", title="Files"),
        meta={"param_id": "AI"},
    )
    figures.append(fig1)

    # NORM_COND vs AV
    fig2 = go.Figure()
    all_y_vals_2 = []

    for s in sets:
        df = raw_by_set[s]
        cycles = df["cycle_number"].unique()
        color = set_color_map[s]

        for idx, cyc in enumerate(cycles):
            tiny = df[df["cycle_number"] == cyc]

            y_vals = pd.to_numeric(tiny["NORM_COND"], errors="coerce")
            all_y_vals_2.extend(y_vals.dropna().tolist())

            fig2.add_trace(
                go.Scatter(
                    x=tiny["AV"],
                    y=y_vals,
                    mode="lines",
                    line=dict(color=color, width=1.2),
                    opacity=0.5,
                    name=f"Cycle {cyc}",
                    legendgroup=s,
                    legendgrouptitle=dict(text=s) if idx == 0 else None,
                    showlegend=(idx == 0),
                    hovertemplate=f"Set: {s}<br>Cycle: {cyc}<br>V: %{{x}}V<br>Cond: %{{y}}<extra></extra>",
                )
            )

    fig2.update_xaxes(
        title_text="AV (V)",
        autorange="reversed",
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="gray",
    )
    fig2.update_yaxes(
        type="linear",
        title_text="Conductance (S)",
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="gray",
        autorange=True,
    )
    fig2.update_layout(
        title="Characteristic Plot – Conductance vs V (All Sets)",
        width=1000,
        height=700,
        template="plotly_white",
        legend=dict(groupclick="togglegroup", title="Files"),
        meta={"param_id": "NORM_COND"},
    )
    figures.append(fig2)

    # BUTTERFLY CURVE – one plot per device, all endurance_set files aggregated.
    # Set sweeps: solid lines. Reset sweeps: dashed lines. Same color per device.

    def _extract_device(source_file: str) -> str:
        """Extract device token (index 1) from {stack}_{device}_{nr}_{type}."""
        parts = source_file.split("_")
        return parts[1] if len(parts) >= 2 else source_file

    # Group set files by device
    device_set_files: dict[str, list[str]] = {}
    for s in sets:
        dev = _extract_device(s)
        device_set_files.setdefault(dev, []).append(s)

    # Group reset files by device
    device_reset_files: dict[str, list[str]] = {}
    if raw_reset_by_set:
        for rf in raw_reset_by_set:
            dev = _extract_device(rf)
            device_reset_files.setdefault(dev, []).append(rf)

    devices_sorted = sorted(device_set_files.keys())
    dev_colors = px.colors.sample_colorscale("Viridis", max(len(devices_sorted), 2))
    dev_color_map = {d: dev_colors[i] for i, d in enumerate(devices_sorted)}

    for device in devices_sorted:
        fig_butterfly = go.Figure()
        all_i_vals = []
        color = dev_color_map[device]
        first_set_trace = True
        first_reset_trace = True

        # Set and reset files get distinct colors; same file = same color across cycles.
        all_legend_files = (
            device_set_files[device]
            + device_reset_files.get(device, [])
        )
        file_colors = px.colors.qualitative.Plotly
        file_color_map = {f: file_colors[i % len(file_colors)] for i, f in enumerate(all_legend_files)}

        # --- Set sweeps (all files for this device) ---
        for s in device_set_files[device]:
            df_set = raw_by_set[s]
            for idx, cyc in enumerate(df_set["cycle_number"].unique()):
                tiny = df_set[df_set["cycle_number"] == cyc]
                av = pd.to_numeric(tiny["AV"], errors="coerce")
                ai = pd.to_numeric(tiny["AI"], errors="coerce").abs()
                valid = ai > 0
                av_v, ai_v = av[valid], ai[valid]
                all_i_vals.extend(ai_v.tolist())
                fig_butterfly.add_trace(
                    go.Scatter(
                        x=av_v,
                        y=ai_v,
                        mode="lines",
                        line=dict(color=file_color_map[s], width=1.2, dash="solid"),
                        opacity=0.5,
                        name=s,
                        legendgroup=s,
                        showlegend=(idx == 0),
                        hovertemplate=f"Set: {s}<br>Cycle: {cyc}<br>V: %{{x:.3f}} V<br>|I|: %{{y}}<extra></extra>",
                    )
                )

        # --- Reset sweeps (all files for this device) ---
        for rf in device_reset_files.get(device, []):
            df_reset = raw_reset_by_set[rf]
            for idx, cyc in enumerate(df_reset["cycle_number"].unique()):
                tiny = df_reset[df_reset["cycle_number"] == cyc]
                av = pd.to_numeric(tiny["AV"], errors="coerce")
                ai = pd.to_numeric(tiny["AI"], errors="coerce").abs()
                valid = ai > 0
                av_v, ai_v = av[valid], ai[valid]
                all_i_vals.extend(ai_v.tolist())
                fig_butterfly.add_trace(
                    go.Scatter(
                        x=av_v,
                        y=ai_v,
                        mode="lines",
                        line=dict(color=file_color_map[rf], width=1.2, dash="dash"),
                        opacity=0.5,
                        name=rf,
                        legendgroup=rf,
                        showlegend=(idx == 0),
                        hovertemplate=f"Reset: {rf}<br>Cycle: {cyc}<br>V: %{{x:.3f}} V<br>|I|: %{{y}}<extra></extra>",
                    )
                )

        yaxis_config_butterfly = dict(
            type="log",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            exponentformat="power",
            gridcolor="#E5E5E5",
            minor=dict(showgrid=False),
            title_text="|I| (A)",
        )
        if all_i_vals:
            lmin, lmax = np.log10(min(all_i_vals)), np.log10(max(all_i_vals))
            if (lmax - lmin) < 1.0:
                mid = (lmin + lmax) / 2
                yaxis_config_butterfly["range"] = [mid - 0.55, mid + 0.55]
            else:
                pad = (lmax - lmin) * 0.05
                yaxis_config_butterfly["range"] = [lmin - pad, lmax + pad]
        fig_butterfly.update_yaxes(**yaxis_config_butterfly)

        fig_butterfly.update_xaxes(
            title_text="V (V)",
            gridcolor="#E5E5E5",
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=2,
            autorange=True,
        )

        fig_butterfly.add_vline(x=0, line_width=2, line_color="black")

        fig_butterfly.update_layout(
            title=f"Butterfly Curve – Device {device} | solid = Set, dashed = Reset",
            width=1000,
            height=700,
            template="plotly_white",
            legend=dict(groupclick="toggleitem", title="Files"),
            meta={"param_id": f"butterfly_{device}"},
        )
        figures.append(fig_butterfly)

    return figures