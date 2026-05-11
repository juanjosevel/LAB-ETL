from __future__ import annotations

from pathlib import Path

import pandas as pd


STANDARD_ORDER_COLUMNS = ["id", "invoice_id", "order_date_raw", "catalog_raw", "product_code_raw", "quantity_raw", "customer_raw"]
PRODUCT_COLUMNS = ["product_id", "product_type", "product_description", "price", "cost", "product_code", "supplier"]


def _read_text_csv(path: Path, *, sep: str, header: int | None = 0, names: list[str] | None = None, skiprows: int | None = None) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep=sep,
        header=header,
        names=names,
        skiprows=skiprows,
        quotechar='"',
        engine="python",
        dtype=str,
        keep_default_na=False,
        na_values=["", "NULL", "null", "None"],
        on_bad_lines="skip",
    )


def read_catalog_orders(path: Path) -> pd.DataFrame:
    frame = _read_text_csv(path, sep=",", header=0)
    frame.columns = [column.strip().lower() for column in frame.columns]
    frame = frame.rename(
        columns={
            "id": "id",
            "inv": "invoice_id",
            "date": "order_date_raw",
            "catalog": "catalog_raw",
            "pcode": "product_code_raw",
            "qty": "quantity_raw",
            "custnum": "customer_raw",
        }
    )
    return frame[STANDARD_ORDER_COLUMNS]


def read_web_orders(path: Path) -> pd.DataFrame:
    frame = _read_text_csv(
        path,
        sep=";",
        header=None,
        names=["id", "invoice_id", "product_code_raw", "order_date_raw", "catalog_raw", "quantity_raw", "customer_raw"],
        skiprows=1,
    )
    return frame[STANDARD_ORDER_COLUMNS]


def read_products(path: Path) -> pd.DataFrame:
    frame = _read_text_csv(path, sep=",", header=0)
    frame.columns = [column.strip().lower() for column in frame.columns]
    frame = frame.rename(
        columns={
            "id": "product_id",
            "type": "product_type",
            "descrip": "product_description",
            "price": "price",
            "cost": "cost",
            "pcode": "product_code",
            "supplier": "supplier",
        }
    )
    return frame[PRODUCT_COLUMNS]
