# src/persistence.py

"""
This script is about persisting quality stage outputs from memory to local storage.
"""

from pathlib import Path
import json

import pandas as pd


def save_dataframe(dataframe: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Destination hierarchy exists
    dataframe.to_parquet(output_path, engine="pyarrow", index=False)

    return output_path


def save_metrics_json(metrics: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    return output_path