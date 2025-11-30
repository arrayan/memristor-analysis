r"""
Endurance-Dashboard für resistive-Switch-Zellen
Auswertung ausschließlich aus den Set-Tabs (ILRS/IHRS/VSET/IMAX stehen in Zeile 1)

Gegeben:
|Spalte| Beispielwert  | Bedeutung                           |
| -----| --------------| ----------------------------------- |
| ILRS | 2.41e-05 A    | Strom nach Set bei Read-Spannung    |
| IHRS | 3.84e-06 A    | Strom vor Set bei Read-Spannung     |
| VSET | 0.66 V        | Spannung am Set-Punkt (aus Messung) |
| IMAX | 2.18e-05 A    | Max. Strom-Anstieg während Set      |

Berechnet werden sollen:
| Größe         | Formel             | Erklärung                                  |
| ------------- | -------------------| ------------------------------------------ |
| R\_LRS        | R = V_read / ILRS  | Ohmsches Gesetz - V\_read = -0.62 V (fest) |
| R\_HRS        | R = V_read / IHRS  | Ohmsches Gesetz - V\_read = -0.62 V (fest) |
| Memory Window | R_HRS / R_LRS      | Verhältnis - groß = gut speicherbar        |
| V\_set        | = VSET (aus Excel) | Keine Berechnung - direkt übernommen       |
| I\_reset\_max | = IMAX (aus Excel) | Keine Berechnung - direkt übernommen       |

KTEI berechnet automatisch:
| Excel-Formel                                    | Bedeutung                                  |
| ----------------------------------------------- | ------------------------------------------ |
| ILRS = ABS(AT(AI, FINDU(AV,-0.2,LASTPOS(AV))))  | Strom nach Set bei -0.2 V (letzte Messung) |
| IHRS = ABS(AT(AI, FINDD(AV,-0.2,FIRSTPOS(AV)))) | Strom vor Set bei -0.2 V (erste Messung)   |
| VSET = ABS(AT(AV, MAXPOS(ID)))                  | Spannung bei größtem Strom-Anstieg         |
| IMAX = MAX(ID)                                  | Größter Strom-Anstieg während Sweep        |

"""


import pandas as pd
import plotly.graph_objects as go
import re
from plotly.subplots import make_subplots
import plotly.offline as pyo
import numpy as np

# ---------------------------------------------------------
# config

FILE       = "03 endurance set.xls"   # Excel-Datei
V_READ     = -0.62                    # Read-Spannung für Widerstands-Berechnung
HTML_OUT   = "endurance_dashboard_tabs.html"  # Ausgabe-Datei

# ---------------------------------------------------------
# Einlesen

xls      = pd.ExcelFile(FILE, engine='xlrd')
set_tabs = {s: pd.read_excel(xls, s) for s in xls.sheet_names
            if s == "Data" or re.match(r"Cycle\d+", s)}

# ---------------------------------------------------------

def extract_from_first_row(df: pd.DataFrame) -> tuple[float, float, float, float]:
    """Liest ILRS, IHRS, VSET, IMAX aus der ersten Zeile."""
    first = df.iloc[0]
    ilrs  = abs(float(first.get("ILRS", 0)))
    ihrs  = abs(float(first.get("IHRS", 0)))
    vset  = abs(float(first.get("VSET", 0)))
    imax  = abs(float(first.get("IMAX", 0)))
    return ilrs, ihrs, vset, imax

# ---------------------------------------------------------
# 1) Endurance-Zusammenfassung pro Cycle

summary: list[dict] = []

for tab, df in set_tabs.items():
    if tab == "Data":
        cycle = 1
    else:
        m = re.search(r"Cycle(\d+)", tab)
        if not m:
            continue
        cycle = int(m.group(1))

    ilrs, ihrs, vset, imax = extract_from_first_row(df)
    r_lrs = abs(V_READ) / ilrs if ilrs else float("nan")
    r_hrs = abs(V_READ) / ihrs if ihrs else float("nan")
    window = r_hrs / r_lrs if (r_lrs and r_hrs) else float("nan")

    summary.append(
        {
            "Cycle": cycle,
            "V_set [V]": vset,
            "I_reset_max [A]": imax,
            "ILRS [A]": ilrs,
            "IHRS [A]": ihrs,
            "R_LRS [Ω]": r_lrs,
            "R_HRS [Ω]": r_hrs,
            "Memory Window": window,
        }
    )

