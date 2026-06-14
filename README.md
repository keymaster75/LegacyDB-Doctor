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

Windows users can start with [START_HERE_WINDOWS.md](START_HERE_WINDOWS.md) for a step-by-step setup and first scan guide.

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
- detect duplicate values in candidate/unique key columns before migration
- print duplicate candidate/key value details in the terminal with `--duplicate-key-details`
- generate an Excel migration-readiness report
- calculate a conservative Migration Readiness Score and readiness level
- explain readiness score factors in the Excel `Readiness Factors` sheet
- create a high-level Excel `Migration Checklist` action plan
- add table-level convertability status and reason to the Excel `Migration Plan` sheet
- print readiness score factor details in the terminal with `--readiness-details`
- include scan metadata in terminal and Excel Summary output: database file, database name, database size, and scan timestamp
- include CSV export readiness guidance in the Excel `Migration Checklist` sheet
- include convertability status counts in the terminal and Excel Summary output
- print table convertability details in the terminal with `--convertability-details`
- limit terminal convertability detail output with `--convertability-details-limit`
- filter terminal convertability details by status with `--convertability-status`
- generate a MySQL `schema.sql`
- optionally export review-only FK suggestions as SQL comments with `--fk-suggestions-out`
- optionally generate schema using normalized MySQL-safe identifiers
- warn about tables without primary key or unique index
- profile column fill rates
- create a migration plan sheet
- create cleanup and data-quality sheets
- create potential relationship and FK suggestion sheets
- skip SQL generation with `--no-schema` / `--report-only`
- run summary-only scans with `--summary-only`
- generate outputs into a selected folder with `--output-dir`
- optionally open the generated Excel report with `--open-report`
- export Access user tables to CSV files with `_export_manifest.csv`
- filter CSV export with `--tables`
- skip empty tables during CSV export with `--skip-empty`
- limit CSV export rows per table with `--limit`
- validate CSV export folders against `_export_manifest.csv` with `validate-csv`
- generate review-only MySQL `LOAD DATA LOCAL INFILE` import scripts from CSV export manifests
- create CSV export dry-run plans with `--manifest-only`
- documented synthetic English demo library scenario for public examples

---

## Report Sheets

The generated Excel report currently includes:

| Sheet | Purpose |
|---|---|
| `Summary` | Scan metadata, overall database metrics, warning counts, migration readiness score, convertability status counts, primary key status counts, and data-quality counts |
| `Readiness Factors` | Explainable readiness score factors with impact, severity, message, and recommendation |
| `Migration Checklist` | High-level action checklist with area, status, finding, recommended action, and related sheet |
| `Migration Plan` | Recommended action per table with convertability status, reason, migration recommendation, and suggested action |
| `Duplicate Key Values` | Duplicate values found in candidate/unique key columns, with affected row counts and sample values |
| `Tables` | Table list, row counts, column counts, recommended MySQL names, PK status |
| `Primary Keys` | Primary key / unique index / candidate status per table |
| `Cleanup Candidates` | Tables that should be reviewed before migration |
| `Data Quality` | Columns with low fill rate or completely empty values |
| `Columns` | Full column inventory with Access types, MySQL types, fill-rate profiling |
| `Type Mapping` | Access/ODBC type to suggested MySQL type mapping |
| `Potential Relationships` | Heuristic relationship suggestions for databases without reliable formal foreign keys |
| `FK Suggestions` | MySQL comment-style foreign key suggestions derived from potential relationships; review-only, no automatic `ALTER TABLE` generation |
| `Warnings` | Detailed warnings and informational notes |

---

## Example Summary

LegacyDB Doctor uses Rich-powered terminal tables for readable scan and validation output:

```text
LegacyDB Doctor scanning: C:\Mdb_test\Library.mdb

           Scan summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric                  ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Database file           │ C:\Mdb_test\Library.mdb │
│ Database name           │ Library.mdb │
│ Database size MB        │ 0.42 │
│ Scan timestamp          │ 2026-06-09T20:15:30 │
│ Tables                  │    35 │
│ Columns                 │   248 │
│ Rows                    │ 23340 │
│ Warnings                │    60 │
│ Info                    │   231 │
│ Total notes             │   291 │
│ Migration readiness score │ 10 / 100 │
│ Migration readiness level │ Low │
│ Convertability ready    │    12 │
│ Convertability review   │     8 │
│ Convertability exclude  │     5 │
│ Convertability blocked  │    10 │
│ Duplicate key issues    │     2 │
│ Duplicate key affected rows │ 12 │
│ PK formal               │     0 │
│ PK unique_index         │    17 │
│ PK candidate            │     0 │
│ PK none                 │    18 │
│ DQ high                 │    63 │
│ DQ medium               │    13 │
│ DQ low                  │     1 │
│ Potential relationships │    10 │
└─────────────────────────┴───────┘
```

