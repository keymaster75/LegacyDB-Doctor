# LegacyDB Doctor

**Access to MySQL Migration Readiness & Validation Toolkit**

LegacyDB Doctor is a practical Python toolkit for analyzing legacy Microsoft Access databases before migrating them to MySQL or MariaDB.

The first goal is not to blindly migrate everything. The goal is to inspect the database, detect migration risks, generate a clear report, and prepare a safer path toward MySQL/MariaDB.

## What it does in this starter version

The starter version provides a CLI command that can:

- read table names from an Access `.mdb` or `.accdb` database via ODBC,
- inspect columns and Access/ODBC data types,
- count rows per table,
- map common Access/ODBC types to MySQL-friendly types,
- generate an Excel migration-readiness report,
- generate a basic MySQL `schema.sql` file.

## Project status

Early private/starter version.

Planned features:

- primary key detection,
- duplicate detection,
- empty-column detection,
- data-quality profiling,
- direct MySQL import,
- post-migration validation,
- HTML report,
- sample demo Access database.

## Requirements

- Windows is recommended for Access ODBC support.
- Python 3.10+
- Microsoft Access Database Engine / ODBC driver installed.

For `.mdb` / `.accdb` files, the required Windows ODBC driver is usually named something like:

```text
Microsoft Access Driver (*.mdb, *.accdb)
```

## Quick start on Windows

Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run help:

```powershell
python -m legacydb_doctor --help
```

Scan an Access database:

```powershell
python -m legacydb_doctor scan "C:\path\to\database.mdb" --out "report.xlsx" --schema-out "schema.sql"
```

## Example output files

After scanning, the tool can create:

```text
report.xlsx
schema.sql
```

The Excel report contains sheets for:

- Summary
- Tables
- Columns
- Type Mapping
- Warnings

## GitHub setup

If this folder is opened locally and you already created a GitHub repository, connect it like this:

```powershell
git init
git add .
git commit -m "Initial LegacyDB Doctor starter project"
git branch -M main
git remote add origin https://github.com/keymaster75/LegacyDB-Doctor.git
git push -u origin main
```

If the remote repository already contains files, use:

```powershell
git pull origin main --allow-unrelated-histories
```

then resolve any conflicts if Git asks.

## Suggested positioning

LegacyDB Doctor is intended for IT managers, developers, and small organizations maintaining old Access, Delphi, VB, or office-based business applications.

It helps answer a practical question before migration:

> Is this database ready to be migrated safely?

## License

MIT License. See `LICENSE`.
