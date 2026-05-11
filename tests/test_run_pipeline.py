import tempfile
from pathlib import Path
import shutil
import os

import pytest

# ensure project src is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.etl_pipeline.pipeline import run_pipeline

CATALOG_SAMPLE = '"ID","INV","DATE","CATALOG","PCODE","QTY","custnum"\n1,100.00,1/01/01 00:00:00,"Toys","TY1100",2.0,"1000"\n'
PRODUCTS_SAMPLE = '"ID","TYPE","DESCRIP","PRICE","COST","PCODE","supplier"\n1,"Toy","Test Toy",10.00,5.00,"TY1100","Acme"\n'
WEB_SAMPLE = '"ID","INV","DATE","CATALOG","PCODE","QTY","custnum"\n1;200.00;"TY1100";01/01/2001 00:00:00;"Toys";1.0;"Alice"\n'


def write_sample_files(tmp_raw: Path):
    (tmp_raw / 'Catalog_Orders.txt').write_text(CATALOG_SAMPLE, encoding='utf-8')
    (tmp_raw / 'Products.txt').write_text(PRODUCTS_SAMPLE, encoding='utf-8')
    (tmp_raw / 'Web_Orders.txt').write_text(WEB_SAMPLE, encoding='utf-8')


def test_run_pipeline_creates_outputs(tmp_path):
    tmp_raw = tmp_path / 'raw'
    tmp_processed = tmp_path / 'processed'
    tmp_raw.mkdir()
    tmp_processed.mkdir()

    write_sample_files(tmp_raw)

    # run pipeline
    res = run_pipeline(str(tmp_raw), str(tmp_processed), load_db=False)

    # check outputs exist
    assert (tmp_processed / 'clean_catalog_orders.csv').exists()
    assert (tmp_processed / 'clean_web_orders.csv').exists()
    assert (tmp_processed / 'dim_product.csv').exists()
    assert (tmp_processed / 'dim_customer.csv').exists()
    assert (tmp_processed / 'dim_date.csv').exists()
    assert (tmp_processed / 'fact_sales.csv').exists()

    # simple content checks
    fact = (tmp_processed / 'fact_sales.csv').read_text(encoding='utf-8')
    assert 'TY1100' in fact

