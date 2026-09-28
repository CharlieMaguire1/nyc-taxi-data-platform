# NYC Taxi Data Platform

## Project overview

The **NYC Taxi Data Platform** is a deterministic batch data engineering project built around NYC TLC Yellow Taxi trip data.

The project is designed as an end-to-end batch pipeline that progressively moves source data through:

1. Ingestion
2. Structural and type validation
3. Transformation
4. Row-level data-quality validation
5. Accepted and quarantined datasets
6. Local and cloud persistence
7. Snowflake loading
8. dbt modelling
9. Airflow orchestration
10. Monitoring and reconciliation

The current implementation covers the pipeline from **source ingestion through local persistence and S3 persistence**.

Snowflake, dbt and Airflow are the next planned stages.

---

## Current architecture

```text
NYC TLC Parquet
       │
       ▼
┌──────────────────────┐
│      Ingestion       │
│ download / reuse     │
│ provenance metadata  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      Validation      │
│ structural contract  │
│ type-family checks   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Silver Transform    │
│ canonical datetimes  │
│ derived columns      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Row-level Data       │
│ Quality Validation   │
│                      │
│ valid / invalid rows │
└───────┬────────┬─────┘
        │        │
        ▼        ▼
   Accepted   Quarantined
     rows         rows
        │        │
        └───┬────┘
            ▼
┌──────────────────────┐
│     Persistence      │
│ Parquet + JSON       │
│ local filesystem     │
│ S3                   │
└──────────┬───────────┘
           │
           ▼
      Snowflake
        planned
           │
           ▼
          dbt
        planned
           │
           ▼
        Airflow
        planned
```

---

## Source dataset

The current pipeline processes the January 2023 NYC TLC Yellow Taxi parquet dataset:

```text
yellow_tripdata_2023-01.parquet
```

The source contains:

- **3,066,766 rows**
- **19 original source columns**

The ingestion process adds four provenance columns:

- `__source_file`
- `__source_url`
- `__ingested_at_utc`
- `__source_file_sha256`

This produces an ingested dataset containing **23 columns** before later transformation-derived fields are added.

---

## Ingestion

The ingestion stage provides repeatable source acquisition while keeping the original source file separate from pipeline-produced datasets.

It currently:

- Downloads the NYC TLC parquet file using streamed HTTP requests
- Reuses an existing non-empty raw file when available
- Writes downloads to a temporary `.part` file before moving them to the final path
- Removes incomplete temporary downloads left by failed runs
- Stores the unmodified source file under `data/raw/`
- Loads the parquet file into a pandas DataFrame
- Calculates source file size
- Calculates a SHA-256 source-file hash
- Records ingestion provenance at row level
- Produces deterministic metadata for later traceability and debugging

The downloaded and locally reused versions of the January 2023 source file produce the same source-file size and SHA-256 hash.

---

## Validation

Validation is divided into **dataset-level validation** and **row-level data-quality validation**.

### Structural validation

Before transformation, the pipeline verifies the expected dataset contract.

Checks include:

- Required columns
- Missing columns
- Unexpected columns
- Duplicate columns
- Empty datasets
- Dataset row count

The policy is intentionally explicit:

- Missing required columns cause validation failure
- Duplicate columns cause validation failure
- Empty datasets cause validation failure
- Unexpected columns are reported without automatically failing the dataset

Validation results are returned through structured Python objects rather than relying only on printed output.

---

## Type-family validation

The pipeline also validates broad type families for important fields.

Supported checks include:

- datetime
- numeric
- integer
- string

This catches schema drift and incompatible source data before downstream transformations or warehouse loading.

The checks focus on expected semantic type families rather than unnecessarily requiring identical low-level pandas dtypes.

---

## Silver transformation

After dataset-level validation, the pipeline creates a deterministic Silver representation of the source data.

Transformations currently include:

- Canonical pickup datetime
- Canonical drop-off datetime
- `trip_duration_minutes`
- `trip_date`
- Preservation of ingestion provenance

The transformation layer separates source representation from the canonical representation expected by downstream quality checks and analytical models.

---

## Row-level data quality

The pipeline applies explicit business and technical rules to individual trip records.

Current checks include:

### Distance

- Trip distance must not be negative

### Duration

- Trip duration must not be negative

### Required trip fields

Records are checked for required values including:

- pickup datetime
- drop-off datetime
- pickup location
- drop-off location

### Domain validation

Categorical values are checked against expected domains, including:

