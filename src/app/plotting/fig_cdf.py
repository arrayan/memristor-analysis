from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def _cdf_xy(values: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """
    Return sorted x and cumulative probability in percent.
    Strictly filters for log-compatibility (absolute magnitude and > 0).
    """
    # 1. Convert to numeric and take absolute value
    v = pd.to_numeric(values, errors="coerce").dropna().abs().to_numpy()
    
    # 2. Filter out zeros (log scale requirement)
    v = v[v > 0]
    
    if v.size == 0:
        return np.array([]), np.array([])
        
    x = np.sort(v)
    y = (np.arange(1, x.size + 1) / x.size) * 100.0
    return x, y

def build_cdf_figs(cdf_table: "pd.DataFrame", sets: list[str]) -> list[go.Figure]:
    """
    Creates a list of CDF Figure objects, one for each parameter.
    Every figure is strictly configured with a Log scale on the X-axis.
    """
    if cdf_table is None or cdf_table.empty or not sets:
        return []

    # Map of internal column -> display names
    # Note: We now treat all as 'log' to match your boxplot requirements
    param_map = {
        "VSET": {"pretty": "V_set (V)"},
        "V_reset": {"pretty": "V_reset (V)"},
        "R_LRS": {"pretty": "R_LRS (Ω)"},
        "R_HRS": {"pretty": "R_HRS (Ω)"},
        "I_reset_max": {"pretty": "I_reset_max (A)"},
        "V_forming": {"pretty": "V_forming (V)"},
    }

    cols = px.colors.sample_colorscale("Viridis", max(len(sets), 2))
    color_map = {s: cols[i] for i, s in enumerate(sets)}

    # Generate custom log ticks (Visual Midpoint logic)
    tick_vals = []
    tick_text = []
    for i in range(-15, 16):
        major_val = 10.0**i
        tick_vals.append(major_val)
        tick_text.append(f"1e{i}" if i != 0 else "1")

        mid_pos = 10.0**(i + 0.5) # The mathematical visual center
        tick_vals.append(mid_pos)
        tick_text.append(f"5e{i}" if i != 0 else "0.5")

    figures = []

    for param, info in param_map.items():
        if param not in cdf_table.columns:
            continue

        fig = go.Figure()
        has_any_data = False

        for s in sets:
            df_s = cdf_table[cdf_table["source_file"] == s]
            x, y = _cdf_xy(df_s[param])
            
            if x.size > 0:
                has_any_data = True
                fig.add_trace(go.Scatter(
                    x=x, 
                    y=y,
                    mode="lines+markers", # Added markers to see data points better
                    name=s,
                    marker=dict(size=4),
                    line=dict(color=color_map.get(s), width=2),
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>"
                ))

        # X-Axis Configuration (The Log Scale)
        fig.update_xaxes(
            type="log",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            title_text=f"|{info['pretty']}|",
            exponentformat="power",
            showgrid=True,
            gridcolor="#E5E5E5",
            zeroline=False,
            # Ensure the range actually contains the data
            autorange=True 
        )

        # Y-Axis (Probability)
        fig.update_yaxes(
            title_text="Probability (%)",
            range=[-2, 102], # Slight padding to see 0 and 100 clearly
            showgrid=True,
            gridcolor="#E5E5E5"
        )

        fig.update_layout(
            title=f"CDF – {info['pretty']} (Log Scale)",
            width=900,
            height=600,
            template="plotly_white",
            showlegend=True,
            # This meta tag is used by your NavigationBar to name the tab
            meta={"param_id": param}
        )

        if not has_any_data:
            fig.add_annotation(
                text="No valid positive data found for log scale",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color="red", size=14)
            )

        figures.append(fig)

    return figures