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


def find_device_sets(df: pd.DataFrame, device: str, source_col: str = "source_file") -> list[str]:
    """
    Find all unique sets for a specific device from a DataFrame.

    Tries exact pattern matching first (e.g., "_AI_" or ends with "_AI"),
    falls back to substring matching if no exact matches found.

    Args:
        df: DataFrame containing the source column
        device: Device identifier to search for (e.g., "AI", "NORM_COND")
        source_col: Column name containing set identifiers (default: "source_file")

    Returns:
        List of unique set names matching the device
    """
    all_sources = df[source_col].unique()
    device_pattern = f"_{device}_"
    device_sets = [
        s for s in all_sources
        if device_pattern in s or s.endswith(f"_{device}")
    ]

    if not device_sets:
        device_sets = [s for s in all_sources if device in s]

    return device_sets