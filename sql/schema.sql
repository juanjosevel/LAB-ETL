CREATE TABLE IF NOT EXISTS dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT,
    product_code TEXT NOT NULL UNIQUE,
    product_catalog TEXT,
    product_type TEXT,
    product_description TEXT,
    price NUMERIC(12,2),
    cost NUMERIC(12,2),
    supplier TEXT
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer TEXT NOT NULL,
    source TEXT NOT NULL,
    UNIQUE (customer, source)
);

CREATE TABLE IF NOT EXISTS dim_channel (
    channel_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    month_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_row_id BIGINT,
    invoice_id TEXT NOT NULL,
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key BIGINT NOT NULL REFERENCES dim_customer(customer_key),
    product_key BIGINT NOT NULL REFERENCES dim_product(product_key),
    channel_key BIGINT NOT NULL REFERENCES dim_channel(channel_key),
    product_code TEXT,
    catalog TEXT,
    product_catalog TEXT,
    quantity NUMERIC(12,2),
    unit_price NUMERIC(12,2),
    unit_cost NUMERIC(12,2),
    line_amount NUMERIC(14,2),
    line_cost NUMERIC(14,2),
    margin NUMERIC(14,2),
    catalog_match BOOLEAN,
    source TEXT NOT NULL,
    order_date DATE,
    CONSTRAINT fact_sales_invoice_line_uk UNIQUE (source, source_row_id, product_code, invoice_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date_key ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_key ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_key ON fact_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_channel_key ON fact_sales(channel_key);
