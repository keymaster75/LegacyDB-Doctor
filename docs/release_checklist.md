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
- table, column, row, warning, primary key, data-quality, and potential relationship metrics look reasonable

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
Migration Plan
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

Open the generated SQL and confirm:

- file starts with LegacyDB Doctor header comments
- `SET NAMES utf8mb4;` is present
- MySQL-safe names look correct when `--use-recommended-names` is used
- tables without primary keys have warning comments before `CREATE TABLE`

---

## 7. Test report-only mode

```powershell
legacydb-doctor scan "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_report_only" --report-only
```

Expected:

- Excel report is generated
- SQL schema is skipped

---

## 8. Test CSV export

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv" --use-recommended-names
```

Expected:

- one CSV file per exported user table
- `_export_manifest.csv` is created
- CSV files use `utf-8-sig` encoding

---

## 9. Test CSV validation

```powershell
legacydb-doctor validate-csv "C:\Mdb_test\release_csv"
```

Expected:

```text
Errors: 0
```

Warnings should be reviewed if present.

---

## 10. Test limited CSV export

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv_sample" --limit 5 --use-recommended-names
legacydb-doctor validate-csv "C:\Mdb_test\release_csv_sample"
```

Expected:

- export succeeds
- validation succeeds
- manifest contains the export limit

---

## 11. Test manifest-only CSV plan

```powershell
legacydb-doctor export-csv "C:\Mdb_test\Library.mdb" --output-dir "C:\Mdb_test\release_csv_plan" --manifest-only
legacydb-doctor validate-csv "C:\Mdb_test\release_csv_plan"
```

Expected:

- `_export_manifest.csv` is created
- no table CSV files are created
- validation treats `planned` rows as valid

---

## 12. Build the Python package

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

## 13. Check Git safety

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

## 14. Confirm documentation

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
- CHANGELOG has an entry for the release checkpoint

---

## 15. Final clean status

```powershell
git status
```

Expected:

```text
nothing to commit, working tree clean
```

---

## 16. Create release tag

Development checkpoint example:

```powershell
git tag -a v0.1.8-dev -m "Release checklist FK suggestions checkpoint"
git push origin v0.1.8-dev
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
