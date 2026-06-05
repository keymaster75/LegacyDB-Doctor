# LegacyDB Doctor

**LegacyDB Doctor** is a practical migration-readiness toolkit for legacy Microsoft Access databases.

It helps developers, IT managers, consultants, and small organizations inspect old `.mdb` / `.accdb` databases before migrating them to **MySQL** or **MariaDB**.

The project focuses on real-world legacy database problems:

- old Microsoft Access databases used by business applications
- Delphi / VB / Access applications with unclear database structure
- missing or unreliable primary key metadata
- Access import error tables and backup/copy tables
- inconsistent table and column names
- MySQL risky/reserved identifiers
- empty or low-fill columns
- Access-to-MySQL type mapping
- migration planning before any destructive change

LegacyDB Doctor does **not** try to blindly convert everything in one click.  
Its first goal is safer and more transparent migration planning.

---

## Current Features

LegacyDB Doctor can currently:

- scan Microsoft Access `.mdb` / `.accdb` databases through ODBC
- list user tables and columns
- count rows per table
- map Access/ODBC column types to suggested MySQL types
- detect suspicious Access table names
- detect import error / copy / backup / temp / test tables
- suggest MySQL-safe table and column names
- warn about MySQL risky/reserved identifiers
- detect primary key status using:
  - formal primary key metadata
  - unique index metadata
  - candidate key heuristics
- generate an Excel migration-readiness report
- generate a MySQL `schema.sql`
- optionally generate schema using normalized MySQL-safe identifiers
- warn about tables without primary key or unique index
- profile column fill rates
- create a migration plan sheet
- create cleanup and data-quality sheets
- skip SQL generation with `--no-schema` / `--report-only`
- run summary-only scans with `--summary-only`
- generate outputs into a selected folder with `--output-dir`
- optionally open the generated Excel report with `--open-report`
- export Access user tables to CSV files with `_export_manifest.csv`
- filter CSV export with `--tables`
- skip empty tables during CSV export with `--skip-empty`
- limit CSV export rows per table with `--limit`

---

## Report Sheets

The generated Excel report currently includes:

| Sheet | Purpose |
|---|---|
| `Summary` | Overall database metrics, warning counts, primary key status counts, and data-quality counts |
| `Migration Plan` | Recommended action per table: migrate, review, or exclude |
| `Tables` | Table list, row counts, column counts, recommended MySQL names, PK status |
| `Primary Keys` | Primary key / unique index / candidate status per table |
| `Cleanup Candidates` | Tables that should be reviewed before migration |
| `Data Quality` | Columns with low fill rate or completely empty values |
| `Columns` | Full column inventory with Access types, MySQL types, fill-rate profiling |
| `Type Mapping` | Access/ODBC type to suggested MySQL type mapping |
| `Warnings` | Detailed warnings and informational notes |

---

## Example Summary

Example terminal output:

```text
Scan summary
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric          ┃ Value ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Tables          │    35 │
│ Columns         │   248 │
│ Rows            │ 23340 │
│ Warnings        │    60 │
│ Info            │   231 │
│ Total notes     │   291 │
│ PK formal       │     0 │
│ PK unique_index │    17 │
│ PK candidate    │     0 │
│ PK none         │    18 │
│ DQ high         │    63 │
│ DQ medium       │    13 │
│ DQ low          │     1 │
└─────────────────┴───────┘
```

---

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/keymaster75/LegacyDB-Doctor.git
cd LegacyDB-Doctor
```

If your project is inside a nested folder after extracting a ZIP, enter the actual project folder that contains:

```text
pyproject.toml
requirements.txt
legacydb_doctor/
tests/
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

---

## Requirements

LegacyDB Doctor currently requires:

- Python 3.10+
- Windows for Access ODBC scanning
- Microsoft Access ODBC driver:
  - `Microsoft Access Driver (*.mdb, *.accdb)`
- Python packages:
  - `pyodbc`
  - `pandas`
  - `openpyxl`
  - `typer`
  - `rich`

To check installed ODBC drivers:

```powershell
python -m legacydb_doctor drivers
```

or, after editable installation:

```powershell
legacydb-doctor drivers
```

You should see something like:

```text
Microsoft Access Driver (*.mdb, *.accdb)
```

---

## Usage

### Basic scan

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --schema-out "C:\Mdb_test\schema.sql"
```

This creates:

```text
legacydb_report.xlsx
schema.sql
```

The SQL schema will use the original Access table and column names.

### Generate schema using recommended MySQL-safe identifiers

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --schema-out "C:\Mdb_test\schema_recommended.sql" --use-recommended-names
```

Example transformation:

```text
Copy Of Naslov      -> copy_of_naslov
Clan$_ImportErrors  -> clan_import_errors
InventarniBroj      -> inventarni_broj
DatumPro            -> datum_pro
```

### Create only the Excel report

Use either `--no-schema` or its alias `--report-only`:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --no-schema
```

or:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --report-only
```

### Summary-only scan

Use this for a quick terminal-only check:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --summary-only
```

This skips Excel report and SQL schema generation.

### Output directory mode

Instead of manually specifying both output files, you can generate default names in a selected folder:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --use-recommended-names
```

This creates:

```text
C:\Mdb_test\out\Library_report.xlsx
C:\Mdb_test\out\Library_schema.sql
```

### Open the generated Excel report

On Windows, the generated report can be opened automatically:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --report-only --open-report
```

### Export Access tables to CSV

Export all user tables to CSV files:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv"
```

