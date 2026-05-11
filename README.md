# Laboratorio 3 - Pipeline ETL

Implementacion en Python y Pandas para el laboratorio de ETL.

## Que incluye

- Lectura de `Catalog_Orders.txt`, `Web_Orders.txt` y `Products.txt`.
- Limpieza de errores comunes en fechas, codigos de producto, catalogos y valores nulos.
- Integracion en un modelo tipo estrella con tabla de hechos y dimensiones.
- Generacion de archivos limpios en `data/processed/`.
- Carga opcional a PostgreSQL mediante SQLAlchemy.

## Estructura

- `run_pipeline.py`: ejecuta el pipeline completo.
- `src/etl_pipeline/`: logica de lectura, limpieza y carga.
- `sql/schema.sql`: esquema relacional para PostgreSQL.
- `data/raw/`: ubicacion esperada de los archivos fuente.
- `data/processed/`: salidas del pipeline.

## Uso rapido

1. Copia los archivos fuente a `data/raw/` con estos nombres:
   - `Catalog_Orders.txt`
   - `Web_Orders.txt`
   - `Products.txt`
2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecuta el pipeline:

```bash
python run_pipeline.py --raw-dir data/raw --processed-dir data/processed
```

4. Para cargar en PostgreSQL:

```bash
set DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/etl_lab
python run_pipeline.py --raw-dir data/raw --processed-dir data/processed --load-db
```

## Nota sobre los datos

El laboratorio tiene inconsistencias reales de calidad: codigos con letras sustituidas por ceros, catalogos mal escritos, fechas con formatos distintos y valores nulos. El pipeline intenta corregirlos de forma determinista y conserva una columna de trazabilidad con el valor original.

## Publicar en GitHub

1. Inicializa un repositorio y sube el proyecto:

```bash
git init
git add .
git commit -m "ETL pipeline lab"
git branch -M main
git remote add origin <url-de-tu-repositorio>
git push -u origin main
```

2. CI: Incluimos un workflow de GitHub Actions en `.github/workflows/ci.yml` que ejecuta `pytest` sobre el repo. Cada push o pull request a `main`/`master` disparará el pipeline de pruebas.

3. Revisa los tests locales antes de pushear:

```bash
python -m pip install -r requirements.txt
pytest -q
```

