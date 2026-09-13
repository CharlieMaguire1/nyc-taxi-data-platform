# src/models.py

"""
This script is about storing dataclass models for the pipeline stages for NYC Taxi Data
"""

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


# ----------------------------------------------------------------------
# Dataclasses
# ----------------------------------------------------------------------

@dataclass
class ResultOfQuality:
    clean_dataframe: pd.DataFrame
    quarantined_dataframe: pd.DataFrame
    total_rows: int
    clean_rows: int
    quarantined_rows: int
    invalid_row_pct: float
    passed_quality_threshold: bool
    failures_by_rule: dict[str, int]




