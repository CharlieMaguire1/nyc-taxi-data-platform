# NYC Taxi Python ETL Pipeline

A deterministic batch data engineering pipeline that ingests NYC TLC Yellow Taxi trip data, validates source records, applies transformations and data-quality rules, and persists accepted and quarantined datasets.

Built with **Python, pandas, PyArrow, pytest, boto3 and Amazon S3**.

## Project overview

This project demonstrates a modular Python ETL workflow with an emphasis on:

- Reproducible batch ingestion
- Source provenance and traceability
- Structural and type-family validation
- Deterministic transformations
- Row-level data-quality checks and quarantine
- Local and Amazon S3 persistence
- Automated testing and failure isolation

The pipeline processes the **January 2023 NYC TLC Yellow Taxi dataset**, containing **3,066,766 records**.

This repository focuses on Python ETL. A separate **NYC Taxi Cloud ELT** project is planned to demonstrate Snowflake, SQL/dbt transformations, warehouse-side data quality and Airflow orchestration.

## Architecture

```text
NYC TLC Yellow Taxi Parquet
            |
            v
    Python ingestion
    - Streamed download
    - Existing-file reuse
    - SHA-256 provenance
            |
            v
    Dataset validation
    - Structural checks
    - Type-family checks
            |
            v
    Silver transformation
    - Canonical datetimes
    - Trip duration
    - Trip date
            |
            v
    Row-level data quality
    - Completeness
    - Domain validation
    - Distance and duration
    - Temporal consistency
            |
       +----+----+
       |         |
       v         v
    Accepted  Quarantined
       |         |
       +----+----+
            |
            v
    Local persistence
    - Parquet datasets
    - JSON quality metrics
            |
            v
    Amazon S3 persistence
    - boto3 upload support
```

## Dataset and provenance

**Source:** `yellow_tripdata_2023-01.parquet`

The original dataset contains 19 columns. Ingestion adds four provenance fields:

| Column | Purpose |
|---|---|
| `__source_file` | Original source filename |
| `__source_url` | Source download location |
| `__ingested_at_utc` | Ingestion timestamp |
| `__source_file_sha256` | Source-file integrity hash |

The original Parquet file is preserved separately under `data/raw/`.

Downloads use streamed HTTP requests and a temporary `.part` file to reduce the risk of leaving incomplete source files. Existing non-empty files can be reused.

## Validation and transformation

### Dataset validation

Before transformation, the pipeline checks:

- Missing and duplicate columns
- Required source and provenance columns
- Unexpected columns
- Empty datasets
- Expected type families, including datetime, numeric, integer and string

Missing required columns, duplicate columns and empty datasets cause validation failure. Unexpected columns are reported without automatically failing the batch.

### Silver transformation

The transformation layer:

- Canonicalises pickup and drop-off timestamps
- Derives `trip_duration_minutes`
- Derives `trip_date`
- Preserves source provenance

### Row-level data quality

The pipeline applies rules covering:

- Required trip timestamps and location identifiers
- Non-negative trip distance and duration
- Valid categorical domains
- Drop-off timestamps occurring after pickup timestamps

Records failing one or more rules are assigned explicit rejection reasons and persisted separately.

The configured maximum invalid-row threshold is **5%**. This threshold controls batch-level quality assessment; it does not automatically make rejected records valid.

## Verified processing results

The January 2023 batch produced:

| Metric | Result |
|---|---:|
| Source records | 3,066,766 |
| Accepted records | 2,995,020 |
| Quarantined records | 71,746 |
| Invalid-row percentage | 2.339% |
| Configured threshold | 5.0% |
| Batch quality result | Passed |

The dominant rejection category consists of **71,743 records** missing `RatecodeID` and `store_and_fwd_flag`.

A further **3 records** have drop-off timestamps earlier than pickup timestamps, producing negative trip durations.

The rejected records remain quarantined. No automatic timestamp correction or relaxation of the acceptance policy has been implemented.

## Persistence and AWS S3

Local pipeline outputs include:

```text
data/
├── raw/
└── processed/
    ├── accepted/
    └── quarantined/

outputs/
└── metrics/
```

Accepted and quarantined records are persisted as Parquet files, while batch-level quality metrics are stored in JSON.

Amazon S3 upload functionality is implemented using `boto3`, with configuration supplied externally rather than hard-coded credentials.

Example configuration:

```env
AWS_REGION=eu-west-2
S3_BUCKET=your-bucket-name
```

The Python ETL implementation uses a default `silver/` object prefix.

**Deployment status:** S3 upload logic is implemented and covered by mocked tests. A successful upload of the full dataset to the live AWS bucket has not yet been verified.

## Repository structure

```text
nyc-taxi-data-platform/
├── data/
│   ├── raw/
│   └── processed/
│       ├── accepted/
│       └── quarantined/
├── outputs/
│   └── metrics/
├── src/
│   ├── ingestion.py
│   ├── validation.py
│   ├── transformation.py
│   ├── quality.py
│   ├── persistence.py
│   └── paths.py
├── tests/
├── .env.example
├── .gitignore
├── environment.yml
├── requirements.txt
├── run_pipeline.py
└── README.md
```

Generated datasets and temporary files are excluded from version control.

## Environment setup

**Requirements:** Python 3.11 and Conda, or a compatible Python virtual environment.

Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate nyc-taxi-de
```

Alternatively, create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
```

On Windows:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Running the pipeline

From the repository root:

```bash
python run_pipeline.py
```

The pipeline ingests the source dataset, performs validation and transformation, applies row-level quality rules, and produces local data and metrics artifacts.

Cloud upload requires appropriate AWS credentials, bucket configuration and IAM permissions.

## Automated tests

The project contains **31 pytest tests** covering:

- Structural and type-family validation
- Transformation logic
- Row-level data-quality rules
- Local persistence
- Mocked Amazon S3 persistence

Run the test suite:

```bash
python -m pytest -q
```

On Windows, if the default pytest temporary directory is inaccessible:

```bash
python -m pytest -q --basetemp=.pytest_temp_repro
```

The full suite has been verified with **31 passing tests** in a freshly reproduced Conda environment.

## Engineering decisions

**Reproducibility:** Dependency versions are pinned, and the Conda environment is defined in `environment.yml`.

**Idempotent source acquisition:** Existing non-empty raw files can be reused, reducing unnecessary downloads.

**Traceability:** Source metadata and SHA-256 hashes support provenance and debugging.

**Explicit data contracts:** Dataset-level validation detects structural problems before transformation.

**Quarantine instead of deletion:** Invalid records are preserved with rejection reasons for investigation.

**Separation of concerns:** Ingestion, validation, transformation, quality assessment and persistence are implemented as distinct modules.

**Testable cloud boundaries:** AWS interactions can be mocked without requiring live cloud resources during unit testing.

## Project status

**Implemented and verified:** Python ingestion, validation, Silver transformation, data-quality checks, quarantine, local persistence, environment reproducibility and 31 automated tests.

**Implemented but awaiting live verification:** Amazon S3 upload of pipeline outputs.

**Out of scope for this repository:** Snowflake warehouse loading, dbt transformations, warehouse-side quarantine and Airflow orchestration. These are planned for the separate NYC Taxi Cloud ELT project.

---

**Project focus:** Demonstrating reliable, testable Python batch ETL with explicit data-quality controls and traceable outputs.