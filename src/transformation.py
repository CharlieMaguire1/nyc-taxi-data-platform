# src/transformation.py

"""
These are deterministic transformations for the NYC Taxi Data Platform.

They transform structurally validated source data into a standardised representation
ready for row-level data quality checks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

import pandas as pd


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Column contract
# ----------------------------------------------------------------------

COLUMN_PICKUP: Final[str] = "tpep_pickup_datetime"
COLUMN_DROPOFF: Final[str] = "tpep_dropoff_datetime"
COLUMN_DURATION: Final[str] = "trip_duration_minutes"
COLUMN_DATE: Final[str] = "trip_date"


# ----------------------------------------------------------------------
# Transformation result
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ResultOfTransformation:
    dataframe: pd.DataFrame


# ----------------------------------------------------------------------
# Transformation helpers
# ----------------------------------------------------------------------

def _derive_trip_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function derives deterministic trip-level metrics by using vectorised operations.
    """


    # Datetime casting is intentionally omitted here because upstream
    # type-family contract requires both timestamp columns to be compatible to datetime
    duration_series = df[COLUMN_DROPOFF] - df[COLUMN_PICKUP]

    return df.assign(
        **{
            COLUMN_DURATION: duration_series.dt.total_seconds() / 60,
            COLUMN_DATE: df[COLUMN_PICKUP].dt.normalize(),
        }
    )


# ------------------------------------------------------------------------
# Public transformation interface
# ------------------------------------------------------------------------

def transform_taxi_data(df: pd.DataFrame) -> ResultOfTransformation:
    """
    This function applies Silver-layer transformations

    Responsibilities include:
    - Validating transformation prerequisites
    - Deriving trip_duration_minutes
    - Deriving trip_date
    - Preserving source and provenance columns
    - Providing structured pipeline logging
    """

    required_columns = {
        COLUMN_PICKUP,
        COLUMN_DROPOFF,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise KeyError(
            "Missing required columns for transformation: "
            f"{sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError(
            "Cannot transform an empty dataframe"
        )

    logger.info(
    "Starting Silver transformation on dataframe with %s rows",
    len(df),
)

    df_processed = df.pipe(_derive_trip_metrics)

    logger.info(
    "Completed Silver transformation with %s rows",
    len(df_processed),
)
    return ResultOfTransformation(dataframe=df_processed)