df_sum = pd.DataFrame(summary).sort_values("Cycle")

# ---------------------------------------------------------
# 2) Characteristic Plots für alle Cycles

iv_traces  = []
gg_traces = []

for tab, df in set_tabs.items():
    if tab == "Data":
        cycle = 1
    else:
        m = re.search(r"Cycle(\d+)", tab)
        if not m:
            continue
        cycle = int(m.group(1))

    df_num = df[pd.to_numeric(df["AV"], errors="coerce").notna()].copy()
    df_num["I_abs"] = df_num["I"].abs()
    df_num["G_S"]   = df_num["I_abs"] / df_num["AV"].abs()
    df_num["NormCond"] = 12900 * df_num["G_S"]

    # I vs V
    iv_traces.append(
        go.Scatter(
            x=df_num["AV"],
            y=df_num["I_abs"],
            mode="lines",
            name=f"Cycle {cycle}",
            hovertemplate="V: %{x:.2f} V<br>I: %{y:.2e} A<extra></extra>",
        )
    )

    # G/G₀ vs V
    gg_traces.append(
        go.Scatter(
            x=df_num["AV"],
            y=df_num["NormCond"],
            mode="lines",
            name=f"Cycle {cycle}",
            hovertemplate="V: %{x:.2f} V<br>G/G₀: %{y:.2e}<extra></extra>",
        )
    )

# ---------------------------------------------------------
# 3) Plots bauen

# 3a) Endurance
fig_end = go.Figure()
endurance_plots = {
    "R_HRS [Ω]": ("log",),
    "R_LRS [Ω]": ("log",),
    "V_set [V]": ("linear",),
    "I_reset_max [A]": ("log",),
    "Memory Window": ("log",),
}
for key, (y_type,) in endurance_plots.items():
    fig_end.add_trace(
        go.Scatter(
            x=df_sum["Cycle"],
            y=df_sum[key],
            mode="lines+markers",
            name=key,
        )
    )
fig_end.update_layout(
    title="Endurance Plots",
    xaxis_title="Cycle Number",
    updatemenus=[
        {
            "buttons": [
                dict(
                    label=key,
                    method="update",
                    args=[{"y": [df_sum[key]], "name": [key]},
                          {"yaxis.type": y_type, "yaxis.title": key}],
                )
                for key, (y_type,) in endurance_plots.items()
            ],
            "direction": "down",
            "showactive": True,
            "x": 1.15,
            "xanchor": "left",
            "y": 1.15,
            "yanchor": "top",
        }
    ],
    template="plotly_white",
)

# 3b) Characteristic
fig_char = go.Figure()
fig_char = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.1,
    subplot_titles=("I vs V", "G/G₀ vs V"),
)
for tr in iv_traces:
    fig_char.add_trace(tr, row=1, col=1)
for tr in gg_traces:
    fig_char.add_trace(tr, row=2, col=1)

fig_char.update_xaxes(title_text="Voltage [V]", row=2, col=1)
fig_char.update_yaxes(title_text="I [A]", type="log", row=1, col=1)
fig_char.update_yaxes(title_text="G/G₀", type="log", row=2, col=1)
fig_char.update_layout(
    title="Characteristic Plots",
    template="plotly_white",
)


# 3c) Device-Level (mittelwertfrei – 1 Wert pro Cycle)
corr_dev: list[dict] = []
for tab, df in set_tabs.items():
    cycle = 1 if tab == "Data" else int(re.search(r"Cycle(\d+)", tab).group(1))
    first = df.iloc[0]
    vset  = abs(float(first.get("VSET", 0)))
    ilrs  = abs(float(first.get("ILRS", 0)))
    ihrs  = abs(float(first.get("IHRS", 0)))
    imax  = abs(float(first.get("IMAX", 0)))
    r_lrs = abs(V_READ) / ilrs if ilrs else float("nan")
    r_hrs = abs(V_READ) / ihrs if ihrs else float("nan")
    # V_reset = V_set (keine Reset-Datei)
    corr_dev.append({
        "Cycle": cycle,
        "I_HRS [A]": ihrs,
        "R_HRS [Ω]": r_hrs,
        "V_set [V]": vset,
        "I_LRS [A]": ilrs,
        "R_LRS [Ω]": r_lrs,
        "I_reset_max [A]": imax,
        "V_reset [V]": vset,
    })
