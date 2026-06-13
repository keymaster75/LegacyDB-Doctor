# Release Checklist

Use this checklist before creating a public or internal LegacyDB Doctor release tag.

The goal is to confirm that the package, CLI, reports, CSV export, validation, and repository state are stable.

---

## 1. Start from a clean working tree

```powershell
git status
```

Expected result:

```text
nothing to commit, working tree clean
```

---

## 2. Install development dependencies

From the project root folder that contains `pyproject.toml`:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Check the CLI entry point:

```powershell
legacydb-doctor --help
```

---

## 3. Run tests

```powershell
python -m pytest -q
```

Expected result:

```text
tests passed
```

---

## 4. Check Access ODBC driver visibility

```powershell
legacydb-doctor drivers
```

Expected result should include:

```text
Microsoft Access Driver (*.mdb, *.accdb)
```

If the driver is missing, install or repair the Microsoft Access Database Engine / Access ODBC driver before testing real Access databases.

---

## 5. Run scan smoke tests

Use a local test database, for example:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only
```

Expected:

- command completes without exception
- scan summary is shown
- scan summary includes `Database file`, `Database name`, `Database size MB`, and `Scan timestamp`
- table, column, row, warning, migration readiness score, migration readiness level, primary key, data-quality, and potential relationship metrics look reasonable
- scan summary includes convertability counts for `Ready`, `Review`, `Exclude`, and `Blocked` tables

Also test terminal duplicate key details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --duplicate-key-details
```

Expected:

- normal scan summary is shown
- duplicate key details are shown when duplicate candidate/key values are detected
- if no duplicate candidate/key values are detected, a no-issues message is shown

Also test terminal convertability details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details
```

Expected:

- normal scan summary is shown
- `Table convertability details` table is shown
- table name, status, reason, row count, and primary key status are visible

Also test limited terminal convertability details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details --convertability-details-limit 10
```

Expected:

- normal scan summary is shown
- `Table convertability details` table is shown
- output is limited to the requested number of rows
- if more rows exist, a message points to the Excel `Migration Plan` sheet for full details

Also test filtered terminal convertability details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --convertability-details --convertability-status Blocked --convertability-details-limit 10
```

Expected:

- normal scan summary is shown
- `Table convertability details` table is shown
- only `Blocked` rows are shown
- output is limited when more rows exist than the requested limit

Also test terminal readiness factor details:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --readiness-details
```

Expected:

- normal scan summary is shown
- `Migration readiness factors` table is shown
- factor impact, severity, message, and recommendation are visible


---

## 6. Generate Excel report and SQL schema

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_check" --use-recommended-names
```

Expected files:

```text
C:\Mdb_test\release_check\Library_report.xlsx
C:\Mdb_test\release_check\Library_schema.sql
```

Review the Excel report sheets:

```text
Summary
Readiness Factors
Migration Checklist
Migration Plan
Duplicate Key Values
Tables
Primary Keys
Potential Relationships
FK Suggestions
Cleanup Candidates
Data Quality
Columns
Type Mapping
Warnings
```

Confirm that:

- `Potential Relationships` contains heuristic relationship suggestions
- `FK Suggestions` contains review-only MySQL comment-style FK suggestions
- `FK Suggestions` does not generate automatic `ALTER TABLE` statements
- `Summary` includes Migration readiness score and Migration readiness level
- `Summary` includes database file, database name, database size, and scan timestamp
- `Readiness Factors` explains score factors with impact, severity, message, and recommendation
- `Migration Checklist` includes action areas such as Readiness score, Primary keys, Data quality, Cleanup, Relationships, Warnings, and Schema
- `Migration Checklist` includes `CSV export readiness` with `export-csv`, `validate-csv`, and `_export_manifest.csv` guidance
- `Summary` includes convertability counts for `Ready`, `Review`, `Exclude`, and `Blocked` tables
- `Migration Plan` includes `Convertability Status` and `Convertability Reason` columns
- convertability statuses include expected values such as `Ready`, `Review`, `Exclude`, and `Blocked`
- `Migration Checklist` includes duplicate key value guidance
- `Duplicate Key Values` contains duplicate candidate/key findings or a no-issues message
- `Summary` includes duplicate key issue and duplicate key affected row counts

Open the generated SQL and confirm:

- file starts with LegacyDB Doctor header comments
- `SET NAMES utf8mb4;` is present
- MySQL-safe names look correct when `--use-recommended-names` is used
- tables without primary keys have warning comments before `CREATE TABLE`

---

## 7. Test FK suggestions SQL comment export

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_fk_sql" --use-recommended-names --fk-suggestions-out "C:\Mdb_test\release_fk_sql\fk_suggestions.sql"
```

Expected file:

```text
C:\Mdb_test\release_fk_sql\fk_suggestions.sql
```

Confirm that:

- file starts with LegacyDB Doctor header comments
- file contains review-only FK suggestions
- file contains confidence and reason comments
- file does not contain executable `ALTER TABLE` statements

