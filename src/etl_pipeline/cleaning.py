from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable

import pandas as pd

CATALOG_ALIASES = {
    "GARDENING": "Gardening",
    "GARDENINGS": "Gardening",
    "GARDNING": "Gardening",
    "GARDNIN": "Gardening",
    "PET": "Pets",
    "PETS": "Pets",
    "PEST": "Pets",
    "SPORST": "Sports",
    "SPORT": "Sports",
    "SPORTS": "Sports",
    "TOSY": "Toys",
    "TOTS": "Toys",
    "TOY": "Toys",
    "TOYS": "Toys",
    "SOFTWAR": "Software",
    "SOFTWARS": "Software",
    "SOFTWARE": "Software",
    "SOFTWARES": "Software",
    "COLECTIBLES": "Collectibles",
    "COLLECTIBLE": "Collectibles",
    "COLLECTIBLES": "Collectibles",
    "COLLECTABLES": "Collectibles",
}

PREFIX_TO_CATALOG = {
    "GD": "Gardening",
    "PT": "Pets",
    "SP": "Sports",
    "TY": "Toys",
    "SW": "Software",
    "CC": "Collectibles",
}


@dataclass(frozen=True)
class QualityMetric:
    source: str
    rows: int
    missing_catalogs: int
    missing_product_codes: int
    duplicate_rows: int
    invalid_quantities: int
    invalid_dates: int


def normalize_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def normalize_catalog(value: object, product_code: str | None = None) -> str | None:
    text = normalize_text(value)
    if text is None:
        return PREFIX_TO_CATALOG.get((product_code or "").upper()[:2])

    upper = re.sub(r"\s+", "", text).upper()
    upper = upper.replace("_", "")
    if upper in CATALOG_ALIASES:
        return CATALOG_ALIASES[upper]

    compact = re.sub(r"[^A-Z]", "", upper)
    if compact in CATALOG_ALIASES:
        return CATALOG_ALIASES[compact]

    return PREFIX_TO_CATALOG.get((product_code or "").upper()[:2], text.strip().title())


def normalize_product_code(value: object) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    cleaned = text.upper().replace(" ", "")
    cleaned = cleaned.replace("O", "0")
    cleaned = cleaned.replace("I", "1") if re.fullmatch(r"[A-Z]{2}[0-9OIL]{4}", cleaned) else cleaned
    return cleaned


def parse_order_date(value: object, source: str) -> pd.Timestamp | None:
    text = normalize_text(value)
    if text is None:
        return None

    date_part = text.split()[0]
    parts = date_part.split("/")
    try:
        if source == "catalog" and len(parts) == 3 and len(parts[1]) == 2:
            month, year, day = parts
            year_value = int(year)
            year_value = 1900 + year_value if year_value >= 50 else 2000 + year_value
            return pd.Timestamp(datetime(year_value, int(month), int(day)))
        return pd.to_datetime(text, dayfirst=True, errors="raise")
    except Exception:
        return pd.NaT


