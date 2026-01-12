import os
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------
# 1) DuckDB + set list
# ------------------------------------------------------------------
DB_FILE = Path(os.environ["MEMRISTOR_DB"]).expanduser()
conn = duckdb.connect(str(DB_FILE))

#discover endurance set files
sets = sorted([r[0] for r in conn.execute(
    "SELECT DISTINCT source_file FROM cycles WHERE source_file LIKE '%endurance set'"
).fetchall()])

# ------------------------------------------------------------------
# 2) Cache DataFrames (AI / NORM_COND)
# ------------------------------------------------------------------
data = {}
for s in sets:
    df = conn.execute(
    "SELECT cycle_number, AV, AI, NORM_COND FROM cycles WHERE source_file = ? ORDER BY cycle_number, Time",
    [s]
    ).df()

    data[s] = df
conn.close()

# ------------------------------------------------------------------
# 3) Figure – AI / NORM_COND vs AV
# ------------------------------------------------------------------
#skeleton figure
fig = go.Figure()

colors = {}
for s in sets:
    n = data[s]["cycle_number"].nunique()
    colors[s] = px.colors.sample_colorscale("Viridis", n)

trace_map = []   # helps to track which trace is which
y_label_map = {"AI": "AI (A)", "NORM_COND": "NORM_COND (S)"}

#prep traces
for y_col in ["AI", "NORM_COND"]:
    for s in sets:
        df = data[s]
        for idx, cyc in enumerate(df["cycle_number"].unique()):
            tiny = df[df["cycle_number"] == cyc]
            fig.add_trace(
                go.Scatter(
                    x=tiny["AV"],
                    y=tiny[y_col].abs() if y_col == "AI" else tiny[y_col],
                    mode="lines",
                    line=dict(color=colors[s][idx], width=1.5),
                    opacity=0.7,
                    name=f"Cycle {cyc}",
                    visible=False,
                    showlegend=False,
                    meta={"set": s, "y": y_col}
                )
            )
            trace_map.append({"set": s, "y": y_col})

#default visibility
for tr, info in zip(fig.data, trace_map):
    tr.visible = (info["y"] == "AI") and (info["set"] == sets[0])

#helper - visibility mask
def build_vis(y_val, set_val):
    return [tr.meta["y"] == y_val and tr.meta["set"] == set_val for tr in fig.data]

#axis template
norm_min = min(df["NORM_COND"].min() for df in data.values())
norm_max = max(df["NORM_COND"].max() for df in data.values())
norm_min = 0 if norm_min < 0 else norm_min
norm_max = np.ceil(norm_max / 5) * 5 

y_buttons, set_buttons = [], [] #lists for dropdowns

yaxis_ai = dict(
    type="log",
    tickmode="array",
    tickvals=10.**np.arange(-12, 0),
    ticktext=[f"1×10<sup>{int(np.log10(d))}</sup>" for d in 10.**np.arange(-12, 0)],
    title="AI (A)"
)
yaxis_norm = dict(
    type="linear",
    tickmode="linear",
    tick0=0,
    dtick=5,
    range=[norm_min, norm_max],
    title="NORM_COND (S)"
)

for y_col in ["AI", "NORM_COND"]:
    visible = build_vis(y_col, sets[0])
    yax = yaxis_ai if y_col == "AI" else yaxis_norm
    y_buttons.append(
        dict(label=y_label_map[y_col],
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,                    # replace entire axis
                    "title": f"{sets[0]} – {y_label_map[y_col]}"}])
    )

for s in sets:
    current_y = next(tr.meta["y"] for tr in fig.data if tr.visible)
    visible = build_vis(current_y, s)
    yax = yaxis_ai if current_y == "AI" else yaxis_norm
    set_buttons.append(
        dict(label=s,
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,                    # replace entire axis
                    "title": f"{s} – {y_label_map[current_y]}"}])
    )

#final layout tweaks
fig.update_xaxes(autorange="reversed", title="AV (V)")
dticks = 10.**np.arange(-12, -5)
fig.update_yaxes(
    type="log",
    tickmode="array",
    tickvals=dticks,
    ticktext=[f"1×10<sup>{int(np.log10(d))}</sup>" for d in dticks],
    title="AI (A)"
)

