# src/ingestion.py

"""
This is the ingestion stage of the NYC Taxi platform.

This module is responsible for the first stage of batch pipeline execution.

The current responsibilities are to:
1. Locate or download one NYC Yellow Taxi parquet source file.
2. Read the parquet file into a pandas DataFrame.
3. Add the ingestion provenance metadata:
    - __source_file
    - __source_url
    - __ingested_at_utc
    - __source_file_sha256
4. Save a parquet copy of the ingested data with provenance metadata for
   downstream pipeline stages.
5. Return a small ingestion summary that can be printed by run_pipeline.py.

Please note that this stage does not clean, validate, transform, aggregate, or load
to a database. Those responsibilities belong to the later modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import requests

import pandas as pd

from .paths import RAW_DATA_DIR, PROCESSED_DATA_DIR


DEFAULT_TAXI_FILE = "yellow_tripdata_2023-01.parquet"
DEFAULT_TAXI_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
)

PROVENANCE_SOURCE_FILE_COL = "__source_file"
PROVENANCE_SOURCE_URL_COL = "__source_url"
PROVENANCE_INGESTED_AT_COL = "__ingested_at_utc"
PROVENANCE_SOURCE_FILE_HASH_COL = "__source_file_sha256"


@dataclass(frozen=True)
class ResultOfIngestion:
    """
    Produces a structured output from the ingestion stage

    This keeps the stage output explicit and easier for inspection in run_pipeline.py
    """

    source_url: str
    source_path: Path
    output_path: Path
    ingested_at_utc: str
    source_file_size_bytes: int
    source_file_sha256: str
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]


def calculate_sha256(file_path: Path) -> str:
    """
    This function calculates the SHA-256 hash of a file.

    This helps to verify whether the raw source file has changed between pipeline runs.
    """
    sha256_hash = hashlib.sha256()

    with file_path.open("rb") as file:
        for byte_block in iter(lambda: file.read(1024 * 1024), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_source_file(
    source_url: str = DEFAULT_TAXI_URL,
    output_path: Path | None = None,
) -> Path:
    """
    This function downloads the source parquet file if it does not exist locally already

    Args:
        source_url (str, optional): URL for the NYC TLC parquet file. Defaults to DEFAULT_TAXI_URL.
        output_path (Path | None, optional): Local path where the raw parquet file is stored.

    Returns:
        Path: This is the local path to the source parquet file
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / DEFAULT_TAXI_FILE

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"The source file exists already: {output_path}")
        return output_path

    # Removing an incomplete temporary download from an earlier failed run
    if output_path.exists():
        output_path.unlink()

    temporary_path = output_path.with_suffix(
        f"{output_path.suffix}.part"
    )

    # Removing an incomplete temporary download from an earlier failed run
    temporary_path.unlink(missing_ok=True)

    print(f"Downloading the source file from: {source_url}")

    try:
        with requests.get(
            source_url,
            stream=True,
            timeout=60,
        ) as response:
            response.raise_for_status()

            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

        if not temporary_path.exists() or temporary_path.stat().st_size == 0:
            raise RuntimeError(
                "The download is completed but it produced an empty file"
            )

        temporary_path.replace(output_path)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    print(f"Downloaded the source file to: {output_path}")

    return output_path


def read_taxi_parquet(source_path: Path) -> pd.DataFrame:
    """
    This function reads the Taxi parquet file into a pandas DataFrame

    Args:
        source_path (Path): The same as the output path in download_source_file()

    Returns:
        pd.DataFrame: To be able to view and manipulate the data
    """
    if not source_path.exists():
        raise FileNotFoundError(f"The source parquet file is not found: {source_path}")

    return pd.read_parquet(source_path)


