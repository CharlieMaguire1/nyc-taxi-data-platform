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

The current implementation contains a working ingestion stage and an initial structural validation stage. Later stages will introduce type-family checks, completeness profiling, row-level data quality rules, deterministic cleaning, analytics-ready tables and orchestration.

## Current pipeline stages

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

Structural validation is implemented and covered by automated tests. Further validation remains in progress: cleaning, transformation, analytics tables and orchestration remain planned.

## Decision layer

The longer-term objective is to produce reliable daily trip and fare metrics from raw monthly taxi files.

Potential users include analysts and operational stakeholders who need trustworthy data for:

- trip-volume analysis
- fare and revenue interpretation
- data-quality monitoring
- anomaly detection

Unreliable or unstable input data can distort demand analysis, revenue interpretation and operational decision-making.

The current ingestion and structural validation stages support the first pipeline decision:

> Can a raw monthly taxi trip file be ingested in a repeatable and traceable manner, and does the resulting dataset satisfy the expected structural contract before downstream cleaning and transformation?

Later stages will extend the platform with data-quality outputs and analytics-ready tables such as daily trip and fare metrics.

## Repository structure

```text
nyc-taxi-data-platform/
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
│   ├── paths.py
│   └── validation.py
├── tests/
│   └── test_validation.py
├── .env.example
├── .gitignore
├── environment.yml
├── README.md
├── requirements.txt
└── run_pipeline.py
```

Generated data files are excluded from Git. `.gitkeep` files preserve the required directory structure.

## Current validation stage

The pipeline performs structural validation after ingestion.

The current validation stage checks the following:

- All required source and provenance columns are present
- Unexpected columns are reported
- Duplicate columns are detected
- The dataset contains at least one row
- The dataset row count is recorded

The current validation policy is:

- Required columns that are missing cause validation failure
- Duplicate column names cause validation failure
- Empty datasets cause validation failure
- Unexpected columns are reported without triggering validation failure

The validation result is returned as a structured dataclass and printed as part of the pipeline summary.

Type-family, completeness checks, null profiling and row-level data quality rules remain planned.

## Automated tests

The structural validation logic is covered by five automated pytest tests:

- A valid dataset passes
- A missing required column causes validation failure
- A duplicate column causes validation failure
- An empty dataset causes validation failure
- An unexpected column is reported without causing validation failure

The tests use small synthetic pandas DataFrames so that they run quickly without loading the whole NYC Taxi dataset.

## Running the tests

From the project root, run:

```bash
python -m pytest
```

## Environment setup

The project supports setup through either Conda or pip.

### Conda

Create the environment from `environment.yml`:

```bash
conda env create -f environment.yml
conda activate nyc-taxi-de
```

### pip

Create or activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

The current dependencies are:

- Python 3.11
- pandas
- pyarrow
- requests
- pytest

## Running the current pipeline

From the project root, run:

```bash
python run_pipeline.py
```

On the first run, the pipeline downloads the source parquet file. On later runs, it reuses the existing non-empty raw file.

The current pipeline:

1. downloads or reuses the raw source parquet file
2. calculates source-file metadata and provenance
3. saves the ingested parquet output
4. reloads the ingested dataset
5. performs structural validation
6. prints ingestion and validation summaries

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
- [x] Structural schema validation
- [x] Required-column checks
- [x] Unexpected-column reporting
- [x] Duplicate-column detection
- [x] Empty-dataset detection
- [x] Automated validation tests
- [x] Reproducible Conda and pip environment specifications
- [ ] Type-family validation
- [ ] Completeness and null-profile checks
- [ ] Row-level data-quality rules
- [ ] Deterministic cleaning
- [ ] Analytics-ready transformations
- [ ] Daily trip and fare metrics
- [ ] Pipeline orchestration