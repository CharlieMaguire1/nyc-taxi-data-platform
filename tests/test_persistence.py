# tests/test_persistence.py

import json

import pandas as pd

from src.persistence import save_dataframe, save_metrics_json


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
