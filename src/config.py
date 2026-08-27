# src/config.py

"""
This script contains the pipeline settings, thresholds, and external configuration for the NYC Taxi
data pipeline including the following:
- source URL
- data quality threshold
- S3 bucket
- AWS region
"""

from __future__ import annotations

import os
from typing import Final


# ----------------------------------------------------------------------
# Source configuration
# ----------------------------------------------------------------------

SOURCE_URL: Final[str] = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
)

SOURCE_FILENAME: Final[str] = "yellow_tripdata_2023-01.parquet"


# ----------------------------------------------------------------------
# Data quality configuration
# ----------------------------------------------------------------------

MAX_INVALID_ROW_PCT = 5.0


# ----------------------------------------------------------------------
# AWS/ S3 configuration
# ----------------------------------------------------------------------

AWS_REGION: Final[str] = os.getenv("AWS_REGION", "eu-west-2")

S3_BUCKET_NAME: Final[str | None] = os.getenv("NYC_TAXI_S3_BUCKET")

S3_SILVER_PREFIX: Final[str] = "silver"