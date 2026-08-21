# tests/test_transformation.py

"""
The script is for testing the deterministic Silver-layer transformations

The tests should be confirmation that the transformation:
- derives trip_duration_minutes correctly
- derives trip_date correctly
- preserves the row count
- preserves the provenance/source columns
- does not mutate the input dataframe
"""

import pandas as pd

from src.transformation import(
    transform_taxi_data,
    COLUMN_PICKUP,
    COLUMN_DROPOFF,
    COLUMN_DURATION,
    COLUMN_DATE,
)

from src.validation import EXPECTED_PROVENANCE_COLUMNS

# 1. Create a small known input dataframe
def make_input_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
           COLUMN_PICKUP: [
               "2023-01-01 08:00:00",
               "2023-01-01 10:00:00",
           ] ,
           COLUMN_DROPOFF: [
               "2023-01-01 08:30:00",
               "2023-01-01 11:15:00",
           ],
           "__source_file": [
               "yellow_tripdate.parquet",
               "yellow_tripdate.parquet",
           ],
           "__source_url": [
               "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet",
               "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet",
           ],
           "__ingested_at_utc": [
               "2026-08-21T10:00:00+00:00",
               "2026-08-21T10:00:00+00:00",
           ],
           "__source_file_sha256": [
               "efg456",
               "efg456",
           ],
        }
    )

# 2. Test that trip_duration_metrics is calculated properly
def test_trip_duration_is_derived_correctly() -> None:
    data = make_input_dataframe()

    result = transform_taxi_data(data)

    transformed_df = result.dataframe

    assert transformed_df[COLUMN_DURATION].tolist() == [30.0, 75.0]

# 3. Test that trip_date is derived from the pickup datetime
def test_trip_date_is_derived_correctly() -> None:
    data = make_input_dataframe()

    result = transform_taxi_data(data)

    transformed_df = result.dataframe

    # Tests should check both the value and the representation that the code promises
    assert transformed_df[COLUMN_DATE].tolist() == [
        pd.Timestamp("2023-01-01"),
        pd.Timestamp("2023-01-01"),
    ]

# 4. Test that the row count is preserved
def test_row_count_preservation() -> None:
    data = make_input_dataframe()

    result = transform_taxi_data(data)

    transformed_df = result.dataframe

    assert len(data) == len(transformed_df)

# 5. Test that the provenance columns are preserved
def test_provenance_columns_are_preserved() -> None:
    data = make_input_dataframe()

    result = transform_taxi_data(data)

    transformed_df = result.dataframe

    assert EXPECTED_PROVENANCE_COLUMNS.issubset(transformed_df.columns)

# 6. Test that the original input dataframe is unchanged
def test_input_dataframe_is_not_mutated() -> None:
    data = make_input_dataframe()

    original_data = data.copy()

    transform_taxi_data(data)

    pd.testing.assert_frame_equal(
        data,
        original_data,
    )


