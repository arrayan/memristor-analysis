from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def build_characteristic_fig(
    raw_by_set: dict[str, "pd.DataFrame"], sets: list[str]
) -> go.Figure:
    """
    Displays AI and NORM_COND vs AV. 
    All sets are displayed simultaneously in the same plot.
    Dropdown allows switching between AI (Log) and NORM_COND (Linear).
    """
    if not sets:
        return go.Figure()

    fig = go.Figure()

    # 1. Setup Colors: Unique color per set
    # Cycles within a set will share the same color to prevent a "rainbow mess"
    base_cols = px.colors.qualitative.Plotly
    set_color_map = {s: base_cols[i % len(base_cols)] for i, s in enumerate(sets)}

    y_label_map = {"AI": "Current |AI| (A)", "NORM_COND": "Conductance NORM_COND (S)"}

    # 2. Add Traces
    for y_col in ["AI", "NORM_COND"]:
        is_log = (y_col == "AI")
        
        for s in sets:
            df = raw_by_set[s]
            cycles = df["cycle_number"].unique()
            color = set_color_map[s]

            for idx, cyc in enumerate(cycles):
                tiny = df[df["cycle_number"] == cyc]
                
                # Prep Y values (Absolute for AI log scale)
                y_vals = tiny[y_col].abs() if is_log else tiny[y_col]

                fig.add_trace(
                    go.Scatter(
                        x=tiny["AV"],
                        y=y_vals,
                        mode="lines",
                        line=dict(color=color, width=1.2),
                        opacity=0.5,
                        name=s, # Show set name in legend
                        legendgroup=s, # Clicking the legend toggles the whole set
                        showlegend=(idx == 0 and y_col == "AI"), # Show each set once in legend
                        visible=(y_col == "AI"), # Default to AI visible
                        meta={"y": y_col, "set": s},
                        hovertemplate=f"Set: {s}<br>Cycle: {cyc}<br>V: %{{x}}V<br>I: %{{y}}A<extra></extra>"
                    )
                )

    # 3. Axis Configurations
    # AI Axis (Log)
    tick_vals = [10.0**i for i in range(-15, 1)]
    tick_text = [f"1e{i}" if i != 0 else "1" for i in range(-15, 1)]
    
    yaxis_ai = dict(
        type="log",
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_text,
        exponentformat="power",
        title=y_label_map["AI"],
        gridcolor="#E5E5E5",
        minor=dict(showgrid=False)
    )

    # NORM_COND Axis (Linear)
    yaxis_norm = dict(
        type="linear",
        title=y_label_map["NORM_COND"],
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="gray",
        autorange=True
    )

    # 4. Dropdown Buttons (Switching Y-Parameter only)
    def get_vis(y_val: str) -> list[bool]:
        # Returns True if trace belongs to the chosen parameter, regardless of set
        return [tr.meta["y"] == y_val for tr in fig.data]

    y_buttons = [
        dict(
            label="Current (AI)",
            method="update",
            args=[
                {"visible": get_vis("AI"), "showlegend": [tr.meta["y"] == "AI" and fig.data.index(tr) % len(fig.data)//2 == 0 for tr in fig.data]}, # Internal logic to keep legend clean
                {"yaxis": yaxis_ai, "title": "Characteristic Plot - Current (All Sets)"}
            ],
        ),
        dict(
            label="Conductance (NORM_COND)",
            method="update",
            args=[
                {"visible": get_vis("NORM_COND")},
                {"yaxis": yaxis_norm, "title": "Characteristic Plot - Conductance (All Sets)"}
            ],
        )
    ]

    # Special logic to ensure legend items update correctly when switching
    # (Since we have duplicate names for AI and NORM_COND traces)
    for i, tr in enumerate(fig.data):
        # Only the first cycle of the first parameter (AI) gets a legend entry initially
        if tr.meta["y"] == "NORM_COND":
            # We hide legend for NORM_COND initially, it will be enabled via button args if needed
            # but simpler is just to let them share the same legend groups.
            pass

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=y_buttons,
                direction="down",
                showactive=True,
                x=1.02, xanchor="left",
                y=1.1, yanchor="top",
            )
        ],
        title="Characteristic Plot - Current (All Sets)",
        xaxis=dict(title="AV (V)", autorange="reversed", gridcolor="#E5E5E5"),
        yaxis=yaxis_ai,
        width=1000,
        height=700,
        template="plotly_white",
        legend=dict(groupclick="toggleitem", title="Files (Click to toggle)")
    )

    return fig