from __future__ import annotations
import pandas as pd


def has_valid_data(
    df: pd.DataFrame | None,
    items: list | None = None,
) -> bool:
    """
    Check if DataFrame has data and optionally if a list (sets/devices) is non-empty.

    Returns True if:
    - df is not None AND not empty
    - AND (devices is None OR devices is non-empty)
    """
    if df is None or df.empty:
        return False
    if items is not None and not items:
        return False
    return True


def find_device_sets(
    df: pd.DataFrame,
    device: str,
    source_col: str = "source_file",
    stack_id: str = "",
) -> list[str]:
    """
    Find all unique sets for a specific device from a DataFrame.

    When *stack_id* is provided, uses precise prefix matching
    (``{stack_id}_{device}_``) to avoid false positives when the stack ID
    itself contains underscores.  Falls back to pattern matching otherwise.

    Args:
        df: DataFrame containing the source column
        device: Device identifier to search for (e.g., "B12", "H9")
        source_col: Column name containing set identifiers (default: "source_file")
        stack_id: Known stack identifier for precise prefix matching

    Returns:
        List of unique set names matching the device
    """
    all_sources = df[source_col].unique()

    if stack_id:
        prefix = f"{stack_id}_{device}_"
        device_sets = [s for s in all_sources if s.startswith(prefix)]
        if device_sets:
            return device_sets

    device_pattern = f"_{device}_"
    device_sets = [
        s for s in all_sources if device_pattern in s or s.endswith(f"_{device}")
    ]

    return device_sets


def log_axis_config(vals: list[float]) -> dict:
    """
    Returns Plotly axis kwargs for a log-scale axis.
    Uses dtick=1 so Plotly spaces ticks natively (one per decade),
    and autorange=True so all data including outliers is always visible.

    Usage:
        yaxis_config = dict(type="log", title_text="...", ...)
        yaxis_config.update(log_axis_config(all_y_vals))
        fig.update_yaxes(**yaxis_config)
    """
    return dict(
        autorange=True,
        dtick=1,
        tickformat=".0e",
    )