# NORM_COND-Axis (linear) – dynamic
# Min/Max for all Sets
norm_min = min(df["NORM_COND"].min() for df in data.values())
norm_max = max(df["NORM_COND"].max() for df in data.values())
norm_min = 0 if norm_min < 0 else norm_min
norm_max = np.ceil(norm_max / 5) * 5  # sum up to next 5

# Axis-Update for NORM_COND
for btn in y_buttons:
    if btn["label"] == "NORM_COND (S)":
        btn["args"][1]["yaxis"] = dict(
            type="linear",
            tickmode="linear",
            tick0=0, dtick=5,
            range=[norm_min, norm_max],
            title="NORM_COND (S)"
        )
        break

#add dropdowns
fig.update_layout(
    updatemenus=[
        dict(buttons=y_buttons, direction="down", showactive=True,
             x=1.02, xanchor="left", y=1.15, yanchor="top"),
        dict(buttons=set_buttons, direction="down", showactive=True,
             x=1.02, xanchor="left", y=1.05, yanchor="top")
    ],
    title=f"{sets[0]} – AI vs AV",
    width=900, height=600
)

#output
html_out = DB_FILE.with_name("characteristic_plots.html")
fig.write_html(html_out)
print(f"Fertig → {html_out}")
fig.show()

# ==================================================================
# 4) CDF PLOTS – V_set, R_LRS, R_HRS, V_reset
# ==================================================================
#reuse cached data
cdf_conn = duckdb.connect(str(DB_FILE))

forming_df = cdf_conn.execute(
    "SELECT MAX(VFORM) as V_forming_global "
    "FROM cycles "
    "WHERE source_file LIKE '%Electroforming%' "
).df()

V_forming_global = forming_df["V_forming_global"].iloc[0] if not forming_df.empty else None
#print("Globale V_forming:", V_forming_global)

classic = cdf_conn.execute(
    "SELECT source_file, cycle_number, "
    "MAX(VSET)  as VSET, "
    "MAX(ILRS)  as R_LRS, "
    "MAX(IHRS)  as R_HRS "
    "FROM cycles "
    "WHERE source_file LIKE '%endurance set' "
    "GROUP BY source_file, cycle_number "
    "ORDER BY source_file, cycle_number"
).df()

vreset = []
ireset = []
for s in sets:
    df_s = data[s]
    # V_reset: AV at max|AI|
    vreset_s = (df_s.groupby("cycle_number")[["AV", "AI"]]
                    .apply(lambda g: g.loc[g["AI"].abs().idxmax(), "AV"],
                           include_groups=False)
                    .reset_index(name="V_reset"))
    vreset_s["source_file"] = s
    vreset.append(vreset_s)
    
    # I_reset_max: max|AI|
    ireset_s = (df_s.groupby("cycle_number")["AI"]
                    .apply(lambda x: x.abs().max())
                    .reset_index(name="I_reset_max"))
    ireset_s["source_file"] = s
    ireset.append(ireset_s)

vreset_df = pd.concat(vreset, ignore_index=True)
ireset_df = pd.concat(ireset, ignore_index=True)
cdf_full = classic.merge(vreset_df, on=["source_file", "cycle_number"], how="left").merge(ireset_df, on=["source_file", "cycle_number"], how="left")
cdf_full["V_forming"] = V_forming_global

#parameter mapping + scaling
param_map = {
    "VSET":    {"pretty": "V_set (V)",   "scale": "linear"},
    "V_forming": {"pretty": "V_forming (V)", "scale": "linear"},
    "R_LRS":   {"pretty": "R_LRS (Ω)",   "scale": "log"},
    "R_HRS":   {"pretty": "R_HRS (Ω)",   "scale": "log"},
    "V_reset": {"pretty": "V_reset (V)", "scale": "linear"},
    "I_reset_max": {"pretty": "I_reset_max (A)", "scale": "log"}
}
set_colors = px.colors.sample_colorscale("Viridis", len(sets))

