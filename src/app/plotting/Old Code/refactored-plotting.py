import duckdb
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
'''Change Filepath as needed'''
DB_FILE = Path(
    r"C:\Users\apesc\OneDrive\Dokumente\TU_SEM1\MEMRISTOR\memristor-analysis-MEM-45-ExcelParse\memristor_data.duckdb")

PARAM_CONFIG = {
    "VSET": {"label": "V_set (V)", "scale": "linear"},
    "V_reset": {"label": "V_reset (V)", "scale": "linear"},
    "R_LRS": {"label": "R_LRS (Ω)", "scale": "log"},
    "R_HRS": {"label": "R_HRS (Ω)", "scale": "log"},
    "I_reset_max": {"label": "I_reset_max (A)", "scale": "log"},
    "Memory_window": {"label": "Memory Window", "scale": "log"},
    "V_forming": {"label": "V_forming (V)", "scale": "linear"}
}


class MemristorDataProcessor:
    def __init__(self, db_path):
        self.conn = duckdb.connect(str(db_path))
        self.sets = self._get_sets()
        self.raw_data = {}  # Full IV traces
        self.summary_df = None  # One row per cycle

    def _get_sets(self):
        res = self.conn.execute("SELECT DISTINCT source_file FROM cycles WHERE source_file LIKE '%endurance set'").fetchall()
        return sorted([r[0] for r in res])

    def load_data(self):
        """Loads raw traces and calculates summary metrics for all sets."""
        summary_list = []

        # Get Global Forming Voltage
        v_form = self.conn.execute("SELECT MAX(VFORM) FROM cycles WHERE source_file LIKE '%Electroforming%'").fetchone()[0]

        for s in self.sets:
            df = self.conn.execute("SELECT * FROM cycles WHERE source_file = ? ORDER BY cycle_number, Time", [s]).df()
            self.raw_data[s] = df

            # Calculate metrics per cycle
            # V_reset logic: AV where |AI| is max
            v_reset_df = df.groupby("cycle_number").apply(
                lambda g: g.loc[g["AI"].abs().idxmax(), "AV"], include_groups=False
            ).reset_index(name="V_reset")

            # Aggregate other metrics
            metrics = df.groupby("cycle_number").agg({
                "VSET": "max",
                "ILRS": "max",  # Assuming ILRS column stores resistance/current as needed
                "IHRS": "max",
                "AI": lambda x: x.abs().max()
            }).rename(columns={"VSET": "VSET", "ILRS": "R_LRS", "IHRS": "R_HRS", "AI": "I_reset_max"}).reset_index()

            merged = metrics.merge(v_reset_df, on="cycle_number")
            merged["source_file"] = s
            merged["V_forming"] = v_form
            merged["Memory_window"] = merged["R_HRS"] / merged["R_LRS"]
            summary_list.append(merged)

        self.summary_df = pd.concat(summary_list, ignore_index=True)
        self.conn.close()


class PlotFactory:
    """Utility class to build Plotly figures with consistent styling."""

    @staticmethod
    def create_layout_with_dropdowns(fig, param_buttons, set_buttons=None):
        menus = [dict(buttons=param_buttons, direction="down", x=1.02, y=1.15, xanchor="left", yanchor="top")]
        if set_buttons:
            menus.append(dict(buttons=set_buttons, direction="down", x=1.02, y=1.05, xanchor="left", yanchor="top"))

        fig.update_layout(updatemenus=menus, width=900, height=600, template="plotly_white")

    @staticmethod
    def get_visibility_mask(fig, target_meta: dict):
        """Returns a boolean list for trace visibility based on metadata matches."""
        mask = []
        for tr in fig.data:
            match = all(tr.meta.get(k) == v for k, v in target_meta.items())
            mask.append(match)
        return mask


# --- MAIN PLOTTING FUNCTIONS ---

def plot_characteristic_curves(processor):
    fig = go.Figure()
    sets = processor.sets
    colors = {s: px.colors.sample_colorscale("Viridis", processor.raw_data[s]["cycle_number"].nunique()) for s in sets}

    for y_col in ["AI", "NORM_COND"]:
        for s in sets:
            df = processor.raw_data[s]
            for idx, cyc in enumerate(df["cycle_number"].unique()):
                tiny = df[df["cycle_number"] == cyc]
                fig.add_trace(go.Scatter(
                    x=tiny["AV"], y=tiny[y_col].abs() if y_col == "AI" else tiny[y_col],
                    mode="lines", line=dict(color=colors[s][idx], width=1),
                    visible=False, name=f"Cyc {cyc}", meta={"set": s, "y": y_col}
                ))

    # Initialize first view
    init_mask = PlotFactory.get_visibility_mask(fig, {"set": sets[0], "y": "AI"})
    for i, val in enumerate(init_mask): fig.data[i].visible = val

    # Building buttons would follow a similar pattern as before, but calling PlotFactory
    # ... (Dropdown logic here)
    fig.show()


def plot_endurance(processor):
    fig = go.Figure()
    df_summary = processor.summary_df
    sets = processor.sets
    colors = px.colors.qualitative.Plotly

    for param, config in PARAM_CONFIG.items():
        if param not in df_summary.columns: continue
        for i, s in enumerate(sets):
            subset = df_summary[df_summary["source_file"] == s]
            fig.add_trace(go.Scatter(
                x=subset["cycle_number"], y=subset[param],
                mode="lines+markers", name=s, marker_color=colors[i % len(colors)],
                visible=(param == "R_LRS"), meta={"param": param}
            ))

    # Generic button generator
    buttons = []
    for param, config in PARAM_CONFIG.items():
        if param not in df_summary.columns: continue
        buttons.append(dict(
            label=config["label"], method="update",
            args=[{"visible": PlotFactory.get_visibility_mask(fig, {"param": param})},
                  {"yaxis": {"type": config["scale"], "title": config["label"]}}]
        ))

    PlotFactory.create_layout_with_dropdowns(fig, buttons)
    fig.write_html(DB_FILE.with_name("endurance_performance.html"))

# Work in Progress
# --- EXECUTION ---
if __name__ == "__main__":
    proc = MemristorDataProcessor(DB_FILE)
    proc.load_data()

    plot_endurance(proc)
    # Call other functions...