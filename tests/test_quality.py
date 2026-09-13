# tests/test_quality.py

import numpy as np
import pandas as pd
import pytest

from src.quality import quality_gate
from src.config import MAX_INVALID_ROW_PCT



# Clean baseline dataframe
def make_valid_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trip_distance": [1.0] * 20,
            "trip_duration_minutes": [10.0] * 20,
            "tpep_pickup_datetime": [pd.Timestamp("2023-01-01 10:00:00")] * 20,
            "tpep_dropoff_datetime": [pd.Timestamp("2023-01-01 10:10:00")] * 20,
            "PULocationID": [100] * 20,
            "DOLocationID": [200] * 20,
            "payment_type": [1] * 20,
            "VendorID": [1] * 20,
            "RatecodeID": [1] * 20,
            "store_and_fwd_flag": ["N"] * 20,
    })


def test_quality_gate_all_rows_valid() -> None:
    data = make_valid_dataframe()

    result = quality_gate(data)

    quality_checked_df = result.clean_dataframe

    assert quality_checked_df.shape[0] == data.shape[0]
    assert result.clean_rows == len(data)
    assert result.quarantined_dataframe.shape[0] == 0
    assert result.passed_quality_threshold is True
    assert result.invalid_row_pct == 0.0


def test_quality_gate_quarantine_negative_distance() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = -1.0

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1  # Checks the metric
    assert quality_checked_df["trip_distance"].iloc[0] < 0
    assert result.failures_by_rule["FAILED_INVALID_DISTANCE"] == 1
    assert result.failures_by_rule["FAILED_INVALID_DURATION"] == 0
    assert quality_checked_df["rejection_reason"].iloc[0] == "FAILED_INVALID_DISTANCE"


def test_quality_gate_quarantine_negative_duration() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_duration_minutes"] = -1.0

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert quality_checked_df["trip_duration_minutes"].iloc[0] < 0
    assert result.failures_by_rule["FAILED_INVALID_DISTANCE"] == 0
    assert result.failures_by_rule["FAILED_INVALID_DURATION"] == 1
    assert quality_checked_df["rejection_reason"].iloc[0] == "FAILED_INVALID_DURATION"


def test_quality_gate_quarantine_missing_distance() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_DISTANCE"] == 1
    assert result.failures_by_rule["FAILED_MISSING_DURATION"] == 0
    assert pd.isna(quality_checked_df["trip_distance"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_DISTANCE"
    )


def test_quality_gate_quarantine_missing_duration() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_duration_minutes"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_DISTANCE"] == 0
    assert result.failures_by_rule["FAILED_MISSING_DURATION"] == 1
    assert pd.isna(quality_checked_df["trip_duration_minutes"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_DURATION"
    )


def test_quality_gate_quarantine_missing_pickup_datetime() -> None:
    data = make_valid_dataframe()
    data.loc[0, "tpep_pickup_datetime"] = pd.NaT

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_PICKUP_DATETIME"] == 1
    assert result.failures_by_rule["FAILED_MISSING_DROPOFF_DATETIME"] == 0
    assert pd.isna(quality_checked_df["tpep_pickup_datetime"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_PICKUP_DATETIME"
    )


def test_quality_gate_quarantine_missing_dropoff_datetime() -> None:
    data = make_valid_dataframe()
    data.loc[0, "tpep_dropoff_datetime"] = pd.NaT

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_PICKUP_DATETIME"] == 0
    assert result.failures_by_rule["FAILED_MISSING_DROPOFF_DATETIME"] == 1
    assert pd.isna(quality_checked_df["tpep_dropoff_datetime"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_DROPOFF_DATETIME"
    )


def test_quality_gate_quarantine_missing_pickup_location() -> None:
    data = make_valid_dataframe()
    data.loc[0, "PULocationID"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_PICKUP_LOCATION"] == 1
    assert result.failures_by_rule["FAILED_MISSING_DROPOFF_LOCATION"] == 0
    assert pd.isna(quality_checked_df["PULocationID"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_PICKUP_LOCATION"
    )


def test_quality_gate_quarantine_missing_dropoff_location() -> None:
    data = make_valid_dataframe()
    data.loc[0, "DOLocationID"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_PICKUP_LOCATION"] == 0
    assert result.failures_by_rule["FAILED_MISSING_DROPOFF_LOCATION"] == 1
    assert pd.isna(quality_checked_df["DOLocationID"].iloc[0])
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_DROPOFF_LOCATION"
    )


def test_quality_gate_quarantine_missing_ratecode_id() -> None:
    data = make_valid_dataframe()
    data.loc[0, "RatecodeID"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_RATECODE_ID"] == 1
    assert result.failures_by_rule["FAILED_INVALID_RATECODE_ID"] == 0
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
         "FAILED_MISSING_RATECODE_ID"
    )


def test_quality_gate_quarantine_missing_store_and_fwd_flag() -> None:
    data = make_valid_dataframe()
    data.loc[0, "store_and_fwd_flag"] = np.nan

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_MISSING_STORE_AND_FWD_FLAG"] == 1
    assert result.failures_by_rule["FAILED_INVALID_STORE_AND_FWD_FLAG"] == 0
    assert (
        quality_checked_df["rejection_reason"].iloc[0] ==
        "FAILED_MISSING_STORE_AND_FWD_FLAG"
    )


def test_quality_gate_handles_multiple_failures_on_same_row() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = -1.0
    data.loc[0, "trip_duration_minutes"] = -1.0

    result = quality_gate(data)

    quality_checked_df = result.quarantined_dataframe

    assert result.quarantined_rows == 1
    assert result.failures_by_rule["FAILED_INVALID_DISTANCE"] == 1
    assert result.failures_by_rule["FAILED_INVALID_DURATION"] == 1
    assert (
        quality_checked_df["rejection_reason"].iloc[0]
        == "FAILED_INVALID_DISTANCE;FAILED_INVALID_DURATION"
    )


def test_quality_gate_calculates_metrics_correctly() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = -1.0

    # 20 rows with 1 invalid row gives an expected invalid rate of 5%
    result = quality_gate(data)

    assert result.total_rows == 20
    assert result.clean_rows == 19
    assert result.quarantined_rows == 1
    assert result.invalid_row_pct == 5.0


def test_quality_gate_passes_threshold_at_limit() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = -1.0

    result = quality_gate(data)

    assert result.invalid_row_pct == MAX_INVALID_ROW_PCT
    assert result.passed_quality_threshold is True


def test_quality_gate_fails_threshold_when_invalid_pct_exceeds_limit() -> None:
    data = make_valid_dataframe()
    data.loc[0, "trip_distance"] = -1.0
    data.loc[1, "trip_distance"] = -1.0

    result = quality_gate(data)

    assert result.invalid_row_pct == 10.0
    assert result.passed_quality_threshold is False


def test_quality_gate_rejects_empty_dataframe() -> None:
    data = pd.DataFrame(columns=[
        "trip_distance",
        "trip_duration_minutes"
    ])

    with pytest.raises(ValueError):
        quality_gate(data)
