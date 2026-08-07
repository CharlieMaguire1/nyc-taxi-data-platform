# src/validation.py

"""
This script is the validation logic for the NYC Taxi data platform.

This module defines structural and type-family validation for ingested data before records
proceed into downstream transformation and row-level data quality checks

Completeness and row-level data-quality rules will be added later.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype, is_string_dtype

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

EXPECTED_TYPE_FAMILIES = {
    # Identifiers/codes
    "VendorID": "numeric",
    "RatecodeID": "numeric",
    "PULocationID": "numeric",
    "DOLocationID": "numeric",
    "payment_type": "numeric",

    # Temporal fields
    "tpep_pickup_datetime": "datetime",
    "tpep_dropoff_datetime": "datetime",

    # Measures
    "passenger_count": "numeric",
    "trip_distance": "numeric",
    "fare_amount": "numeric",
    "extra": "numeric",
    "mta_tax": "numeric",
    "tip_amount": "numeric",
    "tolls_amount": "numeric",
    "improvement_surcharge": "numeric",
    "total_amount": "numeric",
    "congestion_surcharge": "numeric",
    "airport_fee": "numeric",

    # Categorical/text
    "store_and_fwd_flag": "string",

    # Provenance
    "__source_file": "string",
    "__source_url": "string",
    "__ingested_at_utc": "string",
    "__source_file_sha256": "string",
}


@dataclass(frozen=True)
class ResultOfSchemaValidation:
    is_valid: bool
    row_count: int
    expected_columns: list[str]
    actual_columns: list[str]
    missing_columns: list[str]
    unexpected_columns: list[str]
    duplicate_columns: list[str]
    is_empty: bool


@dataclass(frozen=True)
class ResultOfTypeValidation:
    is_valid: bool
    expected_type_families: dict[str, str]
    actual_dtypes: dict[str, str]
    invalid_type_columns: list[str]


def validate_expected_columns(
    data: pd.DataFrame,
) -> ResultOfSchemaValidation:
    """
    This function contains structural validation logic for the NYC Taxi data platform.

    The current validation scope checks whether the ingested dataset:
        - contains all required source and provenance columns,
        - report unexpected columns,
        - contains no duplicate columns,
        - contains at least one row.

    The type, completeness and row-level data quality rules will be added later.
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
        duplicate_columns=duplicate_columns,
        is_empty=is_empty,
    )


def _matches_expected_type_family(
    series: pd.Series,
    expected_family: str,
) -> bool:
    """
    This function checks whether a Pandas series matches the declared type family

    Supported type families
        -"numeric"
        - "datetime"
        - "string"
    """
    if expected_family == "numeric":
        return is_numeric_dtype(series)

    if expected_family == "datetime":
        return is_datetime64_any_dtype(series)

    if expected_family == "string":
        return is_string_dtype(series)

    raise ValueError(
        f"This is an unsupported expected type family: {expected_family}"
    )


def print_schema_validation_summary(
    result: ResultOfSchemaValidation,
) -> None:
    """
    This function prints the validation result to the terminal
    """
    print("\nSchema validation")
    print("-----------------")
    print(f"Is valid: {result.is_valid}")
    print(f"Row count: {result.row_count:,}")
    print(f"Dataset is empty: {result.is_empty}")
    print(f"Missing columns: {result.missing_columns}")
    print(f"Unexpected columns: {result.unexpected_columns}")
    print(f"Duplicate columns: {result.duplicate_columns}")
