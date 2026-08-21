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

The later stages will add the row-level data quality evaluation, quarantine handling,
Silver persistence, outputs ready for analytics, and orchestration.

Detailed implementation logic remains inside src/.
"""

from __future__ import annotations

import logging
import sys

import pandas as pd

from src.ingestion import print_ingestion_summary, run_ingestion
from src.paths import check_project_dirs
from src.transformation import transform_taxi_data
from src.validation import (
    validate_expected_columns,
    print_schema_validation_summary,
    validate_expected_type_families,
    print_type_validation_summary,
)

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

    # NEXT STAGE: To save the curated df_transformed outputs to the silver zone


if __name__ == "__main__":
    main()