### Scan metadata

The terminal summary and Excel `Summary` sheet include basic scan metadata:

| Metric | Meaning |
|---|---|
| `Database file` | Full database path used for the scan |
| `Database name` | Database file name |
| `Database size MB` | Database file size in megabytes |
| `Scan timestamp` | Local timestamp when the scan summary was generated |

This makes generated reports easier to trace, compare, and archive.

CSV validation output is also shown as a compact terminal table:

```text
LegacyDB Doctor validating CSV export: C:\Mdb_test\csv

 CSV validation summary
┏━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric        ┃ Value ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━┩
│ OK            │    35 │
│ Warnings      │     0 │
│ Errors        │     0 │
│ Checked items │    35 │
└───────────────┴───────┘
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

### 3. Install LegacyDB Doctor

For normal use:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

For development and tests:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` is the main source for runtime and development dependencies.

### Windows PowerShell note

If you get an execution policy error when activating the virtual environment, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Then try activating the virtual environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

This changes the execution policy only for the current PowerShell session.

---

## Requirements

LegacyDB Doctor currently requires:

- Python 3.10+
- Windows for Access ODBC scanning
- Microsoft Access ODBC driver:
  - `Microsoft Access Driver (*.mdb, *.accdb)`
- Python runtime packages defined in `pyproject.toml`:
  - `pyodbc`
  - `pandas`
  - `openpyxl`
  - `typer`
  - `rich`
- Development/test dependency available through the `dev` extra:
  - `pytest`

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

### Export review-only FK suggestions

You can export heuristic foreign key suggestions as a separate SQL comment file:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --use-recommended-names --fk-suggestions-out "C:\Mdb_test\out\fk_suggestions.sql"
```

This option can also be used together with `--summary-only` when you want only terminal summary output and a separate FK suggestions comment file:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --fk-suggestions-out "C:\Mdb_test\fk_summary_only.sql"
```

The generated file contains SQL comments only, for example:

```sql
-- Generated by LegacyDB Doctor
-- Review-only FK suggestions. No statements are executed.

-- FK suggestion: `drzi`.`sif_n` may reference `naslov`.`sif_n`
-- Confidence: high
-- Reason: Child column matches a single-column parent key.
```

The generated FK suggestions file does **not** contain executable `ALTER TABLE` statements.

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

To also print the readiness score factors directly in the terminal:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --summary-only --readiness-details
```

This prints the normal scan summary plus a `Migration readiness factors` table with factor, impact, severity, message, and recommendation.

To also print table-level convertability details directly in the terminal:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details
```

This prints the normal scan summary plus a `Table convertability details` table with table name, status, reason, row count, and primary key status.

For large databases, limit the number of terminal convertability rows:

```powershell
python -m legacydb_doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details --convertability-details-limit 20
```

When the output is limited, LegacyDB Doctor shows how many tables are displayed and reminds you to open the Excel `Migration Plan` sheet for full details.


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

### Validate CSV export

Validate an exported CSV folder against `_export_manifest.csv`:

```powershell
legacydb-doctor validate-csv "C:\Mdb_test\csv"
```

The validator checks:

- whether `_export_manifest.csv` exists
- whether exported CSV files listed in the manifest exist
- whether row counts match the manifest
- whether `planned` and `skipped_empty` statuses are consistent with no CSV file
- whether manifest columns required by LegacyDB Doctor are present

For manifest-only export folders, `planned` rows are considered valid when no CSV file is present.

### Generate review-only MySQL import SQL

After exporting and validating CSV files, you can generate a review-only MySQL import script from `_export_manifest.csv`:

```powershell
legacydb-doctor generate-import-sql "C:\Mdb_test\csv" --out "C:\Mdb_test\csv\mysql_import.sql" --use-recommended-names
```

The generated script uses `LOAD DATA LOCAL INFILE` statements, for example:

```sql
-- Generated by LegacyDB Doctor
-- Review this import script before running it in production.
-- Assumes the target MySQL schema already exists.
-- Assumes CSV files were generated by LegacyDB Doctor export-csv.
-- Requires MySQL client/server configuration that allows LOAD DATA LOCAL INFILE.
SET NAMES utf8mb4;

LOAD DATA LOCAL INFILE 'C:/Mdb_test/csv/autor.csv'
INTO TABLE `autor`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;
```

This command does **not** connect to MySQL and does **not** execute the import. It only creates a script for developer review.

Before running the generated script manually, confirm that:

