# src/quality.py

"""
This script is about the evaluation of row-level business and data quality rules for validated
and transformed Silver data.

Quality rule categories:

1. Range rules:
    - trip_distance >= 0
    - trip_duration_minutes >= 0

2. Completeness rules:
    - required values are not null
    - pickup/dropoff datetimes present
    - pickup/dropoff locations present

3. Domain/Categorical rules:
    - payment_type belongs to an allowed set
    - categorical codes (payment_type etc.) belong to expected domains

4. Temporal rules:
    - dropoff_datetime > pickup_datetime
    - timestamps are logically valid

5. Relationship/consistency rules:
    - related fields agree with each other
    - derived values are consistent with source values

6. Business rules:
    - values makes operational sense
    - impossible or implausible combinations are rejected

7. Duplicate/Uniqueness rules:
    - duplicate rows or duplicate business keys where relevant

8. Threshold/Severity rules
    - invalid row percentage compared with configured limits
    - distinguish warning vs failure where needed
"""

from __future__ import annotations

import logging

import pandas as pd

from .models import ResultOfQuality
from .config import (
    MAX_INVALID_ROW_PCT,
    VALID_PAYMENT_TYPES,
    VALID_RATECODE_IDS,
    VALID_STORE_AND_FWD_FLAGS,
    VALID_VENDOR_IDS,
)

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Public Quality Interface
# ----------------------------------------------------------------------

