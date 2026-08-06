# tests/test_validation.py

import pandas as pd

from src.validation import EXPECTED_COLUMNS, validate_expected_columns


def make_valid_dataframe() -> pd.DataFrame:
    """
    This function creates a minimal non-empty DataFrame with every expected column
    """
    return pd.DataFrame(
        {
            column: [None]
            for column in EXPECTED_COLUMNS
        }
    )

def test_valid_dataset_passes() -> None:
    data = make_valid_dataframe()

    result = validate_expected_columns(data)

    assert result.is_valid is True
    assert result.row_count == 1
    assert result.is_empty is False
    assert result.missing_columns == []
    assert result.unexpected_columns == []
    assert result.duplicate_columns == []


def test_missing_required_column_fails() -> None:
    data = make_valid_dataframe().drop(
        columns=["VendorID"]
    )

    result = validate_expected_columns(data)

    assert result.is_valid is False
    assert result.missing_columns == ["VendorID"]


def test_duplicate_column_fails() -> None:
    columns = list(EXPECTED_COLUMNS) + ["VendorID"]

    data = pd.DataFrame(
        [[None] * len(columns)],
        columns=columns
    )

    result = validate_expected_columns(data)

    assert result.is_valid is False
    assert result.duplicate_columns == ["VendorID"]


def test_empty_dataset_fails() -> None:
    data = pd.DataFrame(columns=sorted(EXPECTED_COLUMNS))

    result = validate_expected_columns(data)

    assert result.is_valid is False
    assert result.row_count == 0
    assert result.is_empty is True


def test_reported_unexpected_column_but_no_fail() -> None:
    data = make_valid_dataframe()
    data["new_upstream_column"] = None

    result = validate_expected_columns(data)

    assert result.is_valid is True
    assert result.unexpected_columns == ["new_upstream_column"]