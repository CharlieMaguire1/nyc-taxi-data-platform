# src/paths.py

from __future__ import annotations

"""
These are the central paths definitions for the NYC Taxi data platform.

This module centralises project directory and file path definitions so that the
ingestion, validation, transformation, and reporting stages use consistent, 
reusable paths instead of embedding directory strings directly inside their
implementation.

Current stage:
- data/raw/ stores the source files downloaded from NYC TLC.
- data/processed/ stores the parquet outputs produced from the pipeline.
- outputs/metrics/ and outputs/figures/ are reserved for the later pipeline stages
"""

from pathlib import Path


# Project root: src/paths.py -> src/ -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
FIGURES_DIR = OUTPUTS_DIR / "figures"


def check_project_dirs() -> None:
    """
    This function creates the standard project directories if they do not exist.
    
    This enables the pipeline to be safe to run from a new repo clone.
    """
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        METRICS_DIR,
        FIGURES_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)