# src/ingestion.py

from __future__ import annotations

"""
This is the ingestion stage of the NYC Taxi platform.

This module is responsible for the first stage of batch pipeline execution.

The current responsibilities are to:
1. Locate or download one NYC Yellow Taxi parquet source file.
2. Read the parquet file into a pandas DataFrame.
3. Add the ingestion provenance metadata:
    - __source_file
    - __ingested_at_utc
4. Save a parquet copy of the ingested data with provenance metadata for 
   downstream pipeline stages.
5. Return a small ingestion summary that can be printed by run_pipeline.py.

Please note that this stage does not clean, validate, transform, aggregate, or load
to a database. Those responsibilities belong to the later modules.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from .paths import RAW_DATA_DIR, PROCESSED_DATA_DIR


DEFAULT_TAXI_FILE = "yellow_tripdata_2023-01.parquet"
DEFAULT_TAXI_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
)

PROVENANCE_SOURCE_FILE_COL = "__source_file"
PROVENANCE_INGESTED_AT_COL = "__ingested_at_utc"


@dataclass(frozen = True)
class ResultOfIngestion:
    """
    Produces a structured output from the ingestion stage
    
    This keeps the stage output explicit and easier for inspection in run_pipeline.py
    """
    
    source_path: Path
    output_path: Path
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    
    
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
    
    output_path.parent.mkdir(parents = True, exist_ok = True)
    
    if output_path.exists():
        print(f"The source file exists already: {output_path}")
        return output_path
    
    print(f"Downloading the source file from: {source_url}")
    urlretrieve(source_url, output_path)
    print(f"Downloading the source file to: {output_path}")
    
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


def add_provenance_columns(data: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    """
    This function adds the deterministic ingestion provenance columns.
    
    Provenance makes it possible to trace each row back to the source file used and the UTC
    time the ingestion stage ran
    """
    df = data.copy()
    
    ingested_at_utc = datetime.now(timezone.utc).isoformat()
    
    df[PROVENANCE_SOURCE_FILE_COL] = source_path.name
    df[PROVENANCE_INGESTED_AT_COL] = ingested_at_utc
    
    return df


def save_ingested_data(data: pd.DataFrame, output_path: Path) -> Path:
    """
    This function saves the output parquet file that has provenance columns added to it.
    """
    output_path.parent.mkdir(parents = True, exist_ok = True)
    data.to_parquet(output_path, index = False)
    
    return output_path


def build_ingestion_summary(
    data: pd.DataFrame,
    source_path: Path,
    output_path: Path,
) -> ResultOfIngestion:
    """
    This function is building a small structured summary for logging and inspection
    """
    return ResultOfIngestion(
        source_path = source_path,
        output_path = output_path,
        row_count = len(data),
        column_count = len(data.columns),
        columns = data.columns.to_list(),
        dtypes = {column: str(dtype) for column, dtype in data.dtypes.items()},
    )


def print_ingestion_summary(result: ResultOfIngestion) -> None:
    """
    This function is used to print the key ingestion metadata to the terminal
    """
    print("\nIngestion summary")
    print("-----------------")
    print(f"Source path: {result.source_path}")
    print(f"Output path: {result.output_path}")
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
    source_filename: str = DEFAULT_TAXI_FILE
) -> ResultOfIngestion:
    """
    This function runs the entire ingestion stage
    
    The steps consist of:
    1. Download or reuse the raw source parquet file.
    2. Read the source file.
    3. Add the provenance metadata.
    4. Save the ingested parquet output.
    5. Return an ingestion summary
    """
    source_path = RAW_DATA_DIR / source_filename
    output_path = PROCESSED_DATA_DIR / f"ingested_{source_filename}"
    
    source_path = download_source_file(
        source_url = source_url,
        output_path = source_path
    )
    
    raw_data = read_taxi_parquet(source_path)
    ingested_data = add_provenance_columns(raw_data, source_path)
    save_ingested_data(ingested_data, output_path)
    
    return build_ingestion_summary(
        data = ingested_data,
        source_path = source_path,
        output_path = output_path,
    )