Use normalized MySQL-safe file names:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_recommended" --use-recommended-names
```

Export only selected tables:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_selected" --tables Autor,Naslov,Clan --use-recommended-names
```

Skip empty tables during CSV export:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_skip_empty" --skip-empty --use-recommended-names
```

Skipped empty tables are not exported as CSV files, but they are still recorded in `_export_manifest.csv` with status:

```text
skipped_empty
```

Export only a sample of rows from each table:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_sample" --limit 100 --use-recommended-names
```

This exports at most 100 rows per table and is useful for quickly reviewing large databases.

The export creates one CSV file per exported table and a manifest file:

```text
_export_manifest.csv
autor.csv
naslov.csv
clan.csv
```

CSV files are written with `utf-8-sig` encoding so they can be opened more easily in Excel.

---

## Generated SQL

LegacyDB Doctor can generate a starter MySQL schema.

Example with recommended names:

```sql
-- Generated by LegacyDB Doctor
-- Review this schema before running it in production.
-- Identifier mode: recommended MySQL names
SET NAMES utf8mb4;

CREATE TABLE `autor` (
  `sif_a` INT AUTO_INCREMENT NOT NULL,
  `ime` VARCHAR(60) NULL,
  UNIQUE KEY `uk_autor_sif_a` (`sif_a`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

For tables without a primary key or unique index, the generated SQL includes a warning comment before the table:

```sql
-- Warning: no primary key or unique index detected for table `problem`
CREATE TABLE `problem` (
  `sif_problem` INT NULL,
  `opis` TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Generated SQL is a starter schema and should always be reviewed before production use.

---

## Primary Key Detection

Access databases may not always expose formal primary key metadata correctly through ODBC.

LegacyDB Doctor therefore distinguishes between:

| Status | Meaning |
|---|---|
| `formal` | Formal primary key detected through ODBC metadata |
| `unique_index` | Unique index detected; may represent the real primary key |
| `candidate` | Possible key guessed from column names/types |
| `none` | No key or obvious candidate detected |

The tool is intentionally conservative.  
It does not pretend that a unique index is always a formal primary key.

---

## Cleanup Candidate Detection

LegacyDB Doctor flags tables that may need review before migration, such as:

- Access import error tables
- backup/copy tables
- temporary tables
- test tables
- old/stale tables
- empty tables
- tables without primary keys

Cleanup priority levels:

| Priority | Meaning |
|---|---|
| `High` | Likely import/copy/temp/test/backup table |
| `Medium` | Structural concern, such as missing primary key |
| `Low` | Informational concern, such as empty but valid-looking table |

Empty tables are not automatically treated as bad.  
They are marked for review because some valid application/domain tables may simply have no rows yet.

---

## Data Quality Checks

The `Data Quality` sheet highlights columns with low fill rates:

| Severity | Condition |
|---|---|
| `High` | Completely empty column |
| `Medium` | Less than 10% filled |
| `Low` | Less than 50% filled |

This helps identify columns that may be obsolete, rarely used, or require business explanation before migration.

---

## Project Structure

```text
legacydb-doctor/
  README.md
  LICENSE
  CHANGELOG.md
  pyproject.toml
  requirements.txt
  legacydb_doctor/
    __init__.py
    __main__.py
    cli.py
    access_reader.py
    csv_exporter.py
    models.py
    mysql_mapper.py
    report_writer.py
    sql_writer.py
    summary_builder.py
  tests/
  examples/
  docs/
```

---

## Development Workflow

Run all tests:

```powershell
python -m pytest
```

Run tests with concise output:

```powershell
python -m pytest -q
```

Example current result:

```text
tests passed
```

Check editable package installation and CLI entry point:

```powershell
python -m pip install -e .
legacydb-doctor --help
legacydb-doctor drivers
```

Run scan on a test Access database:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --schema-out "C:\Mdb_test\schema.sql"
```

Run scan with normalized MySQL identifiers:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --out "C:\Mdb_test\legacydb_report.xlsx" --schema-out "C:\Mdb_test\schema_recommended.sql" --use-recommended-names
```

Typical commit workflow:

```powershell
git status
git add .
git commit -m "Describe the change"
git push
```

Safety check before making the repository public:

```powershell
git ls-files | findstr /i /r "\.mdb$ \.accdb$ \.xlsx$ \.xls$ \.sql$"
```

The command should not list real local databases, generated Excel reports, or generated SQL output.

---

## Roadmap

Planned or possible future features:

- CSV export improvements and validation
- generate MySQL import scripts
- direct Access-to-MySQL data migration
- duplicate value detection for candidate key columns
- relationship / foreign key discovery
- improved Access index analysis
- HTML report output
- sample demo Access database
- sample screenshots for documentation
- GUI version
- migration checklist documentation
- first public release tag `v0.1.0`

---

## Project Philosophy

LegacyDB Doctor is built around one principle:

> Before migrating a legacy database, first understand what is really inside it.

Old Access databases often contain valuable business data, but also years of accumulated artifacts: copy tables, import errors, empty structures, unclear keys, inconsistent names, and undocumented assumptions.

This tool is meant to support careful, auditable, step-by-step modernization.

---

## License

MIT License.

See the `LICENSE` file for details.

---

## Status

Early development / prototype.

The current version is useful for migration-readiness analysis, but generated SQL should always be reviewed before production use.