- the target MySQL schema already exists
- CSV export was validated with `validate-csv`
- MySQL client/server configuration allows `LOAD DATA LOCAL INFILE`
- generated CSV paths are valid for the environment where the MySQL client runs
- table order and relationships are reviewed for the target schema

---

### Convertability summary counts

The terminal summary and Excel `Summary` sheet include table-level convertability counts:

| Metric | Meaning |
|---|---|
| `Convertability ready` | Tables that look structurally ready for migration |
| `Convertability review` | Tables that require manual review before migration |
| `Convertability exclude` | Tables that look like copy, backup, temp, test, old, or import-error artifacts |
| `Convertability blocked` | Tables with rows but no detected primary key, unique index, or candidate key |

These counts provide a quick first-page view of how many tables can probably move forward and how many need attention.

## Migration Readiness Score

LegacyDB Doctor calculates a conservative migration-readiness score from 0 to 100.

The score is based on explainable heuristics such as:

- tables without detected primary keys or unique indexes
- possible cleanup/artifact tables
- empty or low-fill columns
- migration warnings
- empty tables
- missing or weak relationship signals

Readiness levels:

| Score | Level |
|---|---|
| 80–100 | High |
| 50–79 | Medium |
| 0–49 | Low |

The score is intentionally conservative. It is not an automatic approval or rejection of a migration. It is meant to highlight how much review work may be needed before migration.

The open-source version provides the basic score, readiness level, and an Excel `Readiness Factors` sheet that explains the main score impacts. The same factor details can also be printed in the terminal with `--readiness-details`, which is useful for quick summary-only checks. More advanced remediation plans, configurable scoring profiles, comparison reports, or exportable branded assessment reports may be added later.

---

## Migration Checklist

The Excel report includes a high-level `Migration Checklist` sheet.

This sheet summarizes the main migration preparation areas into an action-oriented format:

| Column | Meaning |
|---|---|
| `Area` | Migration area being reviewed, such as readiness score, primary keys, data quality, cleanup, relationships, warnings, or schema |
| `Status` | `OK`, `Warning`, `Fail`, or `Info` |
| `Finding` | Short explanation of the detected issue or status |
| `Recommended Action` | Practical next step before migration |
| `Related Sheet` | Detailed sheet or output file where the user can review the underlying evidence |

The checklist is intended as a practical first-page action plan. It does not replace manual review, but it helps users decide where to look first.

It also includes CSV export readiness guidance, pointing users to `export-csv`, `validate-csv`, and `_export_manifest.csv` before data import.

In the open-source version, the checklist is generated as a static Excel sheet. A future advanced/pro workflow may add tracked remediation status, project notes, responsible persons, branded reports, or scan-to-scan progress tracking.

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

## Duplicate Key Value Detection

When LegacyDB Doctor detects a `candidate` key or uses a single-column `unique_index` as a key signal, it also checks whether duplicate values already exist in those key columns.

Composite unique indexes are treated as composite key signals. Their individual columns are not checked as if each column were unique on its own, because junction tables often legitimately repeat values in each individual FK-like column.

This is important because duplicate values can break migration steps such as:

- creating `UNIQUE KEY` constraints in MySQL
- confirming candidate primary keys
- building reliable foreign key relationships
- importing data into a stricter target schema

The Excel report includes a `Duplicate Key Values` sheet with:

| Column | Meaning |
|---|---|
| `Severity` | Issue severity |
| `Table` | Table containing the duplicate values |
| `Column` | Candidate/key column with duplicate values |
| `Key Source` | Whether the key came from `candidate` or `unique_index` detection |
| `Duplicate Values` | Number of distinct duplicate values |
| `Affected Rows` | Total rows involved in duplicate groups |
| `Sample Values` | Example duplicate values for review |
| `Recommendation` | Suggested migration preparation action |

The terminal and Excel `Summary` output also include:

| Metric | Meaning |
|---|---|
| `Duplicate key issues` | Number of candidate/key columns with duplicate values |
| `Duplicate key affected rows` | Total rows affected by duplicate candidate/key values |

The `Migration Checklist` sheet highlights duplicate key values as a migration blocker, because those values should be reviewed or cleaned before creating unique keys or importing into MySQL.

For quick terminal review, the same duplicate key findings can be printed with `--duplicate-key-details` in `--summary-only` mode. This is useful when you want to quickly see the affected table, column, key source, duplicate value count, affected row count, and sample values without opening the Excel report.

This avoids false positives in many-to-many tables such as book-author junction tables, where values like `BookId` and `AuthorId` are expected to repeat individually, while the combination may still be unique.


## Potential Relationships and FK Suggestions

Many legacy Access databases do not expose reliable formal relationship metadata through ODBC.

LegacyDB Doctor therefore includes two review-only report sheets:

