# run_pipeline.py

from __future__ import annotations

"""
This python file is the pipeline entry point for the NYC Taxi platform.

The current pipeline scope is that this script only runs the ingestion stage

The planned pipeline direction is the following:
1. Ingestion:
    Download/read the NYC Yellow Taxi parquet file and add the provenance metadata.
2. Validation:
    Check the schema, nulls, impossible values, and the row-level data quality rules.
3. Cleaning/Preprocessing:
    Standardise the columns and handle the invalid records deterministically.
4. Transformation:
    Create the tables that are ready for analytics, such as daily trip and fare metrics.
5. Outputs:
    Save the metrics, figures, and load the curated outputs to a database later.
    
This file should stay simple and src/ is where the detailed logic belongs. 
"""

from src.ingestion import print_ingestion_summary, run_ingestion
from src.paths import check_project_dirs


def main() -> None:
    """
    This function runs the current batch pipeline.
    """
    check_project_dirs()
    
    result_of_ingestion = run_ingestion()
    print_ingestion_summary(result_of_ingestion)
    

if __name__ == "__main__":
    main()