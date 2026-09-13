# run_pipeline.py

"""
This python file is the pipeline entry point for the NYC Taxi platform.

The current batch pipeline executes the following stages:

1. Ingestion:
    Download or reuse the NYC Yellow Taxi parquet file and add the provenance metadata.
2. Structural validation:
    Verify required columns, duplicate columns, unexpected columns, and non-empty inputs.
3. Type-family validation:
    Verify that the expected columns belong to the required pandas dtype families.
4. Silver transformation:
    Derive trip_duration_minutes and trip_date while preserving source and provenance data.
5. Row-level data quality:
    Apply business quality rules and separate accepted and quarantined rows.
6. Local persistence:
    Persist accepted and quarantined datasets as Parquet and quality metrics as JSON

The later stages will include S3, Snowflake, dbt, Airflow, etc.

Detailed implementation logic remains inside src/.
"""

from __future__ import annotations

import logging
import sys

import pandas as pd

from src.ingestion import print_ingestion_summary, run_ingestion
from src.paths import (
    check_project_dirs,
    METRICS_DIR,
    ACCEPTED_DATA_DIR,
    QUARANTINE_DATA_DIR,
)
from src.transformation import transform_taxi_data
from src.validation import (
    validate_expected_columns,
    print_schema_validation_summary,
    validate_expected_type_families,
    print_type_validation_summary,
)
from src.quality import quality_gate
from src.persistence import save_dataframe, save_metrics_json


# Configuration of basic logging format for visibility in the console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """
    This function orchestrates the batch pipeline execution sequentially across layers.
    """
    # Setup directories
    check_project_dirs()

    # 1. Ingestion layer
    result_of_ingestion = run_ingestion()
    print_ingestion_summary(result_of_ingestion)

    # Loading data for downstream processing
    ingested_data = pd.read_parquet(result_of_ingestion.output_path)

    # 2. Structural validation layer
    result_of_validation = validate_expected_columns(data=ingested_data)
    print_schema_validation_summary(result_of_validation)

    # Guard: Stop the pipeline if the schema is compromised
    if not result_of_validation.is_valid:
        logger.error("Pipeline aborted: Ingested data failed structural validation checks.")
        sys.exit(1)

    # 3. Type-family validation
    result_of_type_family_validation = validate_expected_type_families(data=ingested_data)
    print_type_validation_summary(result_of_type_family_validation)

    # Guard: Stop the pipeline if the expected type family validation failed
    if not result_of_type_family_validation.is_valid:
        logger.error("Pipeline aborted: Ingested data failed type-family validation checks")
        sys.exit(1)

    # 4. Transformation layer (Silver engine)
    logger.info("Proceeding to Silver layer transformations....")
    result_of_transformation = transform_taxi_data(data=ingested_data)

    # Tracing the output shape after transformation
    df_transformed = result_of_transformation.dataframe
    logger.info(
        f"Transformation successful. Final shape: {df_transformed.shape}. "
        f"New metrics generated: ['trip_duration_minutes', 'trip_date']"
    )

    # 5. Data Quality layer
    logger.info("Proceeding to Data Quality Check layer....")
    result_of_quality = quality_gate(dataframe=df_transformed)

    quality_checked_clean_df = result_of_quality.clean_dataframe
    quality_checked_quarantined_df = result_of_quality.quarantined_dataframe

    # 6. Persistence layer
    logger.info("Proceeding to Persistence layer....")

    source_filename = result_of_ingestion.output_path.name
    accepted_output_path = ACCEPTED_DATA_DIR / source_filename
    quarantined_output_path = QUARANTINE_DATA_DIR / source_filename

    source_stem = result_of_ingestion.output_path.stem
    metrics_output_path = METRICS_DIR / f"{source_stem}_quality.json"

    quality_metrics = {
        "total_rows": result_of_quality.total_rows,
        "clean_rows": result_of_quality.clean_rows,
        "quarantined_rows": result_of_quality.quarantined_rows,
        "invalid_row_pct": result_of_quality.invalid_row_pct,
        "passed_quality_threshold": result_of_quality.passed_quality_threshold,
        "failures_by_rule": result_of_quality.failures_by_rule,
    }

    save_dataframe(
        dataframe=quality_checked_clean_df,
        output_path=accepted_output_path,
    )

    save_dataframe(
        dataframe=quality_checked_quarantined_df,
        output_path=quarantined_output_path,
    )

    save_metrics_json(
        metrics=quality_metrics,
        output_path=metrics_output_path
    )

    if not result_of_quality.passed_quality_threshold:
        logger.error(
            f"Pipeline failed quality threshold:"
            f"{result_of_quality.invalid_row_pct:.2f}% invalid rows"
        )
        sys.exit(1)

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()