cdf_fig = go.Figure()

# 5. Traces: Combinations (Param, Set) – only one param visible at a time
first_param = "VSET"
first_set   = sets[0]

for param, info in param_map.items():
    for s, sc in zip(sets, set_colors):
        vals = cdf_full[cdf_full["source_file"] == s][param].dropna().sort_values().to_numpy()
        if vals.size == 0:
            continue
        n = vals.size
        p = np.arange(1, n + 1) / n * 100
        cdf_fig.add_trace(
            go.Scatter(
                x=vals,
                y=p,
                mode="lines",
                name=s,
                line=dict(color=sc, width=2),
                hovertemplate=f"{info['pretty']}: %{{x:.2e}}<br>Probability: %{{y:.1f}}%<extra></extra>",
                visible=((param == first_param) and (s == first_set)),
                meta={"param": param, "set": s}
            )
        )

#helper - visibility mask
def build_vis(param, set_val):
    return [tr.meta["param"] == param and tr.meta["set"] == set_val for tr in cdf_fig.data]

# dropdowns + buttons
param_buttons = []
for param, info in param_map.items():
    visible = build_vis(param, first_set)
    yax = dict(type=info["scale"], title=info["pretty"])
    param_buttons.append(
        dict(label=info["pretty"],
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,
                    "xaxis.title.text": info["pretty"],
                    "title": f"CDF – {info['pretty']} ({first_set})"}])
    )

set_buttons = []
for s in sets:
    current_param = next(tr.meta["param"] for tr in cdf_fig.data if tr.visible)
    visible = build_vis(current_param, s)
    info = param_map[current_param]
    yax = dict(type=info["scale"], title=info["pretty"])
    set_buttons.append(
        dict(label=s,
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,
                    "xaxis.title.text": info["pretty"],
                    "title": f"CDF – {info['pretty']} ({s})"}])
    )

#Layout
cdf_fig.update_layout(
    updatemenus=[
        dict(buttons=param_buttons, direction="down", showactive=True,
             x=1.02, xanchor="left", y=1.15, yanchor="top",
             name="Parameter"),
        dict(buttons=set_buttons, direction="down", showactive=True,
             x=1.02, xanchor="left", y=1.05, yanchor="top",
             name="Set")
    ],
    title=f"CDF – {param_map[first_param]['pretty']} ({first_set})",
    xaxis_title=param_map[first_param]["pretty"],
    yaxis_title="Probability (%)",
    width=900, height=600,
    hovermode="x unified"
)

cdf_html = DB_FILE.with_name("endurance_cdf.html")
cdf_fig.write_html(cdf_html)
print(f"CDF → {cdf_html}")
cdf_conn.close()

# ==================================================================
# 5) BOXPLOTS – V_set, V_reset, R_LRS, R_HRS
# ==================================================================
#reuse cached data
box_conn = duckdb.connect(str(DB_FILE))

forming_df = box_conn.execute(
    "SELECT MAX(VFORM) as V_forming_global "
    "FROM cycles "
    "WHERE source_file LIKE '%Electroforming%' "
).df()

V_forming_global = forming_df["V_forming_global"].iloc[0] if not forming_df.empty else None
#print("Globale V_forming:", V_forming_global)

classic_box = box_conn.execute(
    "SELECT source_file, cycle_number, "
    "MAX(VSET)  as V_set, "
    "MAX(ILRS)  as R_LRS, "
    "MAX(IHRS)  as R_HRS "
    "FROM cycles "
    "WHERE source_file LIKE '%endurance set' "
    "GROUP BY source_file, cycle_number "
    "ORDER BY source_file, cycle_number"
).df()

vreset_box = []
ireset_box = []
for s in sets:
    df_s = data[s]
    vreset_s = (df_s.groupby("cycle_number")[["AV", "AI"]]
                    .apply(lambda g: g.loc[g["AI"].abs().idxmax(), "AV"],
                           include_groups=False)
                    .reset_index(name="V_reset"))
    vreset_s["source_file"] = s
    vreset_box.append(vreset_s)

    # I_reset_max: max|AI|
    ireset_s = (df_s.groupby("cycle_number")["AI"]
                    .apply(lambda x: x.abs().max())
                    .reset_index(name="I_reset_max"))
    ireset_s["source_file"] = s
    ireset_box.append(ireset_s)