- `payment_type`
- `RatecodeID`
- `VendorID`
- `store_and_fwd_flag`

### Temporal consistency

- Drop-off time must occur after pickup time

Rows failing one or more rules receive explicit rejection reasons.

This makes failed records inspectable rather than silently deleting or modifying them.

---

## Accepted and quarantined datasets

Data-quality evaluation splits the transformed dataset into two outputs:

```text
Accepted rows
Quarantined rows
```

For the January 2023 source dataset:

| Metric | Result |
|---|---:|
| Total rows | 3,066,766 |
| Accepted rows | 2,995,020 |
| Quarantined rows | 71,746 |
| Invalid row percentage | 2.339% |

The current maximum permitted invalid-row threshold is:

```text
5.0%
```

The January dataset therefore passes the configured pipeline quality threshold.

The dominant failures in this dataset are missing:

- `RatecodeID`
- `store_and_fwd_flag`

These occur in approximately 71,743 rows each.

The pipeline preserves these records in quarantine instead of silently discarding them.

---

## Data-quality metrics

The pipeline generates metrics describing each batch, including:

- Total records
- Accepted records
- Quarantined records
- Invalid-row percentage
- Quality threshold
- Rule-level failure counts
- Pipeline pass/fail status

Metrics are persisted separately from the data so that future orchestration and monitoring layers can consume them.

---

## Persistence

### Local persistence

Pipeline outputs are persisted locally as deterministic artifacts.

Current output categories include:

```text
data/processed/accepted/
data/processed/quarantined/
outputs/metrics/
```

Accepted and quarantined datasets are stored independently so downstream consumers cannot accidentally treat rejected records as production-quality data.

Data outputs use parquet, while pipeline metrics use structured JSON where appropriate.

---

## Amazon S3 persistence

The project also supports persistence to Amazon S3.

The AWS configuration uses environment-driven values rather than embedding infrastructure credentials or deployment-specific settings in source code.

Current configuration includes:

```text
AWS_REGION=eu-west-2
S3_BUCKET=<configured through environment>
```

The default Silver object prefix is:

```text
silver/
```

S3 uploads use `boto3`.

The persistence implementation separates:

- local output creation
- S3 object-key construction
- cloud upload behaviour

This keeps the transformation and quality layers independent of the persistence destination.

The associated AWS environment uses:

- private S3 access
- public-access blocking
- SSE-S3 server-side encryption
- IAM permissions scoped to required S3 operations

---

## Automated tests

The project currently contains **31 pytest tests** covering the implemented pipeline components.

Test coverage includes:

- structural validation
- type-family validation
- transformations
- row-level data-quality rules
- local persistence
- S3 persistence behaviour

Tests primarily use small synthetic DataFrames and mocked external interactions so that pipeline logic can be tested without repeatedly processing the complete 3-million-row source dataset or making unnecessary network calls.

Run the full test suite from the project root:

```bash
python -m pytest
```

---

## Repository structure

The repository has evolved beyond the original ingestion-only implementation.

A simplified view of the current organisation is:

```text
nyc-taxi-data-platform/
│
├── data/
│   ├── raw/
│   └── processed/
│       ├── accepted/
│       └── quarantined/
│
├── outputs/
│   └── metrics/
│
├── sql/
│
├── src/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── validation.py
│   ├── transformation.py
│   ├── quality.py
│   ├── persistence.py
│   └── paths.py
│
├── tests/
│
├── .env.example
├── .gitignore
├── environment.yml
├── requirements.txt
├── README.md
└── run_pipeline.py
```

Generated data files are excluded from Git.

Directory placeholders such as `.gitkeep` are used where required so the repository retains the expected project structure without committing large source or processed datasets.

---

## Environment setup

The project supports Conda and pip-based development environments.

### Conda

```bash
conda env create -f environment.yml
conda activate nyc-taxi-de
```

### pip