def coerce_quantity(value: object) -> float | None:
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def clean_products(products: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = products.copy()
    cleaned["product_id"] = pd.to_numeric(cleaned["product_id"], errors="coerce")
    cleaned["product_code"] = cleaned["product_code"].map(normalize_product_code)
    cleaned["product_type"] = cleaned["product_type"].map(normalize_text).map(lambda value: value.title() if value else value)
    cleaned["product_description"] = cleaned["product_description"].map(normalize_text)
    cleaned["supplier"] = cleaned["supplier"].map(normalize_text)
    cleaned["price"] = pd.to_numeric(cleaned["price"], errors="coerce")
    cleaned["cost"] = pd.to_numeric(cleaned["cost"], errors="coerce")
    cleaned["product_catalog"] = cleaned["product_code"].map(lambda code: PREFIX_TO_CATALOG.get((code or "")[:2]))

    issue_rows = cleaned[
        cleaned[["product_code", "product_type", "product_description", "price", "cost"]].isna().any(axis=1)
    ].copy()

    cleaned = cleaned.drop_duplicates(subset=["product_code"], keep="first")
    return cleaned.reset_index(drop=True), issue_rows.reset_index(drop=True)


def clean_orders(orders: pd.DataFrame, source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = orders.copy()
    cleaned["source"] = source
    cleaned["invoice_id"] = cleaned["invoice_id"].map(normalize_text)
    cleaned["product_code"] = cleaned["product_code_raw"].map(normalize_product_code)
    cleaned["catalog"] = [normalize_catalog(catalog, code) for catalog, code in zip(cleaned["catalog_raw"], cleaned["product_code"], strict=False)]
    cleaned["order_date"] = cleaned["order_date_raw"].map(lambda value: parse_order_date(value, source))
    cleaned["quantity"] = cleaned["quantity_raw"].map(coerce_quantity)
    cleaned["customer"] = cleaned["customer_raw"].map(normalize_text)

    quality_flags = pd.DataFrame(
        {
            "missing_catalog": cleaned["catalog"].isna(),
            "missing_product_code": cleaned["product_code"].isna(),
            "invalid_quantity": cleaned["quantity"].isna(),
            "invalid_date": cleaned["order_date"].isna(),
        }
    )

    issues = cleaned.loc[quality_flags.any(axis=1)].copy()
    cleaned = cleaned.drop(columns=["catalog_raw", "product_code_raw", "order_date_raw", "quantity_raw", "customer_raw"])
    cleaned = cleaned[["id", "invoice_id", "order_date", "catalog", "product_code", "quantity", "customer", "source"]]
    return cleaned.reset_index(drop=True), issues.reset_index(drop=True)


def build_customer_dimension(orders: pd.DataFrame) -> pd.DataFrame:
    customers = orders[["customer", "source"]].dropna().drop_duplicates().sort_values(["source", "customer"])
    customers = customers.reset_index(drop=True)
    customers.insert(0, "customer_key", customers.index + 1)
    return customers


def build_channel_dimension(orders: pd.DataFrame) -> pd.DataFrame:
    channels = orders[["source"]].dropna().drop_duplicates().sort_values(["source"])
    channels = channels.reset_index(drop=True)
    channels.insert(0, "channel_key", channels.index + 1)
    channels = channels.rename(columns={"source": "channel_name"})
    return channels


def build_date_dimension(orders: pd.DataFrame) -> pd.DataFrame:
    date_values = pd.to_datetime(orders["order_date"].dropna().dt.normalize().unique())
    dimension = pd.DataFrame({"full_date": sorted(date_values)})
    dimension["date_key"] = dimension["full_date"].dt.strftime("%Y%m%d").astype(int)
    dimension["year"] = dimension["full_date"].dt.year
    dimension["quarter"] = dimension["full_date"].dt.quarter
    dimension["month"] = dimension["full_date"].dt.month
    dimension["day"] = dimension["full_date"].dt.day
    dimension["day_name"] = dimension["full_date"].dt.day_name()
    dimension["month_name"] = dimension["full_date"].dt.month_name()
    return dimension[["date_key", "full_date", "year", "quarter", "month", "day", "day_name", "month_name"]]


def build_fact_table(
    orders: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    channels: pd.DataFrame,
) -> pd.DataFrame:
    product_dim = products.copy()
    product_dim = product_dim.rename(
        columns={
            "product_type": "product_type",
            "product_description": "product_description",
            "price": "unit_price",
            "cost": "unit_cost",
            "product_code": "product_code",
            "supplier": "supplier",
            "product_catalog": "product_catalog",
        }
    )
    merged = orders.merge(product_dim, on="product_code", how="left", validate="many_to_one")
    merged = merged.merge(customers, on=["customer", "source"], how="left", validate="many_to_one")
    merged = merged.merge(channels, left_on="source", right_on="channel_name", how="left", validate="many_to_one")
    order_dates = pd.to_datetime(merged["order_date"], errors="coerce")
    merged["date_key"] = (
        order_dates.dt.year.astype("Int64") * 10000
        + order_dates.dt.month.astype("Int64") * 100
        + order_dates.dt.day.astype("Int64")
    )
    merged["line_amount"] = merged["quantity"] * merged["unit_price"]
    merged["line_cost"] = merged["quantity"] * merged["unit_cost"]
    merged["margin"] = merged["line_amount"] - merged["line_cost"]
    merged["catalog_match"] = merged["catalog"] == merged["product_catalog"]
    merged["order_date"] = pd.to_datetime(merged["order_date"]).dt.date
    merged = merged.reset_index(drop=True)
    merged["sales_key"] = merged.index + 1
    fact = merged[
        [
            "sales_key",
            "id",
            "invoice_id",
            "date_key",
            "customer_key",
            "product_key",
            "channel_key",
            "product_code",
            "catalog",
            "product_catalog",
            "quantity",
            "unit_price",
            "unit_cost",
            "line_amount",
            "line_cost",
            "margin",
            "catalog_match",
            "source",
            "channel_name",
            "order_date",
        ]
    ].copy()
    return fact


def summarize_quality(source: str, orders: pd.DataFrame) -> QualityMetric:
    return QualityMetric(
        source=source,
        rows=len(orders),
        missing_catalogs=int(orders["catalog"].isna().sum()),
        missing_product_codes=int(orders["product_code"].isna().sum()),
        duplicate_rows=int(orders.duplicated(subset=["invoice_id", "product_code", "order_date", "customer"], keep=False).sum()),
        invalid_quantities=int(orders["quantity"].isna().sum()),
        invalid_dates=int(orders["order_date"].isna().sum()),
    )
