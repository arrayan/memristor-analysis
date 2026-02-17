import re
from pathlib import Path
from .models import FileMetadata

"""Extracts stack-level metadata from file paths to keep track of origins of measurements.

Expected directory structure:
    <root>/<stack_folder>/<device_folder>/<measurement_type>.xlsx

Stack ID is taken as-is from the stack folder name (e.g. SC20251208#4a, h25096_b1).
Device row/col are parsed from the device folder name (e.g. F11 -> row=F, col=11).
"""


class MetadataExtractor:
    # Pattern to split a device folder name into letters (row) and digits (col)
    DEVICE_FOLDER_PATTERN = re.compile(r"^([A-Za-z]+)(\d+)$", re.IGNORECASE)
    # Pattern for measurement type from filename: "02 reset.xlsx"
    FILENAME_PATTERN = re.compile(r"^(\d{2})\s+(.+)\.xlsx?$", re.IGNORECASE)
    # Normalize measurement types
    TYPE_MAP = {
        "leakage": "leakage",
        "electroforming": "electroforming",
        "reset": "reset",
        "set": "set",
        "endurance reset": "endurance_reset",
        "endurance set": "endurance_set",
        "endurance ratio": "endurance_ratio",
    }

    def extract(self, file_path: Path) -> FileMetadata:
        file_path = Path(file_path).resolve()
        meta = FileMetadata(source_id=file_path.stem, file_path=str(file_path))

        # Extract measurement type from filename
        filename_match = self.FILENAME_PATTERN.match(file_path.name)
        if filename_match:
            raw_type = filename_match.group(2).lower().strip()
            meta.measurement_type = self.TYPE_MAP.get(
                raw_type, raw_type.replace(" ", "_")
            )

        # Derive stack and device info from directory structure
        device_folder = file_path.parent.name
        meta.stack_id = file_path.parent.parent.name
        meta.device_id = f"{meta.stack_id}_{device_folder}"

        # Parse device row/col from device folder name (e.g. F11 -> F, 11)
        folder_match = self.DEVICE_FOLDER_PATTERN.match(device_folder)
        if folder_match:
            meta.device_row = folder_match.group(1).upper()
            meta.device_col = int(folder_match.group(2))

        # Build source_id
        parts = []
        if meta.device_id:
            parts.append(meta.device_id)
        if filename_match:
            parts.append(filename_match.group(1))
        if meta.measurement_type:
            parts.append(meta.measurement_type)

        if parts:
            meta.source_id = "_".join(parts)

        return meta
