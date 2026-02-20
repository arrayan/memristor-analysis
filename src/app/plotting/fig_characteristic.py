from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def build_characteristic_figs(
    raw_by_set: dict[str, "pd.DataFrame"], sets: list[str]
) -> list[go.Figure]:
    """
    Creates two figures: 
    1. AI (Current) vs AV - Log Scale
    2. NORM_COND (Conductance) vs AV - Linear Scale
    
    All sets are displayed in the same plot, colored by file.
    """
    if not sets:
        return []

    param_map = {
        "AI": {"pretty": "Current (A)", "scale": "log"},
        "NORM_COND": {"pretty": "Conductance (S)", "scale": "linear"},
    }

    # Unique color per set (file)
    base_cols = px.colors.qualitative.Plotly
    set_color_map = {s: base_cols[i % len(base_cols)] for i, s in enumerate(sets)}

    # Log ticks for AI
    tick_vals = [10.0**i for i in range(-15, 1)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 1)]

    figures = []

    for y_col, info in param_map.items():
        fig = go.Figure()
        is_log = (info["scale"] == "log")
        all_y_vals = []

        for s in sets:
            df = raw_by_set[s]
            cycles = df["cycle_number"].unique()
            color = set_color_map[s]

            for idx, cyc in enumerate(cycles):
                tiny = df[df["cycle_number"] == cyc]
                
                # Data cleaning
                y_vals = pd.to_numeric(tiny[y_col], errors="coerce")
                if is_log:
                    y_vals = y_vals.abs()
                    all_y_vals.extend(y_vals[y_vals > 0].tolist())
                else:
                    all_y_vals.extend(y_vals.dropna().tolist())

                fig.add_trace(
                    go.Scatter(
                        x=tiny["AV"],
                        y=y_vals,
                        mode="lines",
                        line=dict(color=color, width=1.2),
                        opacity=0.5,
                        name=s,
                        legendgroup=s,
                        showlegend=(idx == 0), # Only show set name once in legend
                        hovertemplate=f"Set: {s}<br>Cycle: {cyc}<br>V: %{{x}}V<br>Y: %{{y}}<extra></extra>"
                    )
                )

        # X-Axis (Voltage)
        fig.update_xaxes(
            title_text="AV (V)",
            autorange="reversed",
            gridcolor="#E5E5E5",
            zeroline=True,
            zerolinecolor="gray"
        )

        # Y-Axis
        if is_log:
            yaxis_config = dict(
                type="log",
                tickmode="array",
                tickvals=tick_vals,
                ticktext=tick_text,
                exponentformat="power",
                gridcolor="#E5E5E5",
                minor=dict(showgrid=False),
                title_text=f"|{info['pretty']}|"
            )
            # Ensure visible grid lines
            if all_y_vals:
                lmin, lmax = np.log10(min(all_y_vals)), np.log10(max(all_y_vals))
                if (lmax - lmin) < 1.0:
                    mid = (lmin + lmax) / 2
                    yaxis_config["range"] = [mid - 0.55, mid + 0.55]
            fig.update_yaxes(**yaxis_config)
        else:
            fig.update_yaxes(
                type="linear",
                title_text=info['pretty'],
                gridcolor="#E5E5E5",
                zeroline=True,
                zerolinecolor="gray",
                autorange=True
            )

        fig.update_layout(
            title=f"Characteristic Plot – {info['pretty']} (All Sets)",
            width=1000,
            height=700,
            template="plotly_white",
            legend=dict(groupclick="toggleitem", title="Files (Click to toggle)"),
            meta={"param_id": y_col}
        )

        figures.append(fig)

    return figures