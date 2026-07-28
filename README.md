# NYC Taxi Data Platform

## Project overview

This project is a deterministic batch data pipeline for NYC Yellow Taxi trip data.

The platform is being developed in stages:

1. Ingestion
2. Validation
3. Cleaning and preprocessing
4. Transformation
5. Analytics outputs
6. Orchestration

The current implementation contains a working ingestion stage. Later stages will introduce schema validation, data-quality checks, deterministic cleaning, analytics-ready tables and orchestration.

## Current pipeline stage: ingestion

The current pipeline ingests one monthly NYC TLC Yellow Taxi parquet file:

```text
yellow_tripdata_2023-01.parquet
```

The ingestion stage currently:

- Downloads the source parquet file using a streamed HTTP request.
- Reuses an existing raw file when a non-empty local copy is already available.
- Writes new downloads to a temporary `.part` file before moving them to the final path.
- Removes incomplete temporary downloads left by failed runs.
- Stores the unmodified source file in `data/raw/`.
- Reads the source parquet file into a pandas DataFrame.
- Calculates the source file size and SHA-256 hash.
- Adds four provenance columns:
  - `__source_file`
  - `__source_url`
  - `__ingested_at_utc`
  - `__source_file_sha256`
- Saves the ingested parquet output to `data/processed/`.
- Prints an ingestion summary containing:
  - source URL
  - source and output paths
  - ingestion timestamp
  - source file size
  - SHA-256 hash
  - row count
  - column count
  - column names
  - pandas data types

The raw source file remains separate from the pipeline-produced ingestion output. This supports traceability, reproducibility and debugging.

## Current status

The ingestion stage has been tested successfully for both:

- downloading the source file from NYC TLC
- reusing an existing local source file

The January 2023 source file produced:

- 3,066,766 rows
- 19 original source columns
- 4 added provenance columns
- 23 columns in the ingested output

The fresh download and reused local file produced the same source file size and SHA-256 hash.

Validation, cleaning, transformation, analytics tables and orchestration are not yet implemented.

## Decision layer

The longer-term objective is to produce reliable daily trip and fare metrics from raw monthly taxi files.

Potential users include analysts and operational stakeholders who need trustworthy data for:

- trip-volume analysis
- fare and revenue interpretation
- data-quality monitoring
- anomaly detection

Unreliable or unstable input data can distort demand analysis, revenue interpretation and operational decision-making.

The current ingestion stage supports the first pipeline decision:

> Can a raw monthly taxi trip file be ingested in a repeatable and traceable manner before downstream validation and cleaning?

Later stages will extend the platform with data-quality outputs and analytics-ready tables such as daily trip and fare metrics.

## Repository structure

```text
nyc-taxi-data-platform/
├── .vscode/
├── data/
│   ├── processed/
│   │   └── .gitkeep
│   └── raw/
│       └── .gitkeep
├── outputs/
│   ├── figures/
│   ├── logs/
│   └── metrics/
│       └── .gitkeep
├── sql/
├── src/
│   ├── __init__.py
│   ├── ingestion.py
│   └── paths.py
├── .env.example
├── .gitignore
├── environment.yml
├── README.md
├── requirements.txt
└── run_pipeline.py
```

Generated data files are excluded from Git. `.gitkeep` files preserve the required directory structure.

## Running the current pipeline

Create or activate a Python environment containing:

- Python 3.11
- pandas
- pyarrow
- requests

From the project root, run:

```bash
python run_pipeline.py
```

On the first run, the pipeline downloads the source parquet file. On later runs, it reuses the existing non-empty raw file.

## Work in progress

This repository is actively being developed.

Current stage:

- [x] Project structure
- [x] Single-file batch ingestion
- [x] Streamed source download
- [x] Temporary-file protection for incomplete downloads
- [x] Source file hashing
- [x] Row-level provenance metadata
- [x] Processed parquet output
- [ ] Schema validation
- [ ] Data-quality rules
- [ ] Deterministic cleaning
- [ ] Analytics-ready transformations
- [ ] Daily trip and fare metrics
- [ ] Automated tests
- [ ] Pipeline orchestration