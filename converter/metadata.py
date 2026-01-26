##Assuming the directory structure doesnt change!
import re
from pathlib import Path
from .models import FileMetadata

"""Extracts stack-level metadata from file paths to keep track of origins of measurements"""


class MetadataExtractor:
    # Pattern for device ID: H16249_A4, H16252L_J1
    DEVICE_PATTERN = re.compile(r"([A-Z]\d{4,6}[A-Z]?)_([A-N])(\d{1,2})", re.IGNORECASE)
    # Pattern for measurement type from filename: "02 reset.xlsx" pre alphabet string is irrelevant!
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
        filename_match = self.FILENAME_PATTERN.match(file_path.name)
        if filename_match:
            raw_type = filename_match.group(2).lower().strip()
            meta.measurement_type = self.TYPE_MAP.get(
                raw_type, raw_type.replace(" ", "_")
            )

        # Look for device info in path
        device_match = self.DEVICE_PATTERN.search(str(file_path))
        if device_match:
            meta.stack_id = device_match.group(1)
            meta.device_row = device_match.group(2).upper()
            meta.device_col = int(device_match.group(3))
            meta.device_id = f"{meta.stack_id}_{meta.device_row}{meta.device_col}"

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
