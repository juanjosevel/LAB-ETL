from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any

import pandas as pd
from sqlalchemy import create_engine

from .cleaning import build_channel_dimension, build_customer_dimension, build_date_dimension, build_fact_table, clean_orders, clean_products, summarize_quality
from .config import PipelinePaths
from .io import read_catalog_orders, read_products, read_web_orders


@dataclass
class PipelineResult:
    cleaned_catalog_orders: pd.DataFrame
    cleaned_web_orders: pd.DataFrame
    dim_product: pd.DataFrame
    dim_customer: pd.DataFrame
    dim_channel: pd.DataFrame
    dim_date: pd.DataFrame
    fact_sales: pd.DataFrame
    quality_report: dict[str, Any]


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_dataframe(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)


def _write_quality_report(report: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def _load_dataframe(engine_url: str, table_name: str, frame: pd.DataFrame) -> None:
    engine = create_engine(engine_url)
    frame.to_sql(table_name, engine, if_exists="replace", index=False, method="multi")


def run_pipeline(
    raw_dir: str | Path,
    processed_dir: str | Path,
    *,
    load_db: bool = False,
    database_url: str | None = None,
) -> PipelineResult:
    paths = PipelinePaths(raw_dir=Path(raw_dir), processed_dir=Path(processed_dir))
    _ensure_directory(paths.processed_dir)

    catalog_orders_raw = read_catalog_orders(paths.catalog_orders)
    web_orders_raw = read_web_orders(paths.web_orders)
    products_raw = read_products(paths.products)

    cleaned_catalog_orders, catalog_issues = clean_orders(catalog_orders_raw, "catalog")
    cleaned_web_orders, web_issues = clean_orders(web_orders_raw, "web")
    cleaned_products, product_issues = clean_products(products_raw)

    all_orders = pd.concat([cleaned_catalog_orders, cleaned_web_orders], ignore_index=True)
    dim_channel = build_channel_dimension(all_orders)
    dim_customer = build_customer_dimension(all_orders)
    dim_date = build_date_dimension(all_orders)

    dim_product = cleaned_products.copy()
    dim_product["product_key"] = dim_product.index + 1
    dim_product = dim_product[
        ["product_key", "product_id", "product_code", "product_catalog", "product_type", "product_description", "price", "cost", "supplier"]
    ]

    fact_sales = build_fact_table(all_orders, dim_product, dim_customer, dim_channel)

    report = {
        "catalog": asdict(summarize_quality("catalog", cleaned_catalog_orders)),
        "web": asdict(summarize_quality("web", cleaned_web_orders)),
        "issues": {
            "catalog_rows_with_issues": len(catalog_issues),
            "web_rows_with_issues": len(web_issues),
            "product_rows_with_issues": len(product_issues),
        },
        "summary": {
            "catalog_rows": len(cleaned_catalog_orders),
            "web_rows": len(cleaned_web_orders),
            "products_rows": len(cleaned_products),
            "fact_rows": len(fact_sales),
            "customer_rows": len(dim_customer),
            "date_rows": len(dim_date),
        },
    }

    _write_dataframe(cleaned_catalog_orders, paths.processed_dir / "clean_catalog_orders.csv")
    _write_dataframe(cleaned_web_orders, paths.processed_dir / "clean_web_orders.csv")
    _write_dataframe(dim_product, paths.dim_product)
    _write_dataframe(dim_customer, paths.dim_customer)
    _write_dataframe(dim_channel, paths.processed_dir / "dim_channel.csv")
    _write_dataframe(dim_date, paths.dim_date)
    _write_dataframe(fact_sales, paths.fact_sales)
    _write_quality_report(report, paths.quality_report)

    if load_db:
        if not database_url:
            raise ValueError("database_url is required when load_db=True")
        _load_dataframe(database_url, "dim_product", dim_product)
        _load_dataframe(database_url, "dim_customer", dim_customer)
        _load_dataframe(database_url, "dim_channel", dim_channel)
        _load_dataframe(database_url, "dim_date", dim_date)
        _load_dataframe(database_url, "fact_sales", fact_sales)

    return PipelineResult(
        cleaned_catalog_orders=cleaned_catalog_orders,
        cleaned_web_orders=cleaned_web_orders,
        dim_product=dim_product,
        dim_customer=dim_customer,
        dim_channel=dim_channel,
        dim_date=dim_date,
        fact_sales=fact_sales,
        quality_report=report,
    )