Also test FK suggestions export in summary-only mode:

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --summary-only --fk-suggestions-out "C:\Mdb_test\release_fk_summary_only.sql"
```

Expected file:

```text
C:\Mdb_test\release_fk_summary_only.sql
```

Confirm that:

- summary-only mode skips Excel and schema generation
- FK suggestions comment file is still created when `--fk-suggestions-out` is provided
- generated file does not contain executable `ALTER TABLE` statements

---

## 8. Test report-only mode

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_report_only" --report-only
```

Expected:

- Excel report is generated
- SQL schema is skipped

---

## 9. Test CSV export

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv" --use-recommended-names
```

Expected:

- one CSV file per exported user table
- `_export_manifest.csv` is created
- CSV files use `utf-8-sig` encoding

---

## 10. Test CSV validation

```powershell
legacydb-doctor validate-csv "C:\Mdb_test\release_csv"
```

Expected:

```text
Errors: 0
```

Warnings should be reviewed if present.

---

## 11. Test MySQL import SQL generation

Generate a review-only import script from a validated CSV export folder:

```powershell
legacydb-doctor generate-import-sql "C:\Mdb_test\release_csv" --out "C:\Mdb_test\release_csv\mysql_import.sql" --use-recommended-names
```

Expected file:

```text
C:\Mdb_test\release_csv\mysql_import.sql
```

Confirm that:

- file starts with LegacyDB Doctor header comments
- file contains `LOAD DATA LOCAL INFILE`
- file contains `SET NAMES utf8mb4;`
- table names are quoted with MySQL backticks
- CSV paths use forward slashes
- generated script is review-only and is not executed automatically
- notes mention that target schema must already exist
- notes mention that MySQL must allow `LOAD DATA LOCAL INFILE`


## 12. Test limited CSV export

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv_sample" --limit 5 --use-recommended-names
legacydb-doctor validate-csv "C:\Mdb_test\release_csv_sample"
```

Expected:

- export succeeds
- validation succeeds
- manifest contains the export limit

---

## 13. Test manifest-only CSV plan

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv_plan" --manifest-only
legacydb-doctor validate-csv "C:\Mdb_test\release_csv_plan"
```

Expected:

- `_export_manifest.csv` is created
- no table CSV files are created
- validation treats `planned` rows as valid

---

## 14. Build the Python package

Install build tooling if needed:

```powershell
python -m pip install build
```

Build:

```powershell
python -m build
```

Expected files:

```text
dist\legacydb_doctor-<version>.tar.gz
dist\legacydb_doctor-<version>-py3-none-any.whl
```

---

## 15. Check Git safety

Confirm that private databases or generated outputs are not tracked:

```powershell
git ls-files | findstr /i /r "\.mdb$ \.accdb$ \.xlsx$ \.xls$ \.sql$"
```

Expected:

- no private `.mdb` / `.accdb` files
- no generated Excel reports
- no generated SQL output

Build artifacts should not be tracked:

```powershell
git ls-files | findstr /i /r "^dist/ ^build/ egg-info"
```

Expected:

```text
```

No output.

---

## 16. Confirm documentation

Review:

```text
README.md
START_HERE_WINDOWS.md
CHANGELOG.md
docs/release_checklist.md
```

Check that:

- installation instructions match `pyproject.toml`
- Windows quick start is current
- implemented features are not still listed as future roadmap items
- generated report sheet list matches the current Excel output
- `--fk-suggestions-out` usage is documented and marked as review-only
- `--fk-suggestions-out` summary-only behavior is documented
- Migration Readiness Score is documented as conservative and heuristic
- `--readiness-details` usage is documented
- `--convertability-details` usage is documented
- `--convertability-details-limit` usage is documented
- `--convertability-status` usage is documented
- scan metadata fields are documented
- `Readiness Factors` sheet is documented in the report sheet list
- `Migration Checklist` sheet is documented in the report sheet list
- CSV export readiness guidance is documented
- table convertability statuses are documented
- convertability summary counts are documented
- duplicate key value detection is documented
- `--duplicate-key-details` usage is documented
- review-only MySQL import SQL assumptions and `LOAD DATA LOCAL INFILE` requirements are documented
- `generate-import-sql` usage is documented
- CHANGELOG has an entry for the release checkpoint

---

## 17. Final clean status

```powershell
git status
```

Expected:

```text
nothing to commit, working tree clean
```

---

## 18. Create release tag

Development checkpoint example:

```powershell
git tag -a v0.1.13-dev -m "MySQL import SQL generator checkpoint"
git push origin v0.1.1-dev
```

Public release example:

```powershell
git tag -a v0.1.0 -m "Initial public prototype release"
git push origin v0.1.0
```

---

## Notes

Generated SQL is a starter schema and must be reviewed before production use.

LegacyDB Doctor is designed to support careful migration-readiness analysis, not blind one-click conversion.