vreset_box_df = pd.concat(vreset_box, ignore_index=True)
ireset_box_df = pd.concat(ireset_box, ignore_index=True)

box_data = classic_box.merge(vreset_box_df, on=["source_file", "cycle_number"], how="left").merge(ireset_box_df, on=["source_file", "cycle_number"], how="left")
box_data["V_forming"] = V_forming_global

#parameter mapping + scaling
param_map = {
    "V_set":   {"pretty": "V_set (V)",   "scale": "linear"},
    "V_forming": {"pretty": "V_forming (V)", "scale": "linear"},
    "V_reset": {"pretty": "V_reset (V)", "scale": "linear"},
    "R_LRS":   {"pretty": "R_LRS (Ω)",   "scale": "log"},
    "R_HRS":   {"pretty": "R_HRS (Ω)",   "scale": "log"},
    "I_reset_max": {"pretty": "I_reset_max (A)", "scale": "log"}
}

#boxplots
box_fig = go.Figure()
first_param = "V_set"
set_cols = px.colors.sample_colorscale("Viridis", len(sets))

for param, info in param_map.items():
    for s, col in zip(sets, set_cols):
        vals = box_data[box_data["source_file"] == s][param].dropna()
        if vals.empty:
            continue
        q = vals.quantile([0, 0.25, 0.5, 0.75, 1])
        # Boxplot
        box_fig.add_trace(
            go.Box(
                y=vals,
                name=s,
                boxmean=False,               # no Mean
                marker_color=col,
                line=dict(width=2),
                visible=(param == first_param),
                meta={"param": param},
                # set whiskers to Q1/Q3 (no fences)
                lowerfence=[q[0]],
                upperfence=[q[1]],
                boxpoints=False,
                whiskerwidth=1
            )
        )

# 4. Statistics as text above boxes
#stats_traces = []
#for s in sets[:1]:
#    for param, info in param_map.items():
#        vals = box_data[box_data["source_file"] == s][param].dropna()
#        if vals.empty:
#            continue
#        q = vals.quantile([0, 0.25, 0.5, 0.75, 1])
#        txt = (f"<b>{s}</b><br>"
#               f"Min={q[0]:.2e}<br>Q1={q[0.25]:.2e}<br>"
#               f"Med={q[0.5]:.2e}<br>Q3={q[0.75]:.2e}<br>Max={q[1]:.2e}")
#        stats_traces.append(
#            go.Scatter(
#                x=[s], y=[q[1] * 1.3],
#                mode="text",
#                text=[txt],
#                textposition="top center",
#                visible=(param == first_param),
#                meta={"param": param},
#                showlegend=False,
#                hoverinfo="skip"
#            )
#        )
#box_fig.add_traces(stats_traces)


#dropdown
buttons = []
for param, info in param_map.items():
    visible = [tr.meta["param"] == param for tr in box_fig.data]
    yax = dict(type=info["scale"], title=info["pretty"])
    buttons.append(
        dict(label=info["pretty"],
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,
                    "title": f"Boxplot – {info['pretty']}"}])
    )

#layout
box_fig.update_layout(
    updatemenus=[dict(buttons=buttons, direction="down", showactive=True,
                      x=1.02, xanchor="left", y=1.15, yanchor="top")],
    title=f"Boxplot – {param_map[first_param]['pretty']}",
    xaxis_title="Set / File",
    yaxis_title=param_map[first_param]["pretty"],
    width=900, height=600,
    boxmode="group"
)

box_html = DB_FILE.with_name("endurance_boxplots.html")
box_fig.write_html(box_html)
print(f"Boxplots → {box_html}")
box_conn.close()

# ==================================================================
# 6) ENDURANCE – Performance Parameter vs. Cycle Number
# ==================================================================
end_conn = duckdb.connect(str(DB_FILE))