Create a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```text
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Core technologies currently include:

- Python 3.11
- pandas
- pyarrow
- requests
- boto3
- pytest

Later stages will extend the stack with Snowflake, dbt and Airflow.

---

## Running the pipeline

From the project root:

```bash
python run_pipeline.py
```

At the implemented stage, the pipeline performs the following logical sequence:

1. Download or reuse the raw NYC TLC parquet file
2. Calculate source metadata and provenance
3. Load the source dataset
4. Validate the dataset structure
5. Validate expected type families
6. Create the canonical Silver representation
7. Apply row-level data-quality rules
8. Split records into accepted and quarantined datasets
9. Calculate batch-level quality metrics
10. Persist accepted records
11. Persist quarantined records
12. Persist quality metrics
13. Upload configured outputs to Amazon S3

---

## Engineering decisions

Several design choices are intentional.

### Raw data is immutable

The original NYC TLC parquet file is preserved independently from pipeline-generated datasets.

This supports:

- reproducibility
- debugging
- lineage
- reprocessing

### Invalid records are quarantined

Rows that fail data-quality rules are not silently dropped.

They are persisted separately with rejection reasons so failures can be investigated and pipeline behaviour can be audited.

### Data quality has a threshold

The pipeline evaluates the percentage of invalid rows rather than assuming that every production source will be perfectly clean.

The current threshold is:

```text
MAX_INVALID_ROW_PCT = 5.0
```

This separates individual record failures from batch-level acceptance.

### Infrastructure configuration is externalised

Environment-specific values such as the S3 bucket and AWS region are supplied through configuration rather than embedded directly in application logic.

### External interactions are testable

Network and cloud interactions are isolated so tests can mock those boundaries while testing deterministic pipeline behaviour independently.

---

## Decision layer

The objective is not simply to move a parquet file between systems.

The platform is intended to produce trustworthy analytical datasets while making data-quality failures visible.

Potential downstream users include analysts and operational stakeholders working with:

- trip-volume analysis
- fare and revenue analysis
- demand patterns
- data-quality monitoring
- anomaly investigation

The pipeline therefore answers progressively stronger questions.

### Dataset contract

> Does the incoming batch satisfy the structural and semantic assumptions required by the pipeline?

### Row-level quality

> Which individual records violate expected trip, temporal, completeness or domain rules?

### Batch quality

> Is the proportion of invalid data within an acceptable operational threshold?

### Traceability

> Can every processed record and batch be traced back to its original source and ingestion event?

Future warehouse and modelling stages will extend this into analytical and reconciliation questions.

---

## Current project status

### Implemented

- Project structure
- Reproducible Python environment
- Streamed NYC TLC source ingestion
- Existing-file reuse
- Temporary download protection
- Source SHA-256 hashing
- Row-level provenance
- Structural validation
- Required-column validation
- Unexpected-column reporting
- Duplicate-column detection
- Empty-dataset detection
- Type-family validation
- Canonical Silver transformation
- Derived trip-duration field
- Derived trip-date field
- Row-level completeness rules
- Row-level domain rules
- Distance validation
- Duration validation
- Temporal validation
- Explicit rejection reasons
- Accepted/quarantined dataset split
- Invalid-row percentage calculation
- Configurable batch-quality threshold
- Local parquet persistence
- JSON metrics persistence
- Amazon S3 persistence
- Automated pytest coverage
- Mocked persistence tests
- End-to-end processing of the January 2023 dataset

### Next

The remaining planned sequence is:

1. **Snowflake**
   - external stage / S3 integration
   - target table design
   - `COPY INTO`
   - load validation
   - source-to-target reconciliation

2. **dbt**
   - staging models
   - dimensional modelling
   - fact and dimension tables
   - tests
   - documentation
   - analytics-ready Gold layer

3. **Airflow**
   - DAG definition
   - dependency management
   - scheduled execution
   - retries and failure handling

4. **Production engineering**
   - reconciliation metrics
   - structured monitoring
   - failure observability
   - operational documentation

---

## Planned target architecture

```text
NYC TLC
   │
   ▼
Python ingestion
   │
   ▼
Validation
   │
   ▼
Silver transformation
   │
   ▼
Row-level quality
   │
   ├──────────────► Quarantine
   │
   ▼
Accepted Silver data
   │
   ▼
Amazon S3
   │
   ▼
Snowflake
   │
   ▼
dbt
   │
   ▼
Analytics-ready facts and dimensions
   │
   ▼
Downstream analytics

Airflow will orchestrate the end-to-end batch workflow.
```

---

## Development philosophy

The project is intentionally being developed stage by stage rather than as a single monolithic pipeline.

Each stage has:

- a defined responsibility
- explicit input/output boundaries
- validation or quality checks
- automated tests
- independently inspectable outputs

The goal is to demonstrate not only that the pipeline can process the NYC Taxi dataset, but that its behaviour is **traceable, deterministic, testable and suitable for extension into a warehouse-oriented data platform**.