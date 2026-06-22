# Demo Library Scenario

This folder documents a synthetic demo scenario for LegacyDB Doctor.

The demo is inspired by common legacy school-library databases, but all names, tables, and data are synthetic and written in English for an international audience.

The goal is to provide a safe public demo that can show the main migration-readiness checks without using any private or real-world database.

---

## Planned demo database

Planned database file name:

```text
legacy_library_demo.mdb
```

The database should intentionally contain both clean and problematic legacy structures.

| Table | Purpose | Expected LegacyDB Doctor result |
|---|---|---|
| `Author` | Clean lookup table with a clear key | `Ready` table, clean key signal |
| `Book` | Main book table with a candidate key problem | duplicate key finding on `InventoryNumber` |
| `Member` | Reader/member table without a reliable key | `Blocked` table because rows exist but no key is detected |
| `BookAuthor` | Junction table between books and authors | composite unique key signal; no false duplicate warnings on individual columns |
| `Member_ImportErrors` | Simulated Access import error table | cleanup candidate / likely `Exclude` |
| `Book_OldBackup` | Simulated old backup/copy table | cleanup candidate / likely `Exclude` |

---

## What the demo should demonstrate

The demo scenario is designed to exercise these LegacyDB Doctor features:

- scan summary with metadata
- Migration Readiness Score
- `Readiness Factors` sheet
- `Migration Checklist` sheet
- table convertability statuses: `Ready`, `Blocked`, and `Exclude`
- duplicate candidate/key value detection
- `Duplicate Key Values` sheet
- composite unique index handling for junction tables
- cleanup candidate detection
- data quality checks for empty and low-fill columns
- potential relationship and FK suggestion review
- CSV export and validation
- review-only MySQL import SQL generation
- structured JSON scan output for future GUI, batch, comparison, HTML, and Pro/workflow layers
- simple standalone HTML report rendering from structured JSON output

---

## Create the demo database

The planned demo can be created with the optional helper script:

```powershell
python examples\demo_library\create_demo_access_db.py --overwrite
```

Then scan it:

```powershell
legacydb-doctor scan "examples\demo_library\legacy_library_demo.mdb" --summary-only --readiness-details --duplicate-key-details
```

See [CREATE_DEMO_DATABASE.md](CREATE_DEMO_DATABASE.md) for details and fallback instructions.


## Expected demo workflow

Run a summary-only scan:

```powershell
legacydb-doctor scan "examples\\demo_library\\legacy_library_demo.mdb" --summary-only --readiness-details --duplicate-key-details
```

Generate report and schema:

```powershell
legacydb-doctor scan "examples\\demo_library\\legacy_library_demo.mdb" --output-dir "examples\\demo_library\\out" --use-recommended-names
```

Review the generated Excel sheets:

```text
Summary
Readiness Factors
Migration Checklist
Migration Plan
Duplicate Key Values
Cleanup Candidates
Data Quality
Potential Relationships
FK Suggestions
```

Export CSV files:

```powershell
legacydb-doctor export-csv "examples\\demo_library\\legacy_library_demo.mdb" --output-dir "examples\\demo_library\\csv" --use-recommended-names
```

Validate CSV export:

```powershell
legacydb-doctor validate-csv "examples\\demo_library\\csv"
```

Generate review-only MySQL import SQL:

```powershell
legacydb-doctor generate-import-sql "examples\\demo_library\\csv" --out "examples\\demo_library\\csv\\mysql_import.sql" --use-recommended-names
```

Generate structured JSON output:

```powershell
legacydb-doctor scan "examples\\demo_library\\legacy_library_demo.mdb" --summary-only --json-out "examples\\demo_library\\scan_result.json"
```

Render a simple HTML report from JSON:

```powershell
legacydb-doctor render-html "examples\\demo_library\\scan_result.json" --out "examples\\demo_library\\scan_report.html"
```

---

## Privacy and safety

The demo database must not contain:

- real student/member names
- school production data
- private addresses, emails, or phone numbers
- real legacy application data
- generated reports or SQL files committed by accident

Only synthetic examples should be used.

---

## Demo output examples

The demo scenario should eventually include screenshots or copied terminal output that show what LegacyDB Doctor reports for this intentionally imperfect database.

Until the actual `.mdb` file is created, the examples below describe the expected output shape.

### Expected scan summary highlights

A completed scan should show a mixed result, not a perfect score:

```text
LegacyDB Doctor scanning: examples\demo_library\legacy_library_demo.mdb

Scan summary
- Tables: 6
- Migration readiness level: Low
- Convertability ready: 2
- Convertability exclude: 2
- Convertability blocked: 2
- Duplicate key issues: 1
- Duplicate key affected rows: 2
```

### Expected duplicate key details

The `Book` table should intentionally contain duplicate `InventoryNumber` values:

```text
Duplicate key value details
Table  Column           Key Source  Duplicate Values  Affected Rows  Sample Values
Book   InventoryNumber  candidate_like  1                 2              10012
```

This demonstrates that LegacyDB Doctor can flag a column that looks like a business key but cannot safely become a unique key until duplicate values are reviewed.

### Expected table convertability result

The demo should produce this table-level pattern:

```text
Ready:
- Author
- BookAuthor

Blocked:
- Book
- Member

Exclude:
- Book_OldBackup
- Member_ImportErrors
```

### Expected blocked table details

The `Member` table should contain rows but no reliable key:

```text
Table convertability details
Table   Status   Reason
Member  Blocked  Table has rows but no detected primary key, unique index, or candidate key.
```

This demonstrates why migration-readiness analysis is useful before creating a target MySQL schema.

### Expected cleanup candidate findings

The following tables should be flagged for cleanup review:

```text
Member_ImportErrors
Book_OldBackup
```

These tables are intentionally included to demonstrate how old Access applications often accumulate import-error, copy, backup, or stale tables.

### Expected report screenshots

When the demo database is created, useful screenshots for README/GitHub should include:

- terminal `Scan summary`
- terminal `Duplicate key value details`
- Excel `Migration Checklist`
- Excel `Migration Plan`
- Excel `Duplicate Key Values`
- Excel `Cleanup Candidates`
- Excel `Data Quality`

Generated screenshots should not include private data.



### Expected HTML report sections

The generated HTML report should show:

- database metadata
- migration readiness score and level
- summary metrics
- table convertability status and reason
- duplicate key findings, including the `Book.InventoryNumber` `candidate_like` example
- warnings

The HTML report is generated from `scan_result.json` and should be treated as a local output unless intentionally published as a documentation sample.
