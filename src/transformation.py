# src/transformation.py

"""
These are deterministic transformations for the NYC Taxi Data Platform.

They transform structurally validated source data into a standardised representation
ready for row-level data quality checks.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd



@dataclass(frozen=True)
class ResultOfTransformation:
    dataframe: pd.DataFrame


def transform_taxi_data(df: pd.DataFrame) -> ResultOfTransformation:
    """
    This function applies Silver layer transformations

    Responsibilities include:
    - ensure canonical datetime representation
    - derive trip_duration_minutes
    - derive trip_date
    - preserve source columns and provenance
    """
    data_silver = df.copy()

    data_silver["tpep_pickup_datetime"] = pd.to_datetime(
        data_silver["tpep_pickup_datetime"]
    )

    data_silver["tpep_dropoff_datetime"] = pd.to_datetime(
        data_silver["tpep_dropoff_datetime"]
    )

    duration_trip = (
        data_silver["tpep_dropoff_datetime"] - data_silver["tpep_pickup_datetime"]
    )

    data_silver["trip_duration_minutes"] = (
        duration_trip.dt.total_seconds() / 60
    )

    data_silver["trip_date"] = data_silver["tpep_pickup_datetime"].dt.date

    return ResultOfTransformation(
        dataframe=data_silver
    )