# Define individual row_level quality rules
def quality_gate(dataframe: pd.DataFrame) -> ResultOfQuality:
    """
    Evaluation of data quality/business rules using configuration values and it
    returns a ResultOfQuality model.
    """
    logger.info("Starting quality gate row-level validation.")

    # Defensive empty check
    if dataframe.empty:
        raise ValueError("Quality gate received an empty DataFrame")

    # Range rules
    invalid_distance = dataframe["trip_distance"] < 0
    invalid_duration = dataframe["trip_duration_minutes"] < 0

    # Completeness rules
    missing_distance = dataframe["trip_distance"].isna()
    missing_duration = dataframe["trip_duration_minutes"].isna()
    missing_pickup_datetime = dataframe["tpep_pickup_datetime"].isna()
    missing_dropoff_datetime = dataframe["tpep_dropoff_datetime"].isna()
    missing_pickup_location = dataframe["PULocationID"].isna()
    missing_dropoff_location = dataframe["DOLocationID"].isna()

    # Domain/Categorical rules
    # - Note: There are no nulls observed in this current batch of payment_type and VendorID
    invalid_payment_type = ~dataframe["payment_type"].isin(VALID_PAYMENT_TYPES)

    invalid_vendor_id = ~dataframe["VendorID"].isin(VALID_VENDOR_IDS)

    missing_ratecode_id = dataframe["RatecodeID"].isna()
    invalid_ratecode_id = (
        dataframe["RatecodeID"].notna() & ~dataframe["RatecodeID"].isin(VALID_RATECODE_IDS)
    )

    missing_store_and_fwd_flag = dataframe["store_and_fwd_flag"].isna()
    invalid_store_and_fwd_flag = (
        dataframe["store_and_fwd_flag"].notna()
        & ~dataframe["store_and_fwd_flag"].isin(VALID_STORE_AND_FWD_FLAGS)
    )

    # Temporal rules
    invalid_dropoff_pickup_time = dataframe["tpep_dropoff_datetime"] < dataframe["tpep_pickup_datetime"]

    # Combine invalid instances for each row
    invalid_row = (
        invalid_distance
        | invalid_duration
        | missing_distance
        | missing_duration
        | missing_pickup_datetime
        | missing_dropoff_datetime
        | missing_pickup_location
        | missing_dropoff_location
        | invalid_payment_type
        | invalid_ratecode_id
        | missing_ratecode_id
        | invalid_vendor_id
        | invalid_store_and_fwd_flag
        | missing_store_and_fwd_flag
        | invalid_dropoff_pickup_time
    )

    # Add rejection reasons
    quality_dataframe = dataframe.copy()
    quality_dataframe["rejection_reason"] = ""

    quality_dataframe.loc[
        invalid_distance,
        "rejection_reason",
    ] += "FAILED_INVALID_DISTANCE;"

    quality_dataframe.loc[
        invalid_duration,
        "rejection_reason",
    ] += "FAILED_INVALID_DURATION;"

    quality_dataframe.loc[
        missing_distance,
        "rejection_reason",
    ] += "FAILED_MISSING_DISTANCE;"

    quality_dataframe.loc[
        missing_duration,
        "rejection_reason",
    ] += "FAILED_MISSING_DURATION;"

    quality_dataframe.loc[
        missing_pickup_datetime,
        "rejection_reason",
    ] += "FAILED_MISSING_PICKUP_DATETIME;"

    quality_dataframe.loc[
        missing_dropoff_datetime,
        "rejection_reason",
    ] += "FAILED_MISSING_DROPOFF_DATETIME;"

    quality_dataframe.loc[
        missing_pickup_location,
        "rejection_reason",
    ] += "FAILED_MISSING_PICKUP_LOCATION;"

    quality_dataframe.loc[
        missing_dropoff_location,
        "rejection_reason",
    ] += "FAILED_MISSING_DROPOFF_LOCATION;"

    quality_dataframe.loc[
        invalid_payment_type,
        "rejection_reason",
    ] += "FAILED_INVALID_PAYMENT_TYPE;"

    quality_dataframe.loc[
        invalid_ratecode_id,
        "rejection_reason",
    ] += "FAILED_INVALID_RATECODE_ID;"

    quality_dataframe.loc[
        invalid_vendor_id,
        "rejection_reason",
    ] += "FAILED_INVALID_VENDOR_ID;"

    quality_dataframe.loc[
        invalid_store_and_fwd_flag,
        "rejection_reason",
    ] += "FAILED_INVALID_STORE_AND_FWD_FLAG;"

    quality_dataframe.loc[
        invalid_dropoff_pickup_time,
        "rejection_reason",
    ] += "FAILED_INVALID_DROPOFF_PICKUP_TIME;"

    quality_dataframe.loc[
        missing_ratecode_id,
        "rejection_reason",
    ] += "FAILED_MISSING_RATECODE_ID;"

    quality_dataframe.loc[
        missing_store_and_fwd_flag,
        "rejection_reason",
    ] += "FAILED_MISSING_STORE_AND_FWD_FLAG;"

    # Remove semicolon at the end
    quality_dataframe["rejection_reason"] = (
        quality_dataframe["rejection_reason"].str.rstrip(";")
    )

    # Split rows into:
    # - clean dataframe and quarantined dataframe split
    clean_dataframe = quality_dataframe[~invalid_row].copy()
    quarantined_dataframe = quality_dataframe[invalid_row].copy()

    # Calculate quality metrics:
    # - total rows
    total_rows = len(dataframe)

    # - clean rows
    clean_rows = len(clean_dataframe)

    # - quarantined rows
    quarantined_rows = len(quarantined_dataframe)

    # - invalid percentage
    invalid_row_pct = (quarantined_rows / total_rows * 100)

    # - passed_quality_threshold
    passed_quality_threshold = invalid_row_pct <= MAX_INVALID_ROW_PCT

    # - failures per rule
    failures_by_rule = {
        "FAILED_INVALID_DISTANCE": int(invalid_distance.sum()),
        "FAILED_INVALID_DURATION": int(invalid_duration.sum()),
        "FAILED_MISSING_DISTANCE": int(missing_distance.sum()),
        "FAILED_MISSING_DURATION": int(missing_duration.sum()),
        "FAILED_MISSING_PICKUP_DATETIME": int(missing_pickup_datetime.sum()),
        "FAILED_MISSING_DROPOFF_DATETIME": int(missing_dropoff_datetime.sum()),
        "FAILED_MISSING_PICKUP_LOCATION": int(missing_pickup_location.sum()),
        "FAILED_MISSING_DROPOFF_LOCATION": int(missing_dropoff_location.sum()),
        "FAILED_INVALID_PAYMENT_TYPE": int(invalid_payment_type.sum()),
        "FAILED_INVALID_RATECODE_ID": int(invalid_ratecode_id.sum()),
        "FAILED_INVALID_VENDOR_ID": int(invalid_vendor_id.sum()),
        "FAILED_INVALID_STORE_AND_FWD_FLAG": int(invalid_store_and_fwd_flag.sum()),
        "FAILED_INVALID_DROPOFF_PICKUP_TIME": int(invalid_dropoff_pickup_time.sum()),
        "FAILED_MISSING_RATECODE_ID": int(missing_ratecode_id.sum()),
        "FAILED_MISSING_STORE_AND_FWD_FLAG": int(missing_store_and_fwd_flag.sum()),
    }

    # Return ResultOfQuality
    return ResultOfQuality(
        clean_dataframe=clean_dataframe,
        quarantined_dataframe=quarantined_dataframe,
        total_rows=total_rows,
        clean_rows=clean_rows,
        quarantined_rows=quarantined_rows,
        invalid_row_pct=invalid_row_pct,
        passed_quality_threshold=passed_quality_threshold,
        failures_by_rule=failures_by_rule,
    )