#DataFrame per Set
raw_data = {}
for s in sets:
    raw_data[s] = end_conn.execute(
        "SELECT cycle_number, AV, AI, VSET, ILRS, IHRS "
        "FROM cycles WHERE source_file = ? ORDER BY cycle_number, Time",
        [s]
    ).df()

end_data = []
for s in sets:
    df_s = raw_data[s]

    # max-values per cycle
    classic = (df_s.groupby("cycle_number")
                   .agg(V_set=("VSET", "max"),
                        I_LRS=("ILRS", "last"),
                        I_HRS=("IHRS", "last"),
                        R_LRS=("ILRS", "max"),
                        R_HRS=("IHRS", "max"),
                        I_reset_max=("AI", lambda x: x.abs().max()))
                   .reset_index())

    # V_reset: AV at max|AI|
    vreset_s = (df_s.groupby("cycle_number")[["AV", "AI"]]
                    .apply(lambda g: g.loc[g["AI"].abs().idxmax(), "AV"],
                           include_groups=False)
                    .reset_index(name="V_reset"))

    cycle_df = classic.merge(vreset_s, on="cycle_number")
    cycle_df["source_file"] = s
    cycle_df["Memory_window"] = cycle_df["R_HRS"] / cycle_df["R_LRS"]
    end_data.append(cycle_df)
    
end_df = pd.concat(end_data, ignore_index=True)

#parameter mapping + scaling
param_map = {
    "R_LRS":        {"pretty": "R_LRS (Ω)",        "scale": "log"},
    "R_HRS":        {"pretty": "R_HRS (Ω)",        "scale": "log"},
    "V_set":        {"pretty": "V_set (V)",        "scale": "linear"},
    "V_reset":      {"pretty": "V_reset (V)",      "scale": "linear"},
    "I_reset_max":  {"pretty": "I_reset_max (A)",  "scale": "log"},
    "Memory_window": {"pretty": "Memory Window",   "scale": "log"}
}

#add traces for figure
end_fig = go.Figure()
first_param = "R_LRS"
set_cols = px.colors.sample_colorscale("Viridis", len(sets))

for param, info in param_map.items():
    for s, col in zip(sets, set_cols):
        df = end_df[end_df["source_file"] == s]
        if df.empty:
            continue
        end_fig.add_trace(
            go.Scatter(
                x=df["cycle_number"],
                y=df[param],
                mode="lines+markers",
                name=s,
                line=dict(color=col, width=2),
                marker=dict(size=4),
                visible=(param == first_param),
                meta={"param": param},
                hovertemplate=f"{info['pretty']}: %{{y:.2e}}<br>Cycle: %{{x}}<extra></extra>"
            )
        )

#dropdown
buttons = []
for param, info in param_map.items():
    visible = [tr.meta["param"] == param for tr in end_fig.data]
    yax = dict(type=info["scale"], title=info["pretty"])
    buttons.append(
        dict(label=info["pretty"],
             method="update",
             args=[{"visible": visible},
                   {"yaxis": yax,
                    "xaxis.title.text": "Cycle Number",
                    "title": f"Endurance – {info['pretty']}"}])
    )

#Layout
end_fig.update_layout(
    updatemenus=[dict(buttons=buttons, direction="down", showactive=True,
                      x=1.02, xanchor="left", y=1.15, yanchor="top")],
    title=f"Endurance – {param_map[first_param]['pretty']}",
    xaxis_title="Cycle Number",
    yaxis_title=param_map[first_param]["pretty"],
    width=900, height=600,
    hovermode="x unified"
)

end_html = DB_FILE.with_name("endurance_performance.html")
end_fig.write_html(end_html)
print(f"Endurance → {end_html}")
end_conn.close()

# ==================================================================
# 7) DEVICE-LEVEL CORRELATION SCATTER PLOTS
#     Pairs: I_HRS vs V_set, R_HRS vs V_set, I_LRS vs V_reset,
#            R_LRS vs V_reset, I_reset_max vs V_reset, V_set vs V_reset
# ==================================================================
corr_scatter_conn = duckdb.connect(str(DB_FILE))

