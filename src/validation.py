# src/validation.py

"""
This script is the validation logic for the NYC Taxi data platform.

The current validation scope checks whether the ingested dataset contains the
expected source and provenance columns.

The row-level data quality rules will be added later
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

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
    row_count: int
    expected_columns: list[str]
    actual_columns: list[str]
    missing_columns: list[str]
    unexpected_columns: list[str]
    duplicated_columns: list[str]
    is_empty: bool


def validate_expected_columns(
    data: pd.DataFrame,
) -> ResultOfSchemaValidation:
    """
    This function validates the basic structural contract of the dataset.

    Structural validation fails when:
        - One or more required columns are missing;
        - Duplicate column names are present; or
        - The dataset contains no rows.

    The unexpected rows are recorded but do not currently fail validation.
    """
    actual_columns = [str(column) for column in data.columns]
    actual_column_set = set(actual_columns)

    column_counts = Counter(actual_columns)

    missing_columns = sorted(EXPECTED_COLUMNS - actual_column_set)
    unexpected_columns = sorted(actual_column_set - EXPECTED_COLUMNS)

    duplicate_columns = sorted(
        column
        for column, count in column_counts.items()
        if count > 1
    )

    row_count = len(data)
    is_empty = row_count == 0

    is_valid = (
        not missing_columns
        and not duplicate_columns
        and not is_empty
    )

    return ResultOfSchemaValidation(
        is_valid=is_valid,
        row_count=row_count,
        expected_columns=sorted(EXPECTED_COLUMNS),
        actual_columns=actual_columns,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        duplicated_columns=duplicate_columns,
        is_empty=is_empty,
    )


def print_schema_validation_summary(
    result: ResultOfSchemaValidation,
) -> None:
    """
    This function prints the schema column validation results to the terminal
    """
    print("\nSchema validation")
    print("-----------------")
    print(f"Is valid: {result.is_valid}")
    print(f"Row count: {result.row_count:,}")
    print(f"Dataset is empty: {result.is_empty}")
    print(f"Missing columns: {result.missing_columns}")
    print(f"Unexpected columns: {result.unexpected_columns}")
    print(f"Duplicate columns: {result.duplicated_columns}")
