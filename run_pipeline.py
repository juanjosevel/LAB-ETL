from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.etl_pipeline.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ETL pipeline for the laboratory project")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"), help="Directory with source TXT files")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"), help="Directory for generated outputs")
    parser.add_argument("--load-db", action="store_true", help="Load the processed tables into PostgreSQL")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="SQLAlchemy database URL")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(
        args.raw_dir,
        args.processed_dir,
        load_db=args.load_db,
        database_url=args.database_url,
    )
    print("Pipeline ejecutado correctamente")
    print(f"Fact rows: {len(result.fact_sales)}")
    print(f"Quality report: {result.quality_report['summary']}")


if __name__ == "__main__":
    main()