df_corr_dev = pd.DataFrame(corr_dev).sort_values("Cycle")

# Stack-Level (pristine – erste 10 % der Sweep-Punkte)
corr_stack: list[dict] = []
for tab, df in set_tabs.items():
    cycle = 1 if tab == "Data" else int(re.search(r"Cycle(\d+)", tab).group(1))
    df_num = df[pd.to_numeric(df["AV"], errors="coerce").notna()]
    pristine = df_num.iloc[:max(1, len(df_num) // 10)]
    v_form   = abs(float(df_num.iloc[0].get("VSET", 0)))  # Notlage
    i_leak   = pristine["I"].abs().median()
    r_prist  = abs(V_READ) / i_leak if i_leak else float("nan")
    corr_stack.append({
        "Cycle": cycle,
        "V_forming [V]": v_form,
        "I_leakage_pristine [A]": i_leak,
        "R_pristine [Ω]": r_prist,
        "1st V_reset [V]": v_form,
    })
df_corr_stack = pd.DataFrame(corr_stack).sort_values("Cycle")

# 3c) Scatter-Plots bauen
corr_plots = [
    # Device-Level
    ("I_HRS [A]", "V_set [V]", df_corr_dev, "Device"),
    ("R_HRS [Ω]", "V_set [V]", df_corr_dev, "Device"),
    ("I_LRS [A]", "V_reset [V]", df_corr_dev, "Device"),
    ("R_LRS [Ω]", "V_reset [V]", df_corr_dev, "Device"),
    ("I_reset_max [A]", "V_reset [V]", df_corr_dev, "Device"),
    ("V_set [V]", "V_reset [V]", df_corr_dev, "Device"),
    # Stack-Level
    ("V_forming [V]", "1st V_reset [V]", df_corr_stack, "Stack"),
    ("I_leakage_pristine [A]", "V_forming [V]", df_corr_stack, "Stack"),
    ("R_pristine [Ω]", "V_forming [V]", df_corr_stack, "Stack"),
]

fig_corr = go.Figure()
for y_col, x_col, df, level in corr_plots:
    fig_corr.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="markers",
            name=f"{y_col} vs. {x_col} ({level})",
            hovertemplate=f"<b>{level}</b><br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>",
        )
    )

# Dropdown für Correlation
corr_buttons = [
    dict(
        label=f"{y_col} vs. {x_col} ({level})",
        method="update",
        args=[
            {"visible": [i == idx for i in range(len(corr_plots))]},
            {"xaxis.title": x_col, "yaxis.title": y_col, "yaxis.type": "linear"},
        ],
    )
    for idx, (y_col, x_col, df, level) in enumerate(corr_plots)
]

fig_corr.update_layout(
    title="Correlation Plots - gemeinsame Schwankungen",
    xaxis_title="V_set [V]",
    yaxis_title="I_HRS [A]",
    updatemenus=[
        {
            "buttons": corr_buttons,
            "direction": "down",
            "showactive": True,
            "x": 1.15,
            "xanchor": "left",
            "y": 1.15,
            "yanchor": "top",
        }
    ],
    template="plotly_white",
)


# 3d) Cumulative Distribution Functions (CDFs)
# pre-processing function
def cumulative_distribution(values):
    """Berechnet kumulative Verteilung in Prozent."""
    values = np.array(values)
    values = values[~np.isnan(values)]  # NaNs entfernen
    values.sort()
    n = len(values)
    if n == 0:
        return np.array([]), np.array([])
    prob = np.arange(1, n + 1) / n * 100
    return values, prob

# 3d) CDF-Plots bauen
params = ["V_set [V]", "V_reset [V]", "V_forming [V]", "R_HRS [Ω]", "R_LRS [Ω]", "I_reset_max [A]"]
fig_cdf = go.Figure()