def add_provenance_columns(
    data: pd.DataFrame,
    source_path: Path,
    source_url: str,
    ingested_at_utc: str,
    source_file_sha256: str,
) -> pd.DataFrame:
    """
    This function adds the deterministic ingestion provenance columns.

    Provenance makes it possible to trace each row back to the source file,
    source URL, ingestion time and source file hash.
    """
    df = data.copy()

    df[PROVENANCE_SOURCE_FILE_COL] = source_path.name
    df[PROVENANCE_SOURCE_URL_COL] = source_url
    df[PROVENANCE_INGESTED_AT_COL] = ingested_at_utc
    df[PROVENANCE_SOURCE_FILE_HASH_COL] = source_file_sha256

    return df


def save_ingested_data(data: pd.DataFrame, output_path: Path) -> Path:
    """
    This function saves the output parquet file that has provenance columns added to it.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(output_path, index=False)

    return output_path


def build_ingestion_summary(
    data: pd.DataFrame,
    source_url: str,
    source_path: Path,
    output_path: Path,
    ingested_at_utc: str,
    source_file_size_bytes: int,
    source_file_sha256: str,
) -> ResultOfIngestion:
    """
    This function is building a small structured summary for logging and inspection
    """
    return ResultOfIngestion(
        source_url=source_url,
        source_path=source_path,
        output_path=output_path,
        ingested_at_utc=ingested_at_utc,
        source_file_size_bytes=source_file_size_bytes,
        source_file_sha256=source_file_sha256,
        row_count=len(data),
        column_count=len(data.columns),
        columns=[str(column) for column in data.columns],
        dtypes={
            str(column): str(dtype)
            for column, dtype in data.dtypes.items()
        },
    )


def print_ingestion_summary(result: ResultOfIngestion) -> None:
    """
    This function is used to print the key ingestion metadata to the terminal
    """
    print("\nIngestion summary")
    print("-----------------")
    print(f"Source URL: {result.source_url}")
    print(f"Source path: {result.source_path}")
    print(f"Output path: {result.output_path}")
    print(f"Ingested at UTC: {result.ingested_at_utc}")
    print(f"Source file size: {result.source_file_size_bytes:,} bytes")
    print(f"Source SHA-256: {result.source_file_sha256}")
    print(f"Rows: {result.row_count:,}")
    print(f"Columns: {result.column_count:,}")

    print("\nColumn names:")
    for column in result.columns:
        print(f"- {column}")

    print("\nSchema / dtypes:")
    for column, dtype in result.dtypes.items():
        print(f"- {column}: {dtype}")


def run_ingestion(
    source_url: str = DEFAULT_TAXI_URL,
    source_filename: str = DEFAULT_TAXI_FILE,
) -> ResultOfIngestion:
    """
    This function runs the entire ingestion stage

    The steps consist of:
    1. Download or reuse the raw source parquet file.
    2. Calculate source file metadata.
    3. Read the source file.
    4. Add the provenance metadata.
    5. Save the ingested parquet output.
    6. Return an ingestion summary
    """
    source_path = RAW_DATA_DIR / source_filename
    output_path = (
        PROCESSED_DATA_DIR / f"ingested_{source_filename}"
    )

    source_path = download_source_file(
        source_url=source_url,
        output_path=source_path,
    )

    ingested_at_utc = datetime.now(timezone.utc).isoformat()
    source_file_size_bytes = source_path.stat().st_size
    source_file_sha256 = calculate_sha256(source_path)

    raw_data = read_taxi_parquet(source_path)

    ingested_data = add_provenance_columns(
        data=raw_data,
        source_path=source_path,
        source_url=source_url,
        ingested_at_utc=ingested_at_utc,
        source_file_sha256=source_file_sha256,
    )

    save_ingested_data(
        data=ingested_data,
        output_path=output_path,
    )

    return build_ingestion_summary(
        data = ingested_data,
        source_url=source_url,
        source_path = source_path,
        output_path = output_path,
        ingested_at_utc=ingested_at_utc,
        source_file_size_bytes=source_file_size_bytes,
        source_file_sha256=source_file_sha256,
    )