# Start Here – Windows

This guide is the fastest way to try **LegacyDB Doctor** on Windows.

LegacyDB Doctor inspects legacy Microsoft Access databases (`.mdb` / `.accdb`) before migration to MySQL or MariaDB.

It does not modify your Access database.

---

## 1. Requirements

You need:

- Windows
- Python 3.10+
- Microsoft Access ODBC driver
- PowerShell or Windows Terminal

To check whether Python is installed:

```powershell
python --version
```

To check whether the Access ODBC driver is visible to LegacyDB Doctor:

```powershell
python -m legacydb_doctor drivers
```

or, after installation:

```powershell
legacydb-doctor drivers
```

You should see something like:

```text
Microsoft Access Driver (*.mdb, *.accdb)
```

---

## 2. Clone the project

```powershell
git clone https://github.com/keymaster75/LegacyDB-Doctor.git
cd LegacyDB-Doctor
```

If the project is inside a nested folder, enter the folder that contains:

```text
pyproject.toml
README.md
legacydb_doctor/
tests/
```

Example:

```powershell
cd C:\Projects\LegacyDB-Doctor\legacydb-doctor
```

---

## 3. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation with an execution policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Then try again:

```powershell
.\.venv\Scripts\Activate.ps1
```

This changes the execution policy only for the current PowerShell window.

---

## 4. Install LegacyDB Doctor

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

Check the command-line tool:

```powershell
legacydb-doctor --help
```

---

## 5. Run your first scan

Example using an Access database at `C:\Mdb_test\Library.mdb`:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out"
```

This creates:

```text
C:\Mdb_test\out\Library_report.xlsx
C:\Mdb_test\out\Library_schema.sql
```

Use recommended MySQL-safe identifiers:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --use-recommended-names
```

Create only the Excel report:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --report-only
```

Run a quick terminal-only scan:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only
```

---

## 6. Review the Excel report

The report helps you review:

- tables and row counts
- columns and Access/MySQL type mapping
- primary key / unique index status
- cleanup candidates
- data quality issues
- risky MySQL identifiers
- potential relationships between tables
- migration plan notes

Start with these sheets:

```text
Summary
Migration Plan
Cleanup Candidates
Primary Keys
Potential Relationships
Warnings
```

---

## 7. Export Access tables to CSV

Export all user tables:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv"
```

Export with MySQL-safe file names:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv" --use-recommended-names
```

Export only selected tables:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_selected" --tables Autor,Naslov,Clan
```

Export a small sample:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_sample" --limit 100
```

Create a dry-run manifest only:

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv_plan" --manifest-only
```

---

## 8. Validate CSV export

After exporting CSV files, validate the folder:

```powershell
legacydb-doctor validate-csv "C:\Mdb_test\csv"
```

The validator checks:

- whether `_export_manifest.csv` exists
- whether exported CSV files exist
- whether row counts match the manifest
- whether skipped or planned exports are consistent

---

## 9. Run tests before changing code

For developers:

```powershell
python -m pytest -q
```

A clean result means the current development checkpoint is stable.

---

## 10. Before sharing or publishing

Check that real databases and generated reports are not accidentally tracked by Git:

```powershell
git status
git ls-files | findstr /i /r "\.mdb$ \.accdb$ \.xlsx$ \.xls$ \.sql$"
```

The command should not list private Access databases, generated Excel reports, or generated SQL outputs.

---

## Typical first workflow

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
legacydb-doctor drivers
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\out" --use-recommended-names
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\csv" --use-recommended-names
legacydb-doctor validate-csv "C:\Mdb_test\csv"
```

---

## Important note

Always review generated SQL before using it in production.

LegacyDB Doctor is a migration-readiness and validation tool. Its goal is to help you understand the legacy database before migration.
