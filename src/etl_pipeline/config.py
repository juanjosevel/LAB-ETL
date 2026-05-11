from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelinePaths:
    raw_dir: Path
    processed_dir: Path

    @property
    def catalog_orders(self) -> Path:
        return self.raw_dir / "Catalog_Orders.txt"

    @property
    def web_orders(self) -> Path:
        return self.raw_dir / "Web_Orders.txt"

    @property
    def products(self) -> Path:
        return self.raw_dir / "Products.txt"

    @property
    def dim_product(self) -> Path:
        return self.processed_dir / "dim_product.csv"

    @property
    def dim_customer(self) -> Path:
        return self.processed_dir / "dim_customer.csv"

    @property
    def dim_date(self) -> Path:
        return self.processed_dir / "dim_date.csv"

    @property
    def fact_sales(self) -> Path:
        return self.processed_dir / "fact_sales.csv"

    @property
    def quality_report(self) -> Path:
        return self.processed_dir / "data_quality_report.json"
