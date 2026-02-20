from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def build_boxplots_fig(box_table: "pd.DataFrame", sets: list[str]) -> list[go.Figure]:
    """
    Creates a list of plotly Figure objects, one for each parameter.
    
    Features:
    - All axes are Log Scale.
    - Data is converted to absolute magnitude (handles negative I_reset/V_reset).
    - Grid lines are placed at magnitudes (1eX) and visual midpoints (labeled 5eX).
    """
    if box_table is None or box_table.empty or not sets:
        return []

    # Mapping of internal column names to pretty display names
    param_map = {
        "VSET": {"pretty": "V_set (V)"},
        "V_reset": {"pretty": "V_reset (V)"},
        "R_LRS": {"pretty": "R_LRS (Ω)"},
        "R_HRS": {"pretty": "R_HRS (Ω)"},
        "I_reset_max": {"pretty": "I_reset_max (A)"},
        "V_forming": {"pretty": "V_forming (V)"},
    }

    # Generate consistent colors for each source file
    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    # Generate custom log ticks
    # tick_vals: the mathematical position on the log axis
    # tick_text: the string shown to the user
    tick_vals = []
    tick_text = []
    for i in range(-15, 16):  # Range covers pA to TOhms
        # Major Magnitude (1, 10, 100...)
        major_val = 10.0**i
        tick_vals.append(major_val)
        tick_text.append(f"1e{i}" if i != 0 else "1")

        # Visual Midpoint
        # 10^(i + 0.5) is mathematically the center point between 10^i and 10^(i+1)
        mid_pos = 10.0**(i + 0.5)
        tick_vals.append(mid_pos)
        tick_text.append(f"5e{i}" if i != 0 else "0.5")

    figures = []

    for param, info in param_map.items():
        if param not in box_table.columns:
            continue

        fig = go.Figure()
        has_any_data = False

        for s in sets:
            df_s = box_table[box_table["source_file"] == s]
            
            # Data Cleaning
            vals = pd.to_numeric(df_s[param], errors="coerce").dropna()
            
            # 1. Take Absolute Magnitude (Mandatory for Log scale of negative currents/voltages)
            vals = vals.abs()
            
            # 2. Filter out Zeros (Log is undefined at 0)
            vals = vals[vals > 0]

            if not vals.empty:
                has_any_data = True
            
            fig.add_trace(go.Box(
                y=vals,
                name=s,
                marker_color=color_map.get(s),
                boxmean=False,
                line=dict(width=2),
                fillcolor=color_map.get(s),
                opacity=0.7
            ))

        # Apply the specialized Log Axis configuration
        fig.update_yaxes(
            type="log",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            title_text=f"|{info['pretty']}|",
            autorange=True,
            showgrid=True,
            gridcolor="#E5E5E5",
            minor_ticks="", # Hide the auto-generated small ticks
            zeroline=False,
        )

        fig.update_xaxes(
            title_text="Set / File",
            showgrid=True,
            gridcolor="#E5E5E5"
        )

        fig.update_layout(
            title=f"Boxplot – {info['pretty']} (Log Magnitude)",
            width=900,
            height=600,
            template="plotly_white",
            showlegend=True,
            boxmode="group",
            # Meta tag used by the PySide6 UI to identify the plot
            meta={"param_id": param}
        )

        # Placeholder if no valid data found
        if not has_any_data:
            fig.add_annotation(
                text="No valid positive data found for log scale",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color="red", size=14)
            )

        figures.append(fig)

    return figures