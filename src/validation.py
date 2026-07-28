# src/validation.py

"""
This script is the validation logic for the NYC Taxi data platform.

The current validation scope checks whether the ingested dataset contains the
expected source and provenance columns.

The row-level data quality runs will be added later
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

EXPECTED_SOURCE_COLUMNS = {
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "store_and_fwd_flag",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "congestion_surcharge",
    "airport_fee",
}

EXPECTED_PROVENANCE_COLUMNS = {
    "__source_file",
    "__source_url",
    "__ingested_at_utc",
    "__source_file_sha256",
}

EXPECTED_COLUMNS = EXPECTED_SOURCE_COLUMNS | EXPECTED_PROVENANCE_COLUMNS

@dataclass(frozen=True)
class ResultOfSchemaValidation:
    is_valid: bool
    expected_columns: list[str]
    actual_columns: list[str]
    missing_columns: list[str]
    unexpected_columns: list[str]


def validate_expected_columns(
    data: pd.DataFrame,
) -> ResultOfSchemaValidation:
    """
    This function checks whether the DataFrame contains the expected pipelines columns.
    """
    actual_columns = {str(column) for column in data.columns}

    missing_columns = sorted(EXPECTED_COLUMNS - actual_columns)
    unexpected_columns = sorted(actual_columns - EXPECTED_COLUMNS)

    return ResultOfSchemaValidation(
        is_valid=not missing_columns,
        expected_columns=sorted(EXPECTED_COLUMNS),
        actual_columns=sorted(actual_columns),
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
    )