scatter_df = (end_df[["source_file", "cycle_number",
                      "V_set", "V_reset", "I_HRS", "I_LRS", "I_reset_max"]]
              .copy())

#good chances that this is redundant, but just to be sure - I struggled with this way too long for no reason
scatter_df["I_HRS"] = scatter_df["I_HRS"]
scatter_df["I_LRS"] = scatter_df["I_LRS"]
scatter_df["R_HRS"] = scatter_df["V_set"] / scatter_df["I_HRS"].abs()
scatter_df["R_LRS"] = scatter_df["V_set"] / scatter_df["I_LRS"].abs()

#select pairs
pairs = [
    ("I_HRS", "V_set", "I_HRS (A) vs V_set (V)"),
    ("R_HRS", "V_set", "R_HRS (Ω) vs V_set (V)"),
    ("I_LRS", "V_reset", "I_LRS (A) vs V_reset (V)"),
    ("R_LRS", "V_reset", "R_LRS (Ω) vs V_reset (V)"),
    ("I_reset_max", "V_reset", "I_reset_max (A) vs V_reset (V)"),
    ("V_set", "V_reset", "V_set (V) vs V_reset (V)")
]

#figure + traces
fig_scatter = go.Figure()
first_pair = pairs[0]
first_set = sets[0]
set_cols = px.colors.sample_colorscale("Viridis", len(sets))
color_map = {s: col for s, col in zip(sets, set_cols)}

for x_col, y_col, title in pairs:
    for s in sets:
        df = scatter_df[scatter_df["source_file"] == s]
        if df.empty:
            continue
        fig_scatter.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="markers",
                marker=dict(color=color_map[s], size=6),
                name=s,
                showlegend=(x_col, y_col) == first_pair,
                visible=((x_col, y_col) == first_pair and s == first_set),
                meta={"set": s, "x": x_col, "y": y_col},
                hovertemplate=f"{x_col}: %{{x:.2e}}<br>{y_col}: %{{y:.2e}}<extra></extra>"
            )
        )

# helper - visibility mask
def vis(set_name, x_y):
    return [tr.meta["set"] == set_name and tr.meta["x"] == x_y[0] and tr.meta["y"] == x_y[1] for tr in fig_scatter.data]

pair_buttons, set_buttons = [], []

# dropdowns + buttons
for x_col, y_col, title in pairs:
    visible = [tr.meta["x"] == x_col and tr.meta["y"] == y_col for tr in fig_scatter.data]
    pair_buttons.append(
        dict(label=title,
             method="update",
             args=[{"visible": visible},
                   {"xaxis.title.text": x_col,
                    "yaxis.title.text": y_col,
                    "title": f"{title} – {first_set}"}])
    )

for s in sets:
    visible = [tr.meta["set"] == s and tr.meta["x"] == fig_scatter.layout.xaxis.title.text for tr in fig_scatter.data]
    set_buttons.append(
        dict(label=s,
             method="update",
             args=[{"visible": visible},
                   {"title": f"{fig_scatter.layout.xaxis.title.text} vs {fig_scatter.layout.yaxis.title.text} - {s}"}])
    )

fig_scatter.update_layout(
    updatemenus=[
        dict(buttons=pair_buttons, direction="down", x=1.02, y=1.15, xanchor="left", yanchor="top"),
        #dict(buttons=set_buttons, direction="down", x=1.02, y=1.05, xanchor="left", yanchor="top")
    ],
    title=f"{first_pair[2]} – {first_set}",
    width=900, height=600
)

#output
html_scatter = DB_FILE.with_name("device_correlation_scatter.html")
fig_scatter.write_html(html_scatter)
print("Device scatter →", html_scatter)
corr_scatter_conn.close()

# ==================================================================
# 8) File Summary
# ==================================================================
#characteristic_plots.html
#endurance_cdf.html
#endurance_boxplots.html
#endurance_performance.html
>>>>>>> 6973844 (improved comments)