| Sheet | Meaning |
|---|---|
| `Potential Relationships` | Detected possible child-to-parent relationships based on matching child columns to single-column parent keys |
| `FK Suggestions` | MySQL comment-style foreign key suggestions derived from potential relationships |

Example FK suggestion:

```sql
-- FK suggestion: `naslov`.`sif_a` may reference `autor`.`sif_a`
```

These suggestions are intentionally **not** generated as automatic `ALTER TABLE` statements.  
They can also be exported to a separate review-only SQL comment file with `--fk-suggestions-out`, including in `--summary-only` mode.  
They should be reviewed by a developer or database owner before any real foreign keys are created.

---

## Table Convertability Status

The `Migration Plan` sheet includes table-level convertability guidance.

Each table receives a conservative status:

| Status | Meaning |
|---|---|
| `Ready` | Table looks structurally ready for migration based on current checks |
| `Review` | Table may be valid, but requires manual review before migration |
| `Exclude` | Table looks like an import-error, copy, backup, temporary, test, or old table |
| `Blocked` | Table has rows but no detected primary key, unique index, or candidate key |

The report also includes a `Convertability Reason` column that explains why the status was assigned.

The same statuses are also summarized as counts in the terminal summary and Excel `Summary` sheet.

For quick terminal review, the same table-level details can be printed with `--convertability-details`.

For large databases, `--convertability-details-limit` can limit the terminal output while preserving risk-based ordering.

Use `--convertability-status` to focus terminal output on only `Ready`, `Review`, `Exclude`, or `Blocked` tables.

This status is intended as migration planning guidance. It should not be treated as an automatic migration decision.

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
  START_HERE_WINDOWS.md
  LICENSE
  CHANGELOG.md
  pyproject.toml
  requirements.txt
  legacydb_doctor/
    __init__.py
    __main__.py
    cli.py
    access_reader.py
    convertability.py
    csv_exporter.py
    csv_validator.py
    duplicate_detector.py
    fk_suggestions_writer.py
    migration_checklist.py
    models.py
    mysql_import_writer.py
    mysql_mapper.py
    report_writer.py
    readiness_score.py
    sql_writer.py
    summary_builder.py
  tests/
  examples/
    demo_library/
      README.md
      demo_data_plan.md
  docs/
    release_checklist.md
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

Check editable development installation and CLI entry point:

```powershell
python -m pip install -e ".[dev]"
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

Run a full scan and review duplicate key value detection:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\duplicate_key_test" --use-recommended-names
```

The `Summary`, `Migration Checklist`, and `Duplicate Key Values` sheets should show duplicate candidate/key findings when duplicate values are detected.

Run a full scan and review the Excel migration checklist:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\migration_checklist_test" --use-recommended-names
```

The `Migration Checklist` sheet should include a `CSV export readiness` row with guidance for `export-csv` and `validate-csv`.

Run a quick scan and review scan metadata:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only
```

The summary should include `Database file`, `Database name`, `Database size MB`, and `Scan timestamp`.

Run a quick scan and review the basic readiness score:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only
```

Run a quick scan with terminal duplicate key details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --duplicate-key-details
```

Run a quick scan with terminal convertability details filtered to blocked tables:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details --convertability-status Blocked
```

Run a quick scan with limited terminal convertability details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details --convertability-details-limit 20
```

Run a quick scan with terminal convertability details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details
```

Run a quick scan with terminal readiness factor details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --readiness-details
```

Generate a review-only MySQL import script from a validated CSV export:

```powershell
legacydb-doctor generate-import-sql "C:\Mdb_test\csv" --out "C:\Mdb_test\csv\mysql_import.sql" --use-recommended-names
```

Review the generated SQL before running it manually in MySQL.

Run scan with review-only FK suggestion comments:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --fk-suggestions-out "C:\Mdb_test\fk_summary_only.sql"
```

Review the planned public demo library scenario:

```powershell
Get-Content .\examples\demo_library\README.md
Get-Content .\examples\demo_library\demo_data_plan.md
```

The demo scenario is synthetic and uses English table and column names for a wider public audience.

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

For a fuller release preparation workflow, see [docs/release_checklist.md](docs/release_checklist.md).

---

## Roadmap

Planned or possible future features:

- configurable scoring profiles
- configurable convertability rules
- scan-to-scan readiness comparison
- exportable readiness assessment reports
- remediation plans based on readiness factors
- tracked remediation workflow based on migration checklist
- direct Access-to-MySQL data migration
- optional reviewed foreign key DDL generation
- improved Access index analysis
- HTML report output
- synthetic English demo Access database based on the documented demo library scenario
- sample screenshots for documentation
- GUI version
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