for param in params:
    if param in df_sum.columns:
        x_vals, y_vals = cumulative_distribution(df_sum[param].values)
        if len(x_vals) > 0:
            fig_cdf.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines+markers",
                    name=param,
                    hovertemplate=f"{param}<br>Value: %{{x}}<br>Cumulative Probability: %{{y:.2f}}%<extra></extra>",
                )
            )


# Dropdown-Menü für Parameter-Auswahl
valid_params = [p for p in params if p in df_sum.columns]

buttons = [
    dict(
        label=param,
        method="update",
        args=[
            {"visible": [i == idx for i in range(len(valid_params))]},  # ← 4 Elemente
            {"xaxis.title": param, "yaxis.title": "Cumulative Probability (%)"},
        ],
    )
    for idx, param in enumerate(valid_params)
]

fig_cdf.update_layout(
    title="Cumulative Distribution of Key Parameters",
    xaxis_title="Parameter Value",
    yaxis_title="Cumulative Probability (%)",
    updatemenus=[
        {
            "buttons": buttons,
            "direction": "down",
            "showactive": True,
            "x": 1.15,
            "xanchor": "left",
            "y": 1.15,
            "yanchor": "top",
        }
    ],
    template="plotly_white",
)

html_cdf = fig_cdf.to_html(include_plotlyjs=False, div_id="cdf")

"""# Debug-Ausgaben für CDF
print("CDF - Anzahl Traces:", len(fig_cdf.data))
print("CDF - Namen der Traces:", [t.name for t in fig_cdf.data])

print("R_LRS [Ω] - nicht-NaN-Werte:", df_sum["R_LRS [Ω]"].notna().sum())
print("I_reset_max [A] - nicht-NaN-Werte:", df_sum["I_reset_max [A]"].notna().sum())
print("R_LRS [Ω] - Beispielwerte:\n", df_sum["R_LRS [Ω]"].dropna().head())
print("I_reset_max [A] - Beispielwerte:\n", df_sum["I_reset_max [A]"].dropna().head())
"""

# ---------------------------------------------------------
# 4) HTML mit 3 Tabs (Endurance, Characteristic, Correlation)

html_end = fig_end.to_html(include_plotlyjs='cdn', div_id="endurance")
html_char = fig_char.to_html(include_plotlyjs=False, div_id="characteristic")
html_corr = fig_corr.to_html(include_plotlyjs=False, div_id="correlation")
html_cdf = fig_cdf.to_html(include_plotlyjs=False, div_id="cdf")

html_tabs = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Resistive Switch - Full Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body{{font-family:Arial,Helvetica,sans-serif;}}
        .tab{{
            overflow:hidden;
            border:1px solid #ccc;
            background-color:#f1f1f1;
        }}
        .tab button{{
            background-color:inherit;
            float:left;
            border:none;
            outline:none;
            cursor:pointer;
            padding:14px 16px;
            transition:0.3s;
            font-size:17px;
        }}
        .tab button:hover{{background-color:#ddd;}}
        .tab button.active{{background-color:#ccc;}}
        .tabcontent{{
            display:none;
            padding:6px 12px;
            border:1px solid #ccc;
            border-top:none;
        }}
    </style>
</head>
<body>

<h2>Resistive Switch - Full Dashboard</h2>

<div class="tab">
  <button class="tablinks" onclick="openTab(event, 'Endurance')" id="defaultOpen">Endurance</button>
  <button class="tablinks" onclick="openTab(event, 'Characteristic')">Characteristic</button>
  <button class="tablinks" onclick="openTab(event, 'Correlation')">Correlation</button>
  <button class="tablinks" onclick="openTab(event, 'Cumulative')">Cumulative Distribution</button>
</div>

<div id="Endurance" class="tabcontent">
    {html_end}
</div>

<div id="Characteristic" class="tabcontent">
    {html_char}
</div>

<div id="Correlation" class="tabcontent">
    {html_corr}
</div>

<div id="Cumulative" class="tabcontent">
    {html_cdf}
</div>

<script>
function openTab(evt, tabName) {{
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {{
    tabcontent[i].style.display = "none";
  }}
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {{
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }}
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}}
document.getElementById("defaultOpen").click();
</script>

</body>
</html>
"""

# ---------------------------------------------------------
# Ausgabe
with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html_tabs)

print(f"Fertig - Full-Dashboard mit 3 Tabs gespeichert unter {HTML_OUT}")