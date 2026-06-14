# Changelog

All notable changes to LegacyDB Doctor will be documented in this file.

## [Unreleased]

### Added
- Microsoft Access `.mdb` / `.accdb` database scanning through ODBC.
- Table and column inventory.
- Row count detection per table.
- Access/ODBC to MySQL type mapping.
- Excel migration-readiness report.
- MySQL `schema.sql` generation.
- Optional normalized MySQL-safe table and column names.
- Suspicious table name detection.
- Cleanup candidates sheet.
- Migration plan sheet.
- Primary key / unique index detection.
- Primary key status summary.
- Data quality sheet for empty and low-fill columns.
- Column fill-rate profiling.
- Warning comments for tables without primary key or unique index.
- CLI options for report-only, summary-only, output directory, and automatic report opening.
- CSV export command for Access user tables.
- CSV export manifest file (`_export_manifest.csv`).
- CSV table filtering with `--tables`.
- Empty-table skipping during CSV export with `--skip-empty`.
- Row-limited CSV export with `--limit`.
- CSV manifest `export_limit` column.
- CSV manifest `planned` status for manifest-only exports.
- CSV export dry-run mode with `--manifest-only`.
- CSV manifest validation for missing files, row-count mismatches, planned exports, skipped empty tables, and required columns.
- CSV export validation command `validate-csv`.
- Unit tests for potential relationship detection.
- Potential relationship count in scan summary.
- `Potential Relationships` Excel report sheet.
- Heuristic potential relationship detection for legacy databases without formal foreign keys.
- Formal Access relationship metadata reader using ODBC and `MSysRelationships` fallback.
- Unit tests for summary building, identifier suggestions, SQL generation, CLI smoke test, CSV manifest writing, table filtering, and CSV export SQL generation.
- Windows quick start guide (`START_HERE_WINDOWS.md`) with setup, first scan, CSV export, and validation workflow.
- README link to the Windows quick start guide.
- `FK Suggestions` Excel report sheet with review-only MySQL comment-style foreign key suggestions.
- Unit tests for FK Suggestions report generation.
- Review-only FK suggestions SQL comment export with `--fk-suggestions-out`.
- Unit tests for FK suggestions SQL comment generation and CLI help option.
- Unit tests for readiness score summary output.
- Conservative Migration Readiness Score and readiness level in scan summary.
- `Readiness Factors` Excel report sheet with score impact, severity, message, and recommendation.
- `Migration Checklist` Excel report sheet with area, status, finding, recommended action, and related sheet.
- Table convertability status and reason in the `Migration Plan` Excel sheet.
- CLI `--readiness-details` option for printing migration readiness factor details in the terminal.
- Scan metadata in terminal and Excel Summary output, including database file, database name, database size, and scan timestamp.
- CSV export readiness action in the `Migration Checklist` Excel sheet.
- Convertability status counts in terminal and Excel Summary output.
- CLI `--convertability-details` option for printing table-level convertability details in the terminal.
- CLI `--convertability-details-limit` option for limiting terminal convertability detail rows.
- CLI `--convertability-status` option for filtering terminal convertability details by `Ready`, `Review`, `Exclude`, or `Blocked`.
- Duplicate key value action row in the Excel `Migration Checklist` sheet.
- Duplicate key issue counts in terminal and Excel Summary output.
- `Duplicate Key Values` Excel report sheet with duplicate value counts, affected rows, sample values, and recommendations.
- Duplicate value detection for candidate and unique-index key columns.
- CLI `--duplicate-key-details` option for printing duplicate candidate/key value findings in the terminal.
- `mysql_import_writer.py` module with manifest-based import SQL generation.
- CLI `generate-import-sql` command for creating `LOAD DATA LOCAL INFILE` scripts.
- Review-only MySQL import SQL generator from CSV export manifests.
- Synthetic English demo library scenario documentation under `examples/demo_library/`.
- Expected demo output examples for the synthetic demo library scenario.
- Duplicate detection for candidate-like business key columns.

### Changed
- Refactored scan summary generation into a shared summary builder.
- Improved generated SQL handling for recommended MySQL-safe identifiers.
- Improved CSV export documentation and test coverage.
- Improved Excel migration-readiness report with potential relationship analysis.
- Extended relationship analysis output with separate review-only FK suggestions.
- Extended scan outputs with optional FK suggestions SQL comment file generation.
- Allowed `--fk-suggestions-out` to work together with `--summary-only`.
- Improved README setup instructions and Rich-style terminal examples.
- Updated README report sheet list and roadmap to reflect implemented CSV validation and potential relationship reporting.
- Documented Windows PowerShell virtual environment activation note.
- Replaced `requirements.txt` dependency duplication with installation guidance.
- Moved dependency management to `pyproject.toml` with a `dev` extra for test dependencies.
- Updated scan summary and Excel Summary sheet to include basic migration readiness indicators.
- Extended Excel report with explainable readiness factor details.
- Extended Excel report with a high-level migration action checklist.
- Extended `Migration Plan` with table-level `Ready`, `Review`, `Exclude`, and `Blocked` convertability statuses.
- Extended scan summary workflow with optional terminal readiness factor details.
- Extended scan summary and Excel Summary sheet with database file metadata for better auditability.
- Extended `Migration Checklist` with CSV export and validation guidance.
- Extended scan summary and Excel Summary sheet with table-level convertability counts.
- Extended scan summary workflow with optional terminal table-level convertability details.
- Improved terminal convertability details output for large databases by allowing row limiting.
- Improved terminal convertability details output by allowing status-focused review.
- Extended migration-readiness reporting with duplicate candidate/key value checks.
- Extended summary-only scan workflow with optional terminal duplicate key details.
- Extended CSV workflow from export and validation to review-only MySQL import script preparation.
- Clarified public demo direction with English table and column names for wider audience.
- Updated duplicate key documentation to explain `candidate_like` findings.

### Fixed
- Handled Access/ODBC metadata decoding errors during column inspection.
- Handled empty CSV table filter results by still creating an export manifest.
- Avoided invalid trailing comma in generated SQL by moving no-primary-key warnings before `CREATE TABLE`.

## [0.1.0] - Planned

Initial public prototype release.
