# tests/test_persistence.py

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.persistence import save_dataframe, save_metrics_json, upload_local_to_s3


def make_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trip_id": [1, 2, 3],
            "trip_distance": [2.5, 4.1, 1.2]
        }
    )


def test_save_dataframe(tmp_path) -> None:
    dataframe = make_dataframe()
    output_path = tmp_path / "accepted" / "test.parquet"
    returned_path = save_dataframe(dataframe, output_path)

    assert returned_path == output_path
    assert output_path.exists()

    saved_dataframe = pd.read_parquet(output_path)
    pd.testing.assert_frame_equal(saved_dataframe, dataframe)


def test_save_metrics_json(tmp_path) -> None:
    metrics = {
        "total_rows": 100,
        "clean_rows": 95,
        "quarantined_rows": 5,
        "invalid_row_pct": 5.0,
    }
    output_path = tmp_path / "metrics" / "quality_metrics.json"
    returned_path = save_metrics_json(metrics, output_path)

    assert returned_path == output_path
    assert output_path.exists()

    with open(output_path, mode="r", encoding="utf-8") as file:
        loaded_metrics = json.load(file)

    assert loaded_metrics == metrics


def test_upload_local_to_s3_calls_boto3_with_expected_arguments(
    tmp_path: Path,
) -> None:
    local_path = tmp_path / "test.parquet"

    # Create an empty file so the test reaches the AWS upload stage
    local_path.touch()

    # Replace the real boto3 Session so the test never connects to AWS
    with patch("src.persistence.boto3.Session") as mock_session:

        # Fake object returned by boto3.Session(...)
        mock_aws_session = mock_session.return_value

        # Fake s3 client returned by session.client("s3")
        mock_s3_client = mock_aws_session.client.return_value

        # Run the target function
        upload_local_to_s3(
            local_path=local_path,
            bucket="test_bucket",
            object_key="silver/test.parquet"
        )

        # Check that the expected AWS profile was used
        mock_session.assert_called_once_with(
            profile_name="nyc-taxi-dev"
        )

        # Check that an S3 client was requested from the session
        mock_aws_session.client.assert_called_once_with("s3")

        # Check that boto3 received the correct file, bucket and S3 key
        mock_s3_client.upload_file.assert_called_once_with(
            Filename=str(local_path),
            Bucket="test_bucket",
            Key="silver/test.parquet"
        )


def test_upload_local_to_s3_raises_when_local_file_missing(
    tmp_path: Path,
) -> None:
    local_path = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError):
        upload_local_to_s3(
            local_path=local_path,
            bucket="test_bucket",
            object_key="silver/test.parquet"
        )


def test_upload_local_to_s3_propagates_boto3_upload_error(
    tmp_path: Path,
) -> None:
    local_path = tmp_path / "test.parquet"

    # Create an empty file so the test reaches the AWS upload stage
    local_path.touch()

    with patch("src.persistence.boto3.Session") as mock_session:
        mock_s3_client = mock_session.return_value.client.return_value

        mock_s3_client.upload_file.side_effect = RuntimeError(
            "S3 upload failed"
        )

        with pytest.raises(RuntimeError, match="S3 upload failed"):
            upload_local_to_s3(
                local_path=local_path,
                bucket="test_bucket",
                object_key="silver/test.parquet",
            )