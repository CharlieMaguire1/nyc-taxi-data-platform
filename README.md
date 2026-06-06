## Project Overview

I am building a project called nyc-taxi-data-platform. At the moment, I have only created the repo skeleton. I want the goal of today to be realistic and move from skeleton to a working ingestion stage, and not build the whole platform.

The objective is to build a deterministic batch data pipeline for NYC Yellow Taxi trip data. The pipeline should ingest raw taxi trip data, add provenance metadata, perform cleaning/validation later, and eventually produce outputs that are ready for analytics, such as the daily trip metrics.


## Current Pipeline Stage: Ingestion

The current version of this project implements the first working stage for NYC Yellow Taxi trip data.

The ingestion stage uses one monthly NYC TLC Yellow Taxi parquet file:

- `yellow_tripdata_2023-01.parquet`

The pipeline currently does the following:

1. Downloads or reuses the source parquet file. 
2. Stores the unedited source file in 'data/raw/'.
3. Reads the parquet file into pandas.
4. Adds the provenance metadata:
    - '__source_file'
    - '__ingested_at_utc'
5. Saves the parquet output to 'data/processed', which includes the provenance columns
6. Prints a summary that consists of:
    - row count
    - column count
    - column names
    - basic schema / dtypes

This will keep the raw source file separate from the ingestion output produced by the pipeline, which will support traceability and aid debugging issues.


## Decision Layer

This layer supports the operational analysis of the NYC Yellow Taxi trip activity by creating reliable daily trip and fare metrics from raw trip files. 

The user is an analyst or an operations stakeholder, who needs trustworthy outputs for:

    - trip volume analysis
    - fare and revenue interpretation
    - data qualtiy monitoring
    - anomaly detection

Demand analysis, revenue interpretation, and operational decision making can be misled wrong or unstable data.

Current decision supported:

> Can the raw monthly taxi trip file be ingested in a repeatable and traceable manner before downstream cleaning.

Outputs for analytics will be extended at the later stages, such as daily